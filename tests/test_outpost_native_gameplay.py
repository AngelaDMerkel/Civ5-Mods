"""Fixture safety and production-path fidelity, not native gameplay evidence."""
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from outpost_native_gameplay import ordinary

try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    LuaRuntime = None


class GameplayFixtureTests(unittest.TestCase):
    @unittest.skipIf(LuaRuntime is None, 'install tests/requirements.txt')
    def test_all_native_scenarios_compile_as_lua51(self):
        lua = LuaRuntime()
        for path in (ROOT / 'mods/resource-outposts/tests/native').glob('*.lua'):
            with self.subTest(source=path.name):
                lua.execute('assert(loadstring(...))', path.read_text())

    @unittest.skipIf(LuaRuntime is None, 'install tests/requirements.txt')
    def test_checks_never_mutate_unrelated_campaigns(self):
        source = (ROOT / 'mods/resource-outposts/tests/native/RO_GameplayChecks.lua').read_text()
        cases = [('', 0, False, 24, 16, 0), ('CG2_STATIC_TEST_V1', 1, False, 24, 16, 0),
                 ('CG2_STATIC_TEST_V1', 0, True, 24, 16, 0), ('CG2_STATIC_TEST_V1', 0, False, 25, 16, 0),
                 ('CG2_STATIC_TEST_V1', 0, False, 24, 16, 1)]
        for marker, turn, multi, width, height, active in cases:
            lua = LuaRuntime()
            lua.globals().marker = marker; lua.globals().turn = turn; lua.globals().multi = multi
            lua.globals().width = width; lua.globals().height = height; lua.globals().active = active
            lua.execute('''
                Game={IsGameMultiPlayer=function() return multi end,GetElapsedGameTurns=function() return turn end,
                      GetActivePlayer=function() return active end}
                Map={GetPlot=function() return {GetScriptData=function() return marker end} end,
                     GetGridSize=function() return width,height end}
            ''')
            # No mutation APIs, runtime or events exist: reaching them fails.
            lua.execute(source.replace('__RO_SCENARIO__', 'core'))

    def test_ordinary_stage_keeps_real_sql_entries_and_art(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'fixture'
            ordinary(output, 'integration')
            transport = ET.parse(next((output / 'transport').glob('*.modinfo'))).getroot()
            self.assertEqual(len(transport.find('Actions/OnModActivated')), 0)
            for slug, folder, entry in [('Resource-Outposts', 'resource-outposts', 'UI/RO_UI.xml'),
                                        ('Realistic-Terrain', 'realistic-terrain', 'UI/RT_Environment.xml')]:
                target = output / 'mods' / slug
                mod = ET.parse(next(target.glob('*.modinfo'))).getroot()
                names = [item.text for item in mod.find('Files')]
                self.assertEqual(names, sorted(names), 'match the production manifest order')
                self.assertEqual(mod.find('EntryPoints/EntryPoint').get('file'), entry)
                self.assertTrue(any(x.text.endswith('.sql') for x in mod.find('Actions/OnModActivated')))
                original = ROOT / 'mods' / folder / 'src' / entry
                self.assertEqual((target / entry).read_bytes(), original.read_bytes())
                script = original.with_suffix('.lua').read_bytes()
                self.assertTrue((target / Path(entry).with_suffix('.lua')).read_bytes().startswith(script))
            with self.assertRaisesRegex(ValueError, 'new ordinary-mod'):
                ordinary(output, 'integration')


if __name__ == '__main__':
    unittest.main()
