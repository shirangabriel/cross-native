"""Deterministic generation and native build operations; no model calls."""
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
from xml.sax.saxutils import escape


def generate(root, config):
    android_name = config['name'].replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    replacements = {'__APP_NAME_ANDROID_XML__': escape(android_name),
                    '__APP_ID__': config['application_id'],
                    '__APP_NAME_XML__': escape(config['name'], {'"': '&quot;', "'": '&apos;'}),
                    '__APP_NAME_JSON__': json.dumps(config['name'], ensure_ascii=True)}
    pattern = b'|'.join(re.escape(token.encode()) for token in replacements)
    identity = {'template_version': 1, 'name': config['name'], 'application_id': config['application_id']}
    for platform in config['platforms']:
        destination = root / platform
        marker = destination / '.cross-native-template.json'
        if destination.exists():
            if not marker.is_file():
                raise ValueError(f'{platform}/ already exists without a template marker; refusing to overwrite it.')
            if json.loads(marker.read_text()) != identity:
                raise ValueError(f'{platform}/ identity differs from saved configuration; reconcile it before continuing.')
            print(f'  Preserved {platform}/ (already generated)', flush=True)
            continue
        template = root / 'templates' / platform
        if not template.is_dir():
            raise ValueError(f'Missing template: {template}')
        # Prepare a complete directory before making it visible. Never merge into an app.
        with tempfile.TemporaryDirectory(prefix='.cross-native-generate-', dir=root) as temporary:
            stage = Path(temporary) / platform
            shutil.copytree(template, stage, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
            for path in stage.rglob('*'):
                if not path.is_file():
                    continue
                data = path.read_bytes()
                data = re.sub(pattern, lambda match: replacements[match.group().decode()].encode(), data)
                path.write_bytes(data)
            (stage / '.cross-native-template.json').write_text(json.dumps(identity, indent=2) + '\n')
            stage.rename(destination)
        print(f'  Created {platform}/', flush=True)


def build(root, platforms):
    failures = []
    logs = root / '.build/logs'
    logs.mkdir(parents=True, exist_ok=True)
    for platform in platforms:
        script = root / platform / 'build.sh'
        log = logs / f'{platform}-build.log'
        if not script.is_file():
            print(f'FAIL {platform}: project build script missing. Run ./tools/init first.', flush=True)
            failures.append(platform)
            continue
        print(f'Building {platform}… Log: {log}', flush=True)
        with log.open('w') as output:
            try:
                result = subprocess.run([str(script)], cwd=script.parent, stdout=output, stderr=subprocess.STDOUT)
                code = result.returncode
            except OSError as exc:
                output.write(str(exc) + '\n')
                code = 1
        if code:
            failures.append(platform)
            print(f'FAIL {platform} build (exit {code}). Last log lines:', flush=True)
            print('\n'.join(log.read_text(errors='replace').splitlines()[-12:]), flush=True)
        else:
            print(f'OK {platform} build', flush=True)
    return not failures


def doctor(root, platforms):
    checks = [('Python', True, 'available')]
    if 'ios' in platforms:
        tool = shutil.which('xcodebuild')
        checks.append(('Xcode tools', bool(tool), tool or 'install/select Xcode on macOS'))
    if 'android' in platforms:
        sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        candidates = [Path(sdk)] if sdk else [Path.home() / 'Library/Android/sdk', Path.home() / 'Android/Sdk']
        found = next((p for p in candidates if (p / 'platforms').is_dir()), None)
        checks.append(('Android SDK', bool(found), str(found) if found else 'set ANDROID_HOME to an installed SDK'))
        java = os.environ.get('JAVA_HOME')
        found_java = (Path(java) / 'bin/java').is_file() if java else bool(shutil.which('java'))
        checks.append(('Java', found_java, java or shutil.which('java') or 'install Java or configure JAVA_HOME'))
    for label, ok, detail in checks:
        print(f'{"OK" if ok else "MISSING"} {label}: {detail}')
    print('Presence checks only; builds check toolchain compatibility. Device launch is not checked.')
    return all(ok for _, ok, _ in checks)


def run_projects(root, platforms, devices=None, build_first=True):
    """Build and launch each platform independently; retain diagnostic logs."""
    import sys
    devices = devices or {}
    failures = []
    logs = root / '.build/logs'
    logs.mkdir(parents=True, exist_ok=True)
    for platform in platforms:
        if build_first and not build(root, [platform]):
            failures.append(platform)
            continue
        script = root / platform / 'run.py'
        if not script.is_file():
            print(f'FAIL {platform}: run.py missing. Existing projects are not overwritten; '
                  'ask the platform agent to adopt the current runner.', flush=True)
            failures.append(platform)
            continue
        log = logs / f'{platform}-run.log'
        command = [sys.executable, str(script)]
        if devices.get(platform):
            command.extend(['--device', devices[platform]])
        print(f'Launching {platform}… Log: {log}', flush=True)
        with log.open('w') as output:
            try:
                result = subprocess.run(command, cwd=script.parent, stdout=output, stderr=subprocess.STDOUT)
                code = result.returncode
            except OSError as exc:
                output.write(str(exc) + '\n')
                code = 1
        if code:
            failures.append(platform)
            print(f'FAIL {platform} launch (exit {code}). Last log lines:', flush=True)
            print('\n'.join(log.read_text(errors='replace').splitlines()[-12:]), flush=True)
        else:
            print(f'OK {platform} launch. Evidence: {root / platform / "build/evidence"}', flush=True)
            print('\n'.join(log.read_text(errors='replace').splitlines()[-4:]), flush=True)
    return not failures
