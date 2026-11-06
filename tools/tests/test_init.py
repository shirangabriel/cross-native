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
        (self.root / 'AGENTS.md').touch()
        (self.root / 'workflow/defaults').mkdir(parents=True)
        (self.root / 'workflow/defaults/main.md').touch()
        (self.root / 'workflow/init.md').touch()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin), RECORD=str(self.root / 'record.json'))

    def invoke(self, *args, answers='', cwd=None):
        return subprocess.run([sys.executable, str(self.root / 'tools/init'), *args],
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
                result = self.invoke('--agent', agent, answers='Garden\nboth\ncom.example.garden\nminimal\ncodex\n', cwd=self.bin)
                self.assertEqual(result.returncode, 0, result.stderr)
                record = json.loads((self.root / 'record.json').read_text())
                self.assertEqual(record['cwd'], str(self.root))
                self.assertIn('dedicated iOS and Android subagents', record['args'][-1])
                self.assertIn('.cross-native/project.json', record['args'][-1])
                if agent == 'codex':
                    self.assertEqual(record['args'][:2], ['--cd', str(self.root)])
                if agent == 'cursor':
                    self.assertEqual(record['args'][:2], ['--workspace', str(self.root)])

    def test_validation_save_and_resume_preserve_project(self):
        result = self.invoke('--no-launch', answers='Garden\nwrong\nandroid\ninvalid-id\ncom.example.garden\nminimal\nclaude\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads((self.root / '.cross-native/project.json').read_text())
        self.assertEqual(config['platforms'], ['android'])
        (self.root / 'android').mkdir()
        source = self.root / 'android/keep.kt'
        source.write_text('developer work')
        resumed = self.invoke('--no-launch', '--agent', 'cursor')
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertIn('Resuming', resumed.stdout)
        self.assertEqual(source.read_text(), 'developer work')
        self.assertFalse((self.root / 'ios').exists())

    def test_missing_agent_saves_answers_for_retry(self):
        result = self.invoke(answers='Garden\nios\ncom.example.garden\nminimal\ncodex\n')
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
        result = self.invoke(answers='Garden\nios\ncom.example.garden\nminimal\ncodex\n')
        self.assertEqual(result.returncode, 7)


if __name__ == '__main__':
    unittest.main()
