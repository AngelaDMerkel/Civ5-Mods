#!/usr/bin/env python3
"""Exercise restoration with disposable directories; never touches Civ V."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'gamecore/tools'))
from native_session import Session, data_inventory, digest, plain_path
from native_test import outcome, prior_recovery, startup
from tools.civ5_test_lock import native_test_lock


class NativeSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='c5m-recovery-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'app'
        self.data = self.root / 'data'
        self.output = self.root / 'session'
        for name, contents in {'app/core': b'stock', 'app/menu': b'normal UI',
                               'data/config.ini': b'original configuration',
                               'data/Saves/Single/save': b'player save',
                               'data/Logs/Lua.log': b'previous log',
                               'data/cache/data.db': b'previous cache'}.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        (self.data / 'Saves/empty').mkdir()
        self.initial = data_inventory(self.data)
        self.mutations = {'core': b'new core', 'menu': b'normal UI\ntest'}

    def prepare(self):
        return Session.prepare(self.output, self.app, self.data, self.mutations, {})

    def assert_restored(self):
        self.assertEqual(data_inventory(self.data), self.initial)
        self.assertEqual((self.app / 'core').read_bytes(), b'stock')
        self.assertEqual((self.app / 'menu').read_bytes(), b'normal UI')

    def test_prepare_does_not_modify_game(self):
        self.prepare()
        self.assert_restored()

    def test_run_data_preserved_then_originals_restored(self):
        session = self.prepare()
        session.install(self.mutations)
        (self.data / 'config.ini').write_bytes(b'test settings')
        (self.data / 'Logs/Lua.log').write_bytes(b'test evidence')
        (self.data / 'Saves/Single/save').unlink()
        (self.data / 'Saves/empty').rmdir()
        (self.data / 'ModdedSaves/Single').mkdir(parents=True)
        (self.data / 'ModdedSaves/Single/newsave').write_bytes(b'test save')
        (self.data / 'UserSettings.ini').write_bytes(b'new setting')
        session.restore_files()
        self.assert_restored()
        self.assertEqual((self.output / 'after/Logs/Lua.log').read_bytes(), b'test evidence')
        self.assertEqual((self.output / 'after/ModdedSaves/Single/newsave').read_bytes(), b'test save')
        self.assertTrue(session.report['files_restored'])
        self.assertFalse(session.report['restored'])  # Preferences still belong to the runner.

    def test_repeated_recovery_does_not_overwrite_evidence(self):
        session = self.prepare()
        session.install(self.mutations)
        (self.data / 'Logs/Lua.log').write_bytes(b'new evidence')
        session.restore_files()
        Session.load(self.output).restore_files()
        self.assert_restored()
        self.assertEqual((self.output / 'after/Logs/Lua.log').read_bytes(), b'new evidence')

    def test_recovery_before_install(self):
        self.prepare().restore_files()
        self.assert_restored()

    def test_interrupted_partial_install(self):
        self.prepare()
        (self.app / 'core').write_bytes(self.mutations['core'])
        Session.load(self.output).restore_files()
        self.assert_restored()

    def test_interrupted_atomic_replacement(self):
        self.prepare()
        (self.app / 'core.c5m-pending').write_bytes(self.mutations['core'])
        Session.load(self.output).restore_files()
        self.assert_restored()
        self.assertFalse((self.app / 'core.c5m-pending').exists())

    def test_new_app_file_is_removed(self):
        self.mutations['temporary'] = b'test-only'
        session = self.prepare()
        session.install(self.mutations)
        session.restore_files()
        self.assertFalse((self.app / 'temporary').exists())

    def test_tampered_app_is_not_overwritten(self):
        session = self.prepare()
        session.install(self.mutations)
        (self.app / 'menu').write_bytes(b'other chat edit')
        with self.assertRaisesRegex(RuntimeError, 'independently'):
            session.restore_files()
        self.assertEqual((self.app / 'menu').read_bytes(), b'other chat edit')
        self.assertEqual((self.app / 'core').read_bytes(), b'new core')

    def test_corrupt_backup_stops_before_restoring(self):
        session = self.prepare()
        session.install(self.mutations)
        (self.output / 'data-backup/config.ini').write_bytes(b'corrupt')
        with self.assertRaisesRegex(RuntimeError, 'backup changed'):
            session.restore_files()
        self.assertEqual((self.app / 'core').read_bytes(), b'new core')

    def test_install_refuses_changed_original(self):
        session = self.prepare()
        (self.app / 'menu').write_bytes(b'other edit')
        with self.assertRaisesRegex(RuntimeError, 'since backup'):
            session.install(self.mutations)
        self.assertEqual((self.app / 'core').read_bytes(), b'stock')

    def test_install_refuses_different_mutation_bytes(self):
        session = self.prepare()
        with self.assertRaisesRegex(ValueError, 'Mutation bytes'):
            session.install(dict(self.mutations, core=b'unrecorded core'))
        self.assert_restored()

    def test_backup_failure_never_installs(self):
        with patch('native_session.shutil.copy2', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.prepare()
        self.assert_restored()

    def test_symlinks_and_traversal_rejected(self):
        for name in ('../escape', '/absolute', '.'):
            with self.assertRaises(ValueError):
                plain_path(self.app, name)
        (self.data / 'Saves/link').symlink_to(self.app, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            self.prepare()

    def test_recovery_refuses_symlink_added_during_run(self):
        session = self.prepare()
        session.install(self.mutations)
        (self.data / 'Logs/link').symlink_to(self.app / 'core')
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            session.restore_files()
        self.assertEqual((self.app / 'core').read_bytes(), b'new core')

    def test_unrestored_journal_blocks_new_run(self):
        session = self.prepare()
        with self.assertRaisesRegex(RuntimeError, 'Recover'):
            prior_recovery(self.output / 'session.json')
        session.report['restored'] = True
        session.save()
        prior_recovery(self.output / 'session.json')

    def test_existing_output_not_reused(self):
        self.prepare()
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_only_current_unique_success_counts(self):
        self.assertIsNone(outcome('[C5M_NATIVE] run=old status=PASS', 'new'))
        line = '[C5M_NATIVE] run=new status=PASS version=0.1.0'
        self.assertEqual(outcome(line, 'new'), 'PASS')
        self.assertIsNone(outcome(line + '\n' + line, 'new'))
        self.assertEqual(outcome(line + '\n[C5M_NATIVE] run=new status=FAIL error=oops', 'new'), 'FAIL')

    def test_unknown_template_parameter_refused(self):
        path = self.root / 'template.lua'
        path.write_text('__TEST_MAJORS__ __TEST_NEW_PARAMETER__')
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            startup(path)

    def test_native_lease_excludes_other_process(self):
        lease = self.root / 'lease'
        code = '''import fcntl,sys
with open(sys.argv[1], 'a+') as stream:
 try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
 except BlockingIOError: sys.exit(42)
'''
        with native_test_lock('fixture', self.output, path=lease):
            self.assertEqual(subprocess.run([sys.executable, '-c', code, str(lease)]).returncode, 42)
        self.assertEqual(subprocess.run([sys.executable, '-c', code, str(lease)]).returncode, 0)


if __name__ == '__main__':
    unittest.main()
