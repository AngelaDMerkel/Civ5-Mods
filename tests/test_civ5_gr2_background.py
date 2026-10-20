"""Regression checks for native-test recovery and cross-runner exclusion."""
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from tools.civ5_gr2.background_test import activate_mods, digest, inventory, mod_payloads, render_template, restore
from tools.civ5_test_lock import native_test_lock


class BackgroundRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app, self.data, self.out = (self.root / n for n in ('app', 'data', 'evidence'))
        for path in (self.app, self.data, self.out):
            path.mkdir()
        self.target = self.app / 'DLC/CG2_StaticRenderTest'
        self.put(self.target / 'model.gr2', b'candidate')
        self.put(self.app / 'game', b'unchanged binary')
        self.put(self.app / 'UI.lua', b'original UI\nhook')
        self.put(self.app / 'Map.lua', b'temporary map')
        self.put(self.out / 'ui-original/UI.lua', b'original UI')
        self.put(self.data / 'Saves/campaign.Civ5Save', b'original save')
        self.put(self.data / 'cache/db', b'changed cache')
        self.put(self.data / 'config.ini', b'changed settings')
        self.put(self.data / 'Logs/Lua.log', b'scene log')
        self.put(self.data / 'Saves/auto/test.Civ5Save', b'test autosave')
        for rel, value in [('Saves/campaign.Civ5Save', b'original save'),
                           ('cache/db', b'original cache'), ('config.ini', b'original settings')]:
            self.put(self.out / 'backup' / rel, value)
        self.report = {'app': str(self.app), 'data': str(self.data), 'target': str(self.target),
                       'binaries': {'game': digest(self.app / 'game')},
                       'originals': inventory(self.out / 'backup'),
                       'payload': inventory(self.target),
                       'ui_originals': {'UI.lua': digest(self.out / 'ui-original/UI.lua'), 'Map.lua': None},
                       'installed_hooks': {n: digest(self.app / n) for n in ('UI.lua', 'Map.lua')},
                       'display_before': {'existed': True, 'value': 'true'},
                       'native_rendering': 'unverified'}
        self.harness = SimpleNamespace(game_pids=lambda: [])

    @staticmethod
    def put(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)

    def test_restore_retains_evidence_and_original_bytes(self):
        self.put(self.data / 'GraphicsSettingsDX9.ini', b'WindowResX=1024\nWindowResY=768\n')
        original_graphics = b'WindowResX=1408\nWindowResY=881\n'
        self.put(self.out / 'backup/GraphicsSettingsDX9.ini', original_graphics)
        self.report['originals']['GraphicsSettingsDX9.ini'] = digest(self.out / 'backup/GraphicsSettingsDX9.ini')
        mod = self.data / 'MODS/CG2_test'
        self.put(mod / 'test.lua', b'diagnostic fixture')
        self.report['temporary_mods'] = [dict(target=str(mod), payload=inventory(mod))]
        with patch('tools.civ5_gr2.background_test.subprocess.run') as command:
            restore(self.out, self.report, self.harness)
        self.assertEqual((self.data / 'cache/db').read_bytes(), b'original cache')
        self.assertEqual((self.data / 'config.ini').read_bytes(), b'original settings')
        self.assertEqual((self.app / 'UI.lua').read_bytes(), b'original UI')
        self.assertFalse((self.app / 'Map.lua').exists())
        self.assertFalse(self.target.exists())
        self.assertFalse(mod.exists())
        self.assertFalse((self.data / 'Saves/auto/test.Civ5Save').exists())
        self.assertEqual((self.out / 'after/Saves/auto/test.Civ5Save').read_bytes(), b'test autosave')
        self.assertEqual((self.out / 'after/Logs/Lua.log').read_bytes(), b'scene log')
        self.assertTrue(self.report['restored'])
        self.assertEqual((self.data / 'GraphicsSettingsDX9.ini').read_bytes(), original_graphics)
        self.assertEqual(self.report['native_rendering'], 'unverified')
        self.assertIn('true', command.call_args.args[0])

    def test_changed_ui_stops_recovery_before_data_writes(self):
        (self.app / 'UI.lua').write_bytes(b'another editor')
        with self.assertRaisesRegex(RuntimeError, 'UI changed'):
            restore(self.out, self.report, self.harness)
        self.assertEqual((self.data / 'cache/db').read_bytes(), b'changed cache')
        self.assertTrue(self.target.exists())

    def test_legacy_journal_does_not_touch_unbacked_mod_userdata(self):
        self.put(self.data / 'ModUserData/existing.db', b'user data absent from old journal')
        with patch('tools.civ5_gr2.background_test.subprocess.run'):
            restore(self.out, self.report, self.harness)
        self.assertEqual((self.data / 'ModUserData/existing.db').read_bytes(), b'user data absent from old journal')

    def test_changed_backup_cannot_overwrite_original(self):
        (self.out / 'backup/Saves/campaign.Civ5Save').write_bytes(b'corrupt')
        with self.assertRaisesRegex(RuntimeError, 'backup changed'):
            restore(self.out, self.report, self.harness)
        self.assertEqual((self.data / 'Saves/campaign.Civ5Save').read_bytes(), b'original save')

    def test_live_game_blocks_restoration(self):
        with self.assertRaisesRegex(RuntimeError, 'Close Civ V'):
            restore(self.out, self.report, SimpleNamespace(game_pids=lambda: [123]))

    def test_lock_excludes_other_runner_and_releases_on_error(self):
        path = self.root / 'lock'
        with self.assertRaisesRegex(ValueError, 'owned failure'):
            with native_test_lock('first runner', self.out, path):
                self.assertEqual(json.loads(path.read_text())['owner'], 'first runner')
                with self.assertRaisesRegex(RuntimeError, 'first runner'):
                    with native_test_lock('second runner', self.out, path):
                        self.fail('Concurrent runner acquired the lock')
                raise ValueError('owned failure')
        with native_test_lock('second runner', self.out, path):
            self.assertEqual(json.loads(path.read_text())['owner'], 'second runner')

    def test_unresolved_external_template_fails(self):
        path = self.root / 'template.lua'
        path.write_text('__TEST_MAP_SCRIPT__ __TEST_AUTOPLAY__')
        self.assertEqual(render_template(path), b'CG2_StaticTest.lua false')
        path.write_text('__TEST_NEW_PARAMETER__')
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            render_template(path)

    def test_reload_uses_explicit_save_without_changing_default(self):
        path = self.root / 'load.lua'
        path.write_text('local load = __TEST_LOAD_PATH__')
        self.assertEqual(render_template(path), b'local load = nil')
        save = Path('/tmp/test "quoted" save.Civ5Save')
        self.assertEqual(render_template(path, save).decode(),
                         'local load = ' + json.dumps(str(save)))

    def test_mod_identity_collision_is_refused(self):
        stage = self.root / 'stage'
        name = '12345678-1234-1234-1234-123456789abc'
        self.put(stage / 'test.modinfo', f'<Mod id="{name}" version="1"/>'.encode())
        mods = mod_payloads([stage], self.data)
        self.assertEqual(mods[0]['id'], name)
        with self.assertRaisesRegex(ValueError, 'existing mod'):
            mod_payloads([stage, stage], self.data)
        self.put(self.data / 'MODS/real/test.modinfo', (stage / 'test.modinfo').read_bytes())
        with self.assertRaisesRegex(ValueError, 'existing mod'):
            mod_payloads([stage], self.data)

    def test_changed_mod_is_never_deleted(self):
        target = self.data / 'MODS/CG2_test'
        self.put(target / 'test.lua', b'original fixture')
        self.report['temporary_mods'] = [dict(target=str(target), payload=inventory(target))]
        (target / 'test.lua').write_bytes(b'changed by another editor')
        with self.assertRaisesRegex(RuntimeError, 'Diagnostic mod changed'):
            restore(self.out, self.report, self.harness)
        self.assertTrue(target.exists())
        self.assertEqual((self.data / 'cache/db').read_bytes(), b'changed cache')

    def test_mod_hook_requires_real_activation_and_known_template(self):
        mods = [dict(id='12345678-1234-1234-1234-123456789abc', version=1)]
        with self.assertRaisesRegex(ValueError, 'activation hook changed'):
            activate_mods(b'unknown template', mods)
        code = activate_mods(b'print("[LEKMOD_TEST] starting unattended match")', mods)
        self.assertIn(b'Modding.ActivateEnabledMods()', code)
        self.assertIn(b'assert(active[', code)


if __name__ == '__main__':
    unittest.main()
