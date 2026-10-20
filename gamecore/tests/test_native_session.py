#!/usr/bin/env python3
"""Exercise restoration with disposable directories; never touches Civ V."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'gamecore/tools'))
from native_session import Session, data_inventory, digest, plain_path, DATA_FOLDERS
from native_test import outcome, prior_recovery, startup, validate_stock, CORE, HOST
from native_mods import prepare_mods, install_mods, verify_mods, activate_mods, validate_load
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

    def test_mod_user_data_restored(self):
        path = self.data / 'ModUserData/state.db'
        path.parent.mkdir()
        path.write_bytes(b'original mod state')
        session = self.prepare()
        path.write_bytes(b'test mod state')
        session.restore_files()
        self.assertEqual(path.read_bytes(), b'original mod state')
        self.assertEqual((self.output / 'after/ModUserData/state.db').read_bytes(), b'test mod state')

    def staged_mod(self):
        stage = self.root / 'stage'
        stage.mkdir()
        (stage / 'test.modinfo').write_text(
            '<Mod id="d571e16c-bb58-40bf-a81f-a919249e7995" version="2"/>')
        (stage / 'test.lua').write_text('return true')
        return stage

    def test_ordinary_mod_install_recovery_and_activation(self):
        stage = self.staged_mod()
        mods = prepare_mods([stage], self.data)
        folders = (*DATA_FOLDERS, *(m['relative'] for m in mods))
        session = Session.prepare(self.output, self.app, self.data, self.mutations,
                                  {'temporary_mods': mods}, data_folders=folders)
        install_mods(mods, self.data)
        verify_mods(mods, self.data)
        self.assertEqual((self.data / mods[0]['relative'] / 'test.lua').read_text(), 'return true')
        code = activate_mods(b'local loadPath = "save"\nif loadPath then return end\n'
                             b'print("[LEKMOD_TEST] starting unattended match")', mods)
        self.assertIn(b'Modding.EnableMod("d571e16c-bb58-40bf-a81f-a919249e7995", 2)', code)
        self.assertLess(code.index(b'DisableMod'), code.index(b'EnableMod'))
        self.assertLess(code.index(b'if loadPath then return end'), code.index(b'ActivateEnabledMods'))
        session.restore_files()
        self.assertFalse((self.data / mods[0]['relative']).exists())
        self.assert_restored()

    def test_existing_mod_identity_refused(self):
        stage = self.staged_mod()
        existing = self.data / 'MODS/user-version'
        existing.mkdir(parents=True)
        (existing / 'user.modinfo').write_bytes((stage / 'test.modinfo').read_bytes())
        with self.assertRaisesRegex(ValueError, 'existing mod'):
            prepare_mods([stage], self.data)
        self.assertTrue((existing / 'user.modinfo').exists())

    def test_duplicate_or_symlink_stage_refused(self):
        stage = self.staged_mod()
        with self.assertRaisesRegex(ValueError, 'existing mod'):
            prepare_mods([stage, stage], self.data)
        (stage / 'linked.lua').symlink_to(stage / 'test.lua')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            prepare_mods([stage], self.data)

    def test_modified_stage_is_not_installed(self):
        stage = self.staged_mod()
        mods = prepare_mods([stage], self.data)
        (stage / 'test.lua').write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'changed since'):
            install_mods(mods, self.data)
        self.assertFalse((self.data / mods[0]['relative']).exists())

    def test_independent_mod_edit_blocks_recovery_check(self):
        stage = self.staged_mod()
        mods = prepare_mods([stage], self.data)
        install_mods(mods, self.data)
        (self.data / mods[0]['relative'] / 'test.lua').write_text('independent edit')
        with self.assertRaisesRegex(RuntimeError, 'changed independently'):
            verify_mods(mods, self.data)

    def test_partial_mod_install_can_be_recovered(self):
        stage = self.staged_mod()
        mods = prepare_mods([stage], self.data)
        folders = (*DATA_FOLDERS, *(m['relative'] for m in mods))
        session = Session.prepare(self.output, self.app, self.data, self.mutations,
                                  {'temporary_mods': mods}, data_folders=folders)
        install_mods(mods, self.data)
        (self.data / mods[0]['relative'] / 'test.lua').unlink()
        verify_mods(mods, self.data)
        session.restore_files()
        self.assertFalse((self.data / mods[0]['relative']).exists())

    def test_changed_activation_hook_refused(self):
        with self.assertRaisesRegex(ValueError, 'hook changed'):
            activate_mods(b'unknown startup', [{'id': 'unused'}])

    def test_saved_mod_load_activates_then_checks_header_before_loading(self):
        code = b'''local function startMatch()
local loadPath = "fixture.Civ5Save"
if loadPath then
Events.PlayerChoseToLoadGame(loadPath)
return
end
end'''
        stage = self.staged_mod()
        result = validate_load(activate_mods(code, prepare_mods([stage], self.data), loading=True))
        self.assertLess(result.index(b'ActivateEnabledMods'), result.index(b'GetFileHeader'))
        self.assertLess(result.index(b'CanLoadSavedGame'), result.index(b'PlayerChoseToLoadGame'))
        self.assertIn(b'assert(compatible == 0', result)
        with self.assertRaisesRegex(ValueError, 'hook changed'):
            validate_load(b'changed hook')

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

    def test_diagnostic_save_path_is_a_lua_string(self):
        path = self.root / 'template.lua'
        path.write_text('local loadPath = __TEST_LOAD_PATH__')
        saved = self.root / 'test "route".Civ5Save'
        text = startup(path, saved)
        self.assertIn(b'\\"route\\".Civ5Save"', text)
        self.assertNotIn(b'__TEST_', text)
        self.assertEqual(startup(path), b'local loadPath = nil')

    def test_stock_control_refuses_an_unrecognized_core(self):
        for relative, contents in ((CORE, b'stock core'), (HOST, b'pinned host')):
            path = self.app / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        config = self.root / 'gamecore'
        abi_path = config / '.compat/pin/abi'
        abi_path.mkdir(parents=True)
        (config / 'compat.lock.json').write_text(json.dumps({'commit': 'pin'}))
        (abi_path / 'aspyr-bnw.json').write_text(json.dumps({
            'stock_gamecore_sha256': [digest(self.app / CORE)],
            'host_executable_sha256': [digest(self.app / HOST)]}))
        with patch('native_test.REPO', self.root):
            self.assertEqual(validate_stock(self.app)['validation']['mode'], 'stock')
            (self.app / CORE).write_bytes(b'unrecognized core')
            with self.assertRaisesRegex(ValueError, 'pinned original'):
                validate_stock(self.app)

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
