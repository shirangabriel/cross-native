#!/usr/bin/env python3
"""Build the generated Android starter without changing system configuration."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
env = os.environ.copy()
if not env.get('JAVA_HOME'):
    studio_jdk = Path('/Applications/Android Studio.app/Contents/jbr/Contents/Home')
    if studio_jdk.is_dir():
        env['JAVA_HOME'] = str(studio_jdk)
if not env.get('ANDROID_HOME') and not env.get('ANDROID_SDK_ROOT'):
    for candidate in (Path.home() / 'Library/Android/sdk', Path.home() / 'Android/Sdk'):
        if candidate.is_dir():
            env['ANDROID_HOME'] = str(candidate)
            break
env.setdefault('GRADLE_USER_HOME', str(root.parent / '.build/gradle'))
try:
    result = subprocess.run([str(root / 'gradlew'), '--no-daemon', '--console=plain', ':app:assembleDebug', *sys.argv[1:]], cwd=root, env=env)
    if result.returncode == 0:
        print(f'APK: {root / "app/build/outputs/apk/debug/app-debug.apk"}')
    sys.exit(result.returncode)
except OSError as exc:
    print(f'Android build failed: {exc}', file=sys.stderr)
    sys.exit(1)
