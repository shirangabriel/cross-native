"""Process-level tests; fake agents record launch arguments without model calls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'init'


class InitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cross native ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'tools').mkdir()
        shutil.copy2(SOURCE, self.root / 'tools/init')
        shutil.copy2(SOURCE.parent / 'project.py', self.root / 'tools/project.py')
        shutil.copy2(SOURCE.parent / 'dev', self.root / 'tools/dev')
        for platform in ('ios', 'android'):
            template = self.root / 'templates' / platform
            template.mkdir(parents=True)
            (template / 'identity.txt').write_text('__APP_ID__ __APP_NAME_XML__')
            script = template / 'build.sh'
            script.write_text('#!/bin/sh\nexit 0\n')
            script.chmod(0o755)
            (template / 'run.py').write_text('import sys\nprint("Launched", sys.argv[1:])\n')
        (self.root / 'AGENTS.md').touch()
        (self.root / 'workflow/defaults').mkdir(parents=True)
        (self.root / 'workflow/defaults/main.md').touch()
        (self.root / 'workflow/init.md').touch()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin), RECORD=str(self.root / 'record.json'))

    def invoke(self, *args, answers='', cwd=None):
        return subprocess.run([sys.executable, str(self.root / 'tools/init'), '--skip-build', *args],
                              input=answers, text=True, capture_output=True,
                              cwd=cwd or self.root, env=self.env)

    def fake_agent(self, binary):
        path = self.bin / binary
        path.write_text(f'#!{sys.executable}\nimport os,json,sys\n'
                        'with open(os.environ["RECORD"], "w") as f:\n'
                        ' json.dump({"cwd":os.getcwd(),"args":sys.argv[1:]}, f)\n')
        path.chmod(0o755)

    def test_all_adapters_receive_root_and_setup_task(self):
        for agent, binary in [('codex', 'codex'), ('claude', 'claude'), ('cursor', 'agent')]:
            with self.subTest(agent=agent):
                self.fake_agent(binary)
                result = self.invoke('--agent', agent, answers='Garden\nboth\ncom.example.garden\n', cwd=self.bin)
                self.assertEqual(result.returncode, 0, result.stderr)
                record = json.loads((self.root / 'record.json').read_text())
                self.assertEqual(record['cwd'], str(self.root))
                self.assertIn('dedicated iOS and Android subagents', record['args'][-1])
                self.assertTrue((self.root / 'ios/identity.txt').is_file())
                self.assertIn('.cross-native/project.json', record['args'][-1])
                if agent == 'codex':
                    self.assertEqual(record['args'][:2], ['--cd', str(self.root)])
                if agent == 'cursor':
                    self.assertEqual(record['args'][:2], ['--workspace', str(self.root)])

    def test_validation_save_and_resume_preserve_project(self):
        result = self.invoke('--no-launch', answers='Garden\nwrong\nandroid\ninvalid-id\ncom.example.garden\nclaude\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads((self.root / '.cross-native/project.json').read_text())
        self.assertEqual(config['platforms'], ['android'])
        self.assertIsNone(config['agent'])
        self.assertEqual(config['starting_experience'], 'A single native screen displaying Hello World.')
        self.assertNotIn('Starting experience', result.stdout)
        source = self.root / 'android/keep.kt'
        source.write_text('developer work')
        resumed = self.invoke('--no-launch', '--agent', 'cursor')
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertIn('Resuming', resumed.stdout)
        self.assertEqual(source.read_text(), 'developer work')
        self.assertFalse((self.root / 'ios').exists())

    def test_missing_agent_saves_answers_for_retry(self):
        result = self.invoke('--agent', 'codex', answers='Garden\nios\ncom.example.garden\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('not found on PATH', result.stderr)
        self.assertTrue((self.root / '.cross-native/project.json').is_file())

    def test_interrupted_questionnaire_does_not_write_config(self):
        result = self.invoke(answers='Garden\n')
        self.assertEqual(result.returncode, 130)
        self.assertFalse((self.root / '.cross-native/project.json').exists())

    def test_corrupt_config_not_overwritten(self):
        path = self.root / '.cross-native/project.json'
        path.parent.mkdir()
        path.write_text('{broken')
        result = self.invoke('--no-launch')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(path.read_text(), '{broken')

    def test_agent_exit_status_propagates(self):
        path = self.bin / 'codex'
        path.write_text(f'#!{sys.executable}\nraise SystemExit(7)\n')
        path.chmod(0o755)
        result = self.invoke('--agent', 'codex', answers='Garden\nios\ncom.example.garden\n')
        self.assertEqual(result.returncode, 7)

    def test_numbered_choices_and_no_agent(self):
        result = self.invoke(answers='Garden\n2\ncom.example.garden\n1\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / 'ios/identity.txt').exists())
        self.assertFalse((self.root / 'android').exists())
        self.assertFalse((self.root / 'record.json').exists())

    def test_generation_escapes_name_and_preserves_modified_files(self):
        result = self.invoke('--no-launch', answers='Garden & "Friends"\nandroid\ncom.example.garden\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.root / 'android/identity.txt'
        self.assertIn('Garden &amp; &quot;Friends&quot;', path.read_text())
        path.write_text('developer edits')
        self.assertEqual(self.invoke('--no-launch').returncode, 0)
        self.assertEqual(path.read_text(), 'developer edits')

    def test_existing_project_is_not_overwritten(self):
        (self.root / 'ios').mkdir()
        result = self.invoke('--no-launch', answers='Garden\nios\ncom.example.garden\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('refusing to overwrite', result.stderr)
        self.assertEqual(list((self.root / 'ios').iterdir()), [])

    def test_build_failure_blocks_agent_and_saves_log(self):
        script = self.root / 'templates/ios/build.sh'
        script.write_text('#!/bin/sh\necho Missing SDK\nexit 3\n')
        self.fake_agent('codex')
        result = subprocess.run([sys.executable, str(self.root / 'tools/init'), '--agent', 'codex'],
                                input='Garden\nios\ncom.example.garden\n', text=True,
                                capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / 'record.json').exists())
        self.assertIn('Missing SDK', (self.root / '.build/logs/ios-build.log').read_text())
        self.assertTrue((self.root / '.cross-native/project.json').exists())

    def test_shipped_templates_generate_valid_identity_resources(self):
        import plistlib
        import xml.etree.ElementTree as ET
        shutil.rmtree(self.root / 'templates')
        shutil.copytree(SOURCE.parent.parent / 'templates', self.root / 'templates')
        name = 'Garden & "Friends" __APP_ID__'
        result = self.invoke('--no-launch', answers=name + '\nboth\ncom.example.garden\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        with (self.root / 'ios/CrossNative/Info.plist').open('rb') as stream:
            info = plistlib.load(stream)
        self.assertEqual(info['CFBundleDisplayName'], name)
        text = ET.parse(self.root / 'android/app/src/main/res/values/strings.xml').getroot().find('string').text
        self.assertEqual(text, '"' + name.replace('"', '\\"') + '"')
        jar = Path('gradle/wrapper/gradle-wrapper.jar')
        self.assertEqual((self.root / 'android' / jar).read_bytes(),
                         (self.root / 'templates/android' / jar).read_bytes())
        for platform in ('ios', 'android'):
            self.assertTrue(os.access(self.root / platform / 'build.sh', os.X_OK))

    def test_default_flow_builds_and_runs_before_agent(self):
        self.fake_agent('codex')
        result = subprocess.run([sys.executable, str(self.root / 'tools/init'), '--agent', 'codex'],
                                input='Garden\nios\ncom.example.garden\n', text=True,
                                capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('OK ios build', result.stdout)
        self.assertIn('OK ios launch', result.stdout)
        self.assertTrue((self.root / 'record.json').exists())

    def test_failed_launch_blocks_agent_but_attempts_other_platform(self):
        (self.root / 'templates/ios/run.py').write_text('raise SystemExit(4)\n')
        self.fake_agent('codex')
        result = subprocess.run([sys.executable, str(self.root / 'tools/init'), '--agent', 'codex'],
                                input='Garden\nboth\ncom.example.garden\n', text=True,
                                capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 1)
        self.assertIn('OK android launch', result.stdout)
        self.assertFalse((self.root / 'record.json').exists())

    def test_skip_run_builds_without_launching_devices(self):
        result = subprocess.run([sys.executable, str(self.root / 'tools/init'), '--no-launch', '--skip-run'],
                                input='Garden\nios\ncom.example.garden\n', text=True,
                                capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / '.build/logs/ios-build.log').exists())
        self.assertFalse((self.root / '.build/logs/ios-run.log').exists())

    def test_dev_run_all_uses_configured_platform_and_device(self):
        self.assertEqual(self.invoke('--no-launch', answers='Garden\nios\ncom.example.garden\n').returncode, 0)
        result = subprocess.run([sys.executable, str(self.root / 'tools/dev'), 'run', 'all', '--ios-device', 'device with spaces'],
                                text=True, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("['--device', 'device with spaces']", result.stdout)
        self.assertNotIn('Building android', result.stdout)


if __name__ == '__main__':
    unittest.main()
