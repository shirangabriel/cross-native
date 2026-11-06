import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('ios_run', Path(__file__).resolve().parents[1] / 'run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def data():
    return {'devices': {'com.apple.CoreSimulator.SimRuntime.iOS-26-0': [
        {'udid': 'A', 'name': 'iPhone', 'state': 'Shutdown', 'isAvailable': True},
        {'udid': 'B', 'name': 'iPhone', 'state': 'Booted', 'isAvailable': True}]}}


class RunTests(unittest.TestCase):
    def test_booted_and_explicit_udid(self):
        self.assertEqual(runner.select_device(data())['udid'], 'B')
        self.assertEqual(runner.select_device(data(), 'A')['udid'], 'A')

    def test_ambiguous_name_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            runner.select_device(data(), 'iPhone')

    def test_devicehub_and_legacy_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            developer = Path(temp) / 'Xcode.app/Contents/Developer'
            hub = developer.parent / 'Applications/DeviceHub.app'
            hub.mkdir(parents=True)
            self.assertEqual(runner.simulator_app(developer), hub)
            hub.rmdir()
            legacy = developer / 'Applications/Simulator.app'
            legacy.mkdir(parents=True)
            self.assertEqual(runner.simulator_app(developer), legacy)

    def test_launch_evidence_and_stale_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / 'build/Build/Products/Debug-iphonesimulator/CrossNative.app'
            app.mkdir(parents=True)
            with (app / 'Info.plist').open('wb') as stream:
                plistlib.dump({'CFBundleIdentifier': 'com.example.hello'}, stream)
            commands = []
            def fake(command, **kwargs):
                commands.append(command)
                output = ''
                if 'list' in command:
                    output = json.dumps(data())
                if 'launch' in command:
                    output = 'com.example.hello: 1234\n'
                if 'screenshot' in command:
                    Path(command[-1]).write_bytes(b'fake-png')
                return subprocess.CompletedProcess(command, 0, output, '')
            with patch.object(runner.subprocess, 'run', side_effect=fake), patch.object(runner, 'simulator_app', return_value=Path('/DeviceHub.app')), patch.object(runner.time, 'sleep'):
                self.assertEqual(runner.launch(root, 'B'), 0)
            report = root / 'build/evidence/launch.json'
            saved = json.loads(report.read_text())
            self.assertEqual(saved['status'], 'launched')
            self.assertEqual(saved['device']['udid'], 'B')
            self.assertEqual(saved['pid'], 1234)
            for command in commands:
                if len(command) > 2 and command[2] in ('install', 'terminate', 'launch', 'io', 'bootstatus'):
                    self.assertEqual(command[3], 'B')
            (app / 'Info.plist').unlink()
            self.assertEqual(runner.launch(root, 'B'), 1)
            self.assertEqual(json.loads(report.read_text())['status'], 'failed')
            self.assertFalse((root / 'build/evidence/screenshot.png').exists())


if __name__ == '__main__':
    unittest.main()
