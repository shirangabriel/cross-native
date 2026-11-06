import importlib.util
import json
import subprocess
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

    def test_boot_query_timeout_retries_same_serial_until_ready(self):
        calls = []
        clock = [0.0]
        class Fake:
            def device(self, serial, *args, timeout):
                calls.append((serial, args, timeout))
                if len(calls) == 1:
                    clock[0] += timeout
                    raise subprocess.TimeoutExpired('adb', timeout)
                return '1\n'
        with patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(run.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            run.wait_boot(Fake(), 'emulator-5554', 30)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[0] == 'emulator-5554' for call in calls))

    def test_boot_deadline_caps_queries_and_fails(self):
        timeouts = []
        clock = [0.0]
        class Fake:
            def device(self, serial, *args, timeout):
                timeouts.append(timeout)
                clock[0] += timeout
                raise subprocess.TimeoutExpired('adb', timeout)
        with patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(run.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            with self.assertRaisesRegex(RuntimeError, 'Timed out after 15s.*emulator-5554.*cold boot'):
                run.wait_boot(Fake(), 'emulator-5554', 15)
        self.assertEqual(timeouts, [10, 4])
        self.assertEqual(clock[0], 15)

    def test_boot_temporarily_offline_then_not_booted_then_ready(self):
        answers = iter([RuntimeError('device offline'), '', '1'])
        clock = [0.0]
        class Fake:
            def device(self, serial, *args, timeout):
                answer = next(answers)
                if isinstance(answer, Exception):
                    raise answer
                return answer
        with patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(run.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            run.wait_boot(Fake(), 'emulator-5554', 5)
        self.assertEqual(clock[0], 2)

    def test_boot_deadline_returns_failed_launch_without_install(self):
        clock = [0.0]
        calls = []
        class FakeRunner:
            def __init__(self, adb, evidence):
                pass
            def device(self, serial, *args, timeout):
                calls.append(args)
                clock[0] += timeout
                raise subprocess.TimeoutExpired('adb', timeout)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / 'app/build/outputs/apk/debug/app-debug.apk'
            apk.parent.mkdir(parents=True)
            apk.touch()
            with patch.object(run, 'APP_ID', 'com.example.app'), \
                    patch.object(run, 'sdk_tool', return_value='adb'), \
                    patch.object(run, 'Runner', FakeRunner), \
                    patch.object(run, 'select_device', return_value='emulator-5554'), \
                    patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                    patch.object(run.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
                self.assertEqual(run.launch(root, timeout=15), 1)
            report = json.loads((root / 'build/evidence/launch.json').read_text())
            self.assertEqual(report['status'], 'failed')
            self.assertIn('Timed out after 15s', report['error'])
            self.assertTrue(all(args == ('shell', 'getprop', 'sys.boot_completed') for args in calls))
            self.assertFalse((root / 'build/evidence/screenshot.png').exists())

    def test_timed_out_command_is_recorded_in_evidence(self):
        evidence = {'commands': []}
        runner = run.Runner('adb', evidence)
        error = subprocess.TimeoutExpired(['adb'], 3, output=b'partial', stderr=b'busy')
        with patch.object(run.subprocess, 'run', side_effect=error):
            with self.assertRaises(subprocess.TimeoutExpired):
                runner.device('emulator-5554', 'shell', 'getprop', timeout=3)
        self.assertEqual(evidence['commands'][0]['timeout_seconds'], 3)
        self.assertEqual(evidence['commands'][0]['stdout'], 'partial')
        self.assertEqual(evidence['commands'][0]['argv'][:3], ['adb', '-s', 'emulator-5554'])

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

    def start_runner(self, clock, window_results, start_result=None):
        calls = []
        results = iter(window_results)
        class Fake:
            def device(self, serial, *args, timeout):
                calls.append((serial, args, timeout))
                if 'start' in args:
                    if start_result is not None:
                        return start_result
                    clock[0] += timeout
                    raise subprocess.TimeoutExpired('adb am start', timeout, output=b'Starting: Intent')
                result = next(results)
                if isinstance(result, Exception):
                    clock[0] += timeout
                    raise result
                return result
        return Fake(), calls

    def test_start_timeout_accepts_only_verified_foreground(self):
        clock = [0.0]
        runner, calls = self.start_runner(clock, ['mCurrentFocus=Window{a u0 com.example.app/dev.crossnative.app.MainActivity}'])
        evidence = {}
        with patch.object(run, 'APP_ID', 'com.example.app'), \
                patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]):
            run.start_activity(runner, 'emulator-5554', evidence)
        self.assertEqual(evidence['start_command_status'], 'timed_out')
        self.assertEqual(evidence['foreground_verification_source'], 'window')
        self.assertTrue(all(call[0] == 'emulator-5554' for call in calls))
        self.assertEqual(sum('start' in call[1] for call in calls), 1)

    def test_start_timeout_unrelated_foreground_still_fails(self):
        clock = [0.0]
        runner, calls = self.start_runner(clock, ['mCurrentFocus=Window{a u0 other.app/.MainActivity}'] * 10)
        with patch.object(run, 'APP_ID', 'com.example.app'), \
                patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(run.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            with self.assertRaisesRegex(RuntimeError, 'could not be verified within 32s'):
                run.start_activity(runner, 'emulator-5554', {}, timeout=32)
        self.assertEqual(clock[0], 32)
        self.assertEqual(sum('start' in call[1] for call in calls), 1)

    def test_foreground_queries_retry_timeouts_with_remaining_budget(self):
        clock = [0.0]
        runner, calls = self.start_runner(clock, [subprocess.TimeoutExpired('adb', 5),
                                                'mCurrentFocus=Window{a u0 com.example.app/dev.crossnative.app.MainActivity}'])
        with patch.object(run, 'APP_ID', 'com.example.app'), \
                patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(run.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            run.start_activity(runner, 'emulator-5554', {}, timeout=38)
        self.assertEqual([call[2] for call in calls], [30, 5, 2.5])

    def test_explicit_activity_start_error_is_not_overridden(self):
        clock = [0.0]
        runner, calls = self.start_runner(clock, [], start_result='Error type 3\nError: Activity class does not exist')
        with patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]):
            with self.assertRaisesRegex(RuntimeError, 'Activity launch failed'):
                run.start_activity(runner, 'emulator-5554', {})
        self.assertEqual(len(calls), 1)

    def test_unresponsive_foreground_queries_fail_at_deadline(self):
        clock = [0.0]
        runner, calls = self.start_runner(clock, [subprocess.TimeoutExpired('adb', 5)] * 3)
        with patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(run.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            with self.assertRaisesRegex(RuntimeError, 'ADB foreground query timed out'):
                run.start_activity(runner, 'emulator-5554', {}, timeout=37)
        self.assertEqual([call[2] for call in calls], [30, 5, 1.5])
        self.assertEqual(clock[0], 37)

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
