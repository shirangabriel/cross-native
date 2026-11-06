#!/usr/bin/env python3
"""Install and launch the built Android app on one explicitly resolved device."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

APP_ID = '__APP_ID__'
ACTIVITY = 'dev.crossnative.app.MainActivity'


def sdk_tool(name):
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    roots = [Path(sdk)] if sdk else [Path.home() / 'Library/Android/sdk', Path.home() / 'Android/Sdk']
    relative = 'platform-tools/adb' if name == 'adb' else 'emulator/emulator'
    for root in roots:
        candidate = root / relative
        if candidate.is_file():
            return str(candidate)
    fallback = shutil.which(name)
    if fallback:
        return fallback
    raise RuntimeError(f'{name} not found. Set ANDROID_HOME to your installed Android SDK.')


class Runner:
    def __init__(self, adb, evidence):
        self.adb = adb
        self.evidence = evidence

    def command(self, args, timeout=30, binary=False):
        result = subprocess.run(args, capture_output=True, timeout=timeout)
        output = result.stdout if binary else result.stdout.decode(errors='replace')
        stderr = result.stderr.decode(errors='replace')
        self.evidence['commands'].append({'argv': args, 'exit_code': result.returncode,
                                         'stdout': '<binary>' if binary else output, 'stderr': stderr})
        if result.returncode:
            raise RuntimeError(f'Command failed ({result.returncode}): {args}\n{stderr}')
        return output

    def device(self, serial, *args, **kwargs):
        return self.command([self.adb, '-s', serial, *args], **kwargs)

    def devices(self):
        text = self.command([self.adb, 'devices'])
        return {parts[0]: parts[1] for line in text.splitlines()[1:]
                if len(parts := line.split()) >= 2}


def select_device(runner, requested, root, timeout):
    devices = runner.devices()
    if requested in devices:
        if devices[requested] != 'device':
            raise RuntimeError(f'{requested} is {devices[requested]}; authorize/unlock it before retrying.')
        return requested
    if not requested:
        emulators = [serial for serial, state in devices.items()
                     if serial.startswith('emulator-') and state == 'device']
        if len(emulators) == 1:
            return emulators[0]
        if len(emulators) > 1:
            raise RuntimeError('Multiple running emulators; use --device SERIAL: ' + ', '.join(emulators))
    emulator = sdk_tool('emulator')
    avds = runner.command([emulator, '-list-avds']).splitlines()
    avds = [name.strip() for name in avds if name.strip()]
    if requested:
        if requested not in avds:
            raise RuntimeError(f'Unknown device/AVD {requested}. Connected: {list(devices)}; AVDs: {avds}')
        avd = requested
        for serial, state in devices.items():
            if serial.startswith('emulator-') and state == 'device':
                name = runner.device(serial, 'emu', 'avd', 'name').splitlines()[0].strip()
                if name == avd:
                    return serial
    elif len(avds) == 1:
        avd = avds[0]
    else:
        raise RuntimeError('Start an emulator or select an AVD with --device NAME. Available AVDs: ' + ', '.join(avds))
    # Pin a free emulator console port so another concurrently booted device cannot be selected.
    import socket
    port = None
    for candidate in range(5554, 5682, 2):
        if f'emulator-{candidate}' in devices:
            continue
        try:
            with socket.socket() as first, socket.socket() as second:
                first.bind(('127.0.0.1', candidate))
                second.bind(('127.0.0.1', candidate + 1))
            port = candidate
            break
        except OSError:
            continue
    if port is None:
        raise RuntimeError('No free emulator port available.')
    log = root / 'build/evidence/emulator.log'
    with log.open('ab') as stream:
        subprocess.Popen([emulator, '-avd', avd, '-port', str(port)], stdout=stream, stderr=subprocess.STDOUT,
                         start_new_session=True)
    serial = f'emulator-{port}'
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if runner.devices().get(serial) == 'device':
            return serial
        time.sleep(1)
    raise RuntimeError(f'Timed out starting {avd} as {serial}. See {log}')


def wait_boot(runner, serial, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if runner.device(serial, 'shell', 'getprop', 'sys.boot_completed', timeout=10).strip() == '1':
            return
        time.sleep(1)
    raise RuntimeError(f'Timed out waiting for Android boot on {serial}.')


def foreground_matches(text, package, activity, fields):
    """True/False for an authoritative foreground field; None if unavailable.

    Do not accept a component merely because it occurs in a historical task or
    visible-window listing. Package and normalized activity must both match.
    Field order gives current window focus priority over focused/resumed apps.
    """
    for field in fields:
        lines = re.findall(r'^\s*' + re.escape(field) + r'\s*[:=]\s*(.*)$', text, re.MULTILINE)
        if not lines:
            continue
        for line in lines:
            for found_package, found_activity in re.findall(
                    r'(?<![A-Za-z0-9_.])([A-Za-z][A-Za-z0-9_.]*)/([A-Za-z0-9_.$]+)', line):
                if found_activity.startswith('.'):
                    found_activity = found_package + found_activity
                if found_package == package and found_activity == activity:
                    return True
        return False
    return None


def foreground_app(runner, serial, package, activity):
    # `window windows` omits display focus on recent Android releases. The full
    # dump includes mCurrentFocus/mFocusedApp; activity state is a fallback only
    # when those fields are unavailable, never when another window has focus.
    window = runner.device(serial, 'shell', 'dumpsys', 'window')
    match = foreground_matches(window, package, activity, ('mCurrentFocus', 'mFocusedApp'))
    if match is not None:
        return match, 'window'
    activities = runner.device(serial, 'shell', 'dumpsys', 'activity', 'activities')
    return (foreground_matches(activities, package, activity,
                               ('topResumedActivity', 'mResumedActivity')) is True, 'activity')


def hello_world_verified(xml, package):
    tree = ET.fromstring(xml)
    return any(node.get('package') == package and node.get('text') == 'Hello World'
               for node in tree.iter('node'))


def launch(root, requested=None, timeout=180):
    directory = root / 'build/evidence'
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('launch.json', 'screenshot.png', 'ui.xml'):
        (directory / name).unlink(missing_ok=True)
    evidence = {'platform': 'android', 'application_id': APP_ID,
                'timestamp': datetime.now(timezone.utc).isoformat(), 'status': 'failed',
                'commands': [], 'ui_verified': False}
    try:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)+', APP_ID):
            raise RuntimeError('Generate the Android template before running it.')
        apk = root / 'app/build/outputs/apk/debug/app-debug.apk'
        if not apk.is_file():
            raise RuntimeError('APK missing. Run ./tools/dev build android first.')
        runner = Runner(sdk_tool('adb'), evidence)
        serial = select_device(runner, requested or os.environ.get('ANDROID_SERIAL'), root, timeout)
        evidence['device_id'] = serial
        print(f'Android target: {serial}', flush=True)
        wait_boot(runner, serial, timeout)
        result = runner.device(serial, 'install', '-r', str(apk), timeout=120)
        if 'Success' not in result:
            raise RuntimeError('APK installation did not report Success: ' + result)
        runner.device(serial, 'shell', 'am', 'force-stop', APP_ID)
        result = runner.device(serial, 'shell', 'am', 'start', '-W', '-n', f'{APP_ID}/{ACTIVITY}')
        if re.search(r'(^|\n)\s*(Error|Exception)', result) or 'Status: ok' not in result:
            raise RuntimeError('Activity launch failed: ' + result)
        # Wait for a rendered foreground activity, then capture evidence from that same serial.
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            focused, source = foreground_app(runner, serial, APP_ID, ACTIVITY)
            if focused:
                evidence['foreground_verification_source'] = source
                break
            time.sleep(0.5)
        else:
            raise RuntimeError('Launched activity did not become foreground. Check the emulator for a lock screen or system dialog; foreground dumps are in launch.json.')
        evidence['launch_verified'] = True
        remote = '/sdcard/cross-native-ui.xml'
        runner.device(serial, 'shell', 'rm', '-f', remote)
        runner.device(serial, 'shell', 'uiautomator', 'dump', remote, timeout=30)
        xml = runner.device(serial, 'shell', 'cat', remote)
        (directory / 'ui.xml').write_text(xml)
        runner.device(serial, 'shell', 'rm', '-f', remote)
        png = runner.device(serial, 'exec-out', 'screencap', '-p', binary=True)
        if not png.startswith(b'\x89PNG\r\n\x1a\n'):
            raise RuntimeError('Screenshot did not contain PNG data.')
        (directory / 'screenshot.png').write_bytes(png)
        evidence['ui_verified'] = hello_world_verified(xml, APP_ID)
        evidence['screenshot'] = str(directory / 'screenshot.png')
        evidence['ui_hierarchy'] = str(directory / 'ui.xml')
        evidence['status'] = 'launched'
        print(f'Launched {APP_ID} on {serial}. Evidence: {directory}', flush=True)
        print('Hello World text: ' + ('verified in app UI hierarchy' if evidence['ui_verified'] else 'not found; screen content remains unverified'), flush=True)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError, ET.ParseError) as exc:
        evidence['error'] = str(exc)
        print(f'Android launch failed: {exc}', file=sys.stderr)
        return 1
    finally:
        (directory / 'launch.json').write_text(json.dumps(evidence, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', help='Connected serial or installed AVD name; ANDROID_SERIAL is also honored')
    parser.add_argument('--timeout', type=int, default=180, help='Boot timeout in seconds (default: 180)')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    return launch(Path(__file__).resolve().parent, args.device, args.timeout)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
