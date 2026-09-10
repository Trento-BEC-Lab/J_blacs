"""Safeguard tests; never modify the real environment."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('environment', Path(__file__).with_name('environment.py'))
env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(env)


def package(version='1', editable=False, pip=True):
    return dict(version=version, editable=editable, pip=pip)


class EnvironmentTests(unittest.TestCase):
    def test_successful_sync_with_metadata_issues_exits_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            contents = '@EXPLICIT\nhttps://example.org/wanted.conda\n'
            lock.write_text(contents)
            with patch.object(env, 'LOCK', lock), patch.object(env, 'requirements', return_value={}), \
                 patch.object(env, 'export', return_value=contents), \
                 patch.object(env, 'inventory', return_value={}), \
                 patch.object(env, 'sync_pip'), patch.object(env, 'health', return_value=1) as health, \
                 patch.object(sys, 'argv', ['environment.py', 'sync']):
                self.assertEqual(env.main(), 0)
                health.assert_called_once()

    def test_sync_preserves_editables_and_removes_only_extra_pip(self):
        before = {'local': package(editable=True), 'conda': package(pip=False),
                  'extra': package(), 'wanted': package()}
        after = {'local': before['local'], 'conda': before['conda'], 'wanted': package('2')}
        with patch.object(env, 'inventory', side_effect=[before, after]), patch.object(env, 'run') as run:
            env.sync_pip({'wanted': '2'})
        calls = [list(map(str, c.args[0])) for c in run.call_args_list]
        self.assertEqual(calls[0][-3:], ['uninstall', '-y', 'extra'])
        self.assertEqual(calls[1][-3:], ['install', '--no-deps', 'wanted==2'])

    def test_collision_stops_before_mutation(self):
        for item in [package(editable=True), package(pip=False)]:
            with patch.object(env, 'inventory', return_value={'wanted': item}), patch.object(env, 'run') as run:
                with self.assertRaises(ValueError):
                    env.sync_pip({'wanted': '2'})
                run.assert_not_called()

    def test_conda_difference_stops_before_pip_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            lock.write_text('@EXPLICIT\nhttps://example.org/wanted.conda\n')
            with patch.object(env, 'LOCK', lock), patch.object(env, 'requirements', return_value={}), \
                 patch.object(env, 'export', return_value='@EXPLICIT\nhttps://example.org/other.conda\n'), \
                 patch.object(env, 'sync_pip') as sync, patch.object(sys, 'argv', ['environment.py', 'sync']):
                self.assertEqual(env.main(), 2)
                sync.assert_not_called()

    def test_failed_prefetch_does_not_remove_live_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / 'lock'
            lock.write_text('@EXPLICIT\nhttps://example.org/wanted.conda\n')
            with patch.object(env, 'LOCK', lock), patch.object(env, 'requirements', return_value={}), \
                 patch('builtins.input', return_value='rebuild'), \
                 patch.object(sys, 'argv', ['environment.py', 'rebuild']), \
                 patch.object(env, 'run', side_effect=subprocess.CalledProcessError(1, 'prefetch')) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    env.main()
                self.assertEqual(run.call_count, 1)
                args = run.call_args.args[0]
                self.assertIn('--download-only', args)
                self.assertNotEqual(args[args.index('-p') + 1], env.PREFIX)


if __name__ == '__main__':
    unittest.main()
