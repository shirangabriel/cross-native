import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('android_run', Path(__file__).resolve().parents[1] / 'run.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class SelectionTests(unittest.TestCase):
    def runner(self, devices):
        class Fake:
            def devices(self):
                return devices
        return Fake()

    def test_one_running_emulator_selected_without_physical_device(self):
        self.assertEqual(run.select_device(self.runner({'phone': 'device', 'emulator-5554': 'device'}), None, None, 1), 'emulator-5554')

    def test_multiple_running_emulators_require_explicit_choice(self):
        with self.assertRaisesRegex(RuntimeError, 'Multiple running'):
            run.select_device(self.runner({'emulator-5554': 'device', 'emulator-5556': 'device'}), None, None, 1)

    def test_physical_device_requires_explicit_serial(self):
        self.assertEqual(run.select_device(self.runner({'phone': 'device'}), 'phone', None, 1), 'phone')
        with self.assertRaisesRegex(RuntimeError, 'authorize'):
            run.select_device(self.runner({'phone': 'unauthorized'}), 'phone', None, 1)

    def test_multiple_avds_report_choices(self):
        class Fake:
            def devices(self):
                return {}
            def command(self, args):
                return 'Pixel_1\nPixel_2\n'
        with patch.object(run, 'sdk_tool', return_value='emulator'):
            with self.assertRaisesRegex(RuntimeError, 'Pixel_1, Pixel_2'):
                run.select_device(Fake(), None, None, 1)

    def test_ui_text_must_belong_to_target_package(self):
        self.assertTrue(run.hello_world_verified('<hierarchy><node text="Hello World" package="com.example.app"/></hierarchy>', 'com.example.app'))
        self.assertFalse(run.hello_world_verified('<hierarchy><node text="Hello World" package="other.app"/></hierarchy>', 'com.example.app'))

    def test_failed_launch_replaces_old_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / 'build/evidence'
            evidence.mkdir(parents=True)
            (evidence / 'launch.json').write_text('{"status":"launched"}')
            (evidence / 'screenshot.png').write_bytes(b'old')
            with patch.object(run, 'APP_ID', 'com.example.app'):
                self.assertEqual(run.launch(root), 1)
            self.assertFalse((evidence / 'screenshot.png').exists())
            report = json.loads((evidence / 'launch.json').read_text())
            self.assertEqual(report['status'], 'failed')
            self.assertIn('APK missing', report['error'])

    def test_success_keeps_every_device_command_pinned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / 'app/build/outputs/apk/debug/app-debug.apk'
            apk.parent.mkdir(parents=True)
            apk.touch()
            calls = []
            class FakeRunner:
                def __init__(self, adb, evidence):
                    pass
                def devices(self):
                    return {'emulator-5554': 'device'}
                def device(self, serial, *args, **kwargs):
                    calls.append((serial, args))
                    if args == ('shell', 'getprop', 'sys.boot_completed'):
                        return '1'
                    if args[0] == 'install':
                        return 'Success'
                    if 'start' in args:
                        return 'Status: ok'
                    if 'dumpsys' in args:
                        return 'mCurrentFocus=Window com.example.app/dev.crossnative.app.MainActivity'
                    if args[0] == 'exec-out':
                        return b'\x89PNG\r\n\x1a\nimage'
                    if 'cat' in args:
                        return '<hierarchy><node text="Hello World" package="com.example.app"/></hierarchy>'
                    return ''
            with patch.object(run, 'APP_ID', 'com.example.app'), patch.object(run, 'sdk_tool', return_value='adb'), patch.object(run, 'Runner', FakeRunner):
                self.assertEqual(run.launch(root), 0)
            self.assertTrue(all(serial == 'emulator-5554' for serial, _ in calls))
            report = json.loads((root / 'build/evidence/launch.json').read_text())
            self.assertEqual(report['device_id'], 'emulator-5554')
            self.assertTrue(report['ui_verified'])


if __name__ == '__main__':
    unittest.main()
