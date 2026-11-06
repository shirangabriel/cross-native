#!/usr/bin/env python3
"""Install and launch the built app on one explicit iOS simulator, with evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import time


def select_device(data, selected=None):
    devices = [dict(device, runtime=runtime)
               for runtime, group in data.get('devices', {}).items() if '.iOS-' in runtime
               for device in group if device.get('isAvailable')]
    if selected:
        devices = [device for device in devices if selected in (device['udid'], device['name'])]
        if len(devices) != 1:
            raise ValueError('Device must match exactly one available iOS simulator; use its UDID to disambiguate.')
    if not devices:
        raise ValueError('No available iOS simulator. Install an iOS runtime and create a simulator in Xcode.')
    return sorted(devices, key=lambda device: (device['state'] != 'Booted', device['name'], device['runtime'], device['udid']))[0]


def simulator_app(developer):
    developer = Path(developer)
    if developer.suffix == '.app':
        developer = developer / 'Contents/Developer'
    candidates = [developer.parent / 'Applications/DeviceHub.app',
                  developer / 'Applications/Simulator.app',
                  developer.parent / 'Applications/Simulator.app']
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise ValueError(f'No Device Hub or Simulator application found in selected Xcode: {developer}')


def launch(root, selected=None):
    evidence = root / 'build/evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    screenshot = evidence / 'screenshot.png'
    screenshot.unlink(missing_ok=True)
    result = {'status': 'started', 'started_at': datetime.now(timezone.utc).isoformat(),
              'commands': [], 'visual_contract': 'unverified', 'interaction': 'unverified'}
    report = evidence / 'launch.json'

    def save():
        temporary = report.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, indent=2) + '\n')
        temporary.replace(report)

    def run(command, check=True, timeout=30):
        try:
            completed = subprocess.run([str(arg) for arg in command], text=True, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            result['commands'].append({'argv': [str(arg) for arg in command], 'timeout_seconds': timeout,
                                       'stdout': str(exc.stdout or ''), 'stderr': str(exc.stderr or '')})
            raise
        result['commands'].append({'argv': [str(arg) for arg in command], 'returncode': completed.returncode,
                                   'stdout': completed.stdout, 'stderr': completed.stderr})
        if check and completed.returncode:
            raise RuntimeError(f'Command failed ({completed.returncode}): {command}\n{completed.stderr.strip()}')
        return completed

    save()
    try:
        app = root / 'build/Build/Products/Debug-iphonesimulator/CrossNative.app'
        if not (app / 'Info.plist').is_file():
            raise ValueError('Built simulator app missing. Run ./tools/dev build ios first.')
        with (app / 'Info.plist').open('rb') as stream:
            app_info = plistlib.load(stream)
        bundle = app_info['CFBundleIdentifier']
        if not isinstance(bundle, str) or not bundle or '$(' in bundle:
            raise ValueError('Built application has an unresolved bundle identifier.')
        marker = root / '.cross-native-template.json'
        if marker.is_file() and json.loads(marker.read_text())['application_id'] != bundle:
            raise ValueError('Built app identifier differs from generated project identity. Rebuild before launching.')
        result.update(bundle_id=bundle, app_path=str(app.resolve()))
        data = json.loads(run(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']).stdout)
        device = select_device(data, selected or os.environ.get('IOS_DEVICE'))
        result['device'] = device
        udid = device['udid']
        print(f'iOS device: {device["name"]} ({udid})', flush=True)
        if device['state'] != 'Booted':
            run(['xcrun', 'simctl', 'boot', udid])
        run(['xcrun', 'simctl', 'bootstatus', udid, '-b'], timeout=180)
        developer = os.environ.get('DEVELOPER_DIR') or run(['xcode-select', '-p']).stdout.strip()
        gui = simulator_app(developer)
        run(['open', '-a', gui])
        run(['xcrun', 'simctl', 'install', udid, app], timeout=120)
        # Absence of a prior running app is expected on the first launch.
        run(['xcrun', 'simctl', 'terminate', udid, bundle], check=False)
        output = run(['xcrun', 'simctl', 'launch', udid, bundle]).stdout.strip()
        result['launch_output'] = output
        try:
            result['pid'] = int(output.rsplit(':', 1)[1].strip())
        except (ValueError, IndexError):
            raise ValueError(f'Launch returned no process identifier: {output}')
        time.sleep(1)
        run(['xcrun', 'simctl', 'io', udid, 'screenshot', screenshot])
        if not screenshot.is_file() or screenshot.stat().st_size == 0:
            raise ValueError('Simulator screenshot was not created.')
        result.update(status='launched', screenshot=str(screenshot.resolve()),
                      screenshot_captured_at=datetime.now(timezone.utc).isoformat())
        print(f'Launched {bundle}; screenshot captured at {screenshot}', flush=True)
        print('Screenshot capture is not verification of Hello World text or interaction.', flush=True)
        return 0
    except KeyboardInterrupt:
        screenshot.unlink(missing_ok=True)
        result.update(status='interrupted')
        return 130
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        screenshot.unlink(missing_ok=True)
        result.update(status='failed', error=str(exc))
        print(f'iOS launch failed: {exc}', file=sys.stderr)
        return 1
    finally:
        result['finished_at'] = datetime.now(timezone.utc).isoformat()
        save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', help='Simulator UDID or unique name (also IOS_DEVICE)')
    args = parser.parse_args()
    return launch(Path(__file__).resolve().parent, args.device)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
