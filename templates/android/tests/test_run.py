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

    def test_modern_window_subdump_has_no_foreground_fields(self):
        # Reduced from the user's captured Android window-windows output.
        captured = """WINDOW MANAGER WINDOWS (dumpsys window windows)
  Window #8 Window{a355b99 u0 com.widgetcorps.com/dev.crossnative.app.MainActivity}:
    mActivityRecord=ActivityRecord{135332325 u0 com.widgetcorps.com/dev.crossnative.app.MainActivity t342}
    isOnScreen=true
  mTopFocusedDisplayId=0
  imeInputTarget in display# 0 Window{a355b99 u0 com.widgetcorps.com/dev.crossnative.app.MainActivity}
"""
        self.assertIsNone(run.foreground_matches(captured, 'com.widgetcorps.com', run.ACTIVITY,
                                                 ('mCurrentFocus', 'mFocusedApp')))

    def test_full_window_dump_matches_exact_component(self):
        text = '  mCurrentFocus=Window{a355b99 u0 com.widgetcorps.com/dev.crossnative.app.MainActivity}'
        fields = ('mCurrentFocus', 'mFocusedApp')
        self.assertTrue(run.foreground_matches(text, 'com.widgetcorps.com', run.ACTIVITY, fields))
        self.assertFalse(run.foreground_matches(text, 'widgetcorps.com', run.ACTIVITY, fields))
        self.assertFalse(run.foreground_matches(text, 'com.widgetcorps.com', 'other.Activity', fields))
        short = 'mCurrentFocus=Window{a u0 dev.crossnative.app/.MainActivity}'
        self.assertTrue(run.foreground_matches(short, 'dev.crossnative.app', run.ACTIVITY, fields))

    def test_system_focus_cannot_be_overruled_by_resumed_target(self):
        window = ('mCurrentFocus=Window{a u0 com.android.permissioncontroller/.GrantPermissionsActivity}\n'
                  'mFocusedApp=ActivityRecord{b u0 com.example.app/dev.crossnative.app.MainActivity}')
        self.assertFalse(run.foreground_matches(window, 'com.example.app', run.ACTIVITY,
                                               ('mCurrentFocus', 'mFocusedApp')))
        self.assertFalse(run.foreground_matches('mCurrentFocus=null', 'com.example.app', run.ACTIVITY,
                                               ('mCurrentFocus', 'mFocusedApp')))

    def test_activity_fallback_uses_resumed_record_not_history(self):
        calls = []
        class Fake:
            def device(self, serial, *args):
                calls.append((serial, args))
                if args == ('shell', 'dumpsys', 'window'):
                    return 'mTopFocusedDisplayId=0'
                return ('topResumedActivity=ActivityRecord{a u0 com.example.app/dev.crossnative.app.MainActivity t1}\n'
                        'mResumedActivity=ActivityRecord{b u0 other.app/.MainActivity t0}')
        self.assertEqual(run.foreground_app(Fake(), 'emulator-5554', 'com.example.app', run.ACTIVITY),
                         (True, 'activity'))
        self.assertEqual(calls[0][1], ('shell', 'dumpsys', 'window'))
        historical = 'Hist #0: ActivityRecord{a u0 com.example.app/dev.crossnative.app.MainActivity t1}'
        self.assertIsNone(run.foreground_matches(historical, 'com.example.app', run.ACTIVITY,
                                                 ('topResumedActivity', 'mResumedActivity')))

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
