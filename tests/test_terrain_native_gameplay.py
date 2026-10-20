"""Acceptance fixtures must preserve production content and stay out of releases."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from packages import PACKAGES, RT_ID, package_files
from terrain_native_gameplay import stage


class TerrainNativeFixtureTests(unittest.TestCase):
    def test_only_diagnostic_include_changes_production_content(self):
        spec = next(p for p in PACKAGES if p['id'] == RT_ID)
        originals = package_files(spec)
        self.assertNotIn('Lua/C5M_TerrainChecks.lua', originals)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'fixture'
            stage(output)
            evidence = json.loads((output / 'fixture.json').read_text())
            for name, source in originals.items():
                self.assertEqual(evidence['source_hashes'][name],
                                 hashlib.sha256(source.read_bytes()).hexdigest())
                actual = (output / name).read_bytes()
                if name == 'UI/RT_Environment.lua':
                    self.assertEqual(actual, source.read_bytes() +
                        b'\n-- Disposable acceptance fixture only.\ninclude("C5M_TerrainChecks.lua");\n')
                else:
                    self.assertEqual(actual, source.read_bytes())
            mod = ET.parse(output / (spec['name'] + '.modinfo')).getroot()
            self.assertEqual(mod.get('id'), RT_ID)
            self.assertEqual(mod.find('EntryPoints/EntryPoint').get('file'), spec['entry'])
            files = {item.text: item for item in mod.find('Files')}
            self.assertEqual(files['Lua/C5M_TerrainChecks.lua'].get('import'), '1')
            self.assertNotIn('fixture.json', files)
            self.assertEqual([item.text for item in mod.find('Actions/OnModActivated')], spec['actions'])
            with self.assertRaises(ValueError):
                stage(output)


if __name__ == '__main__':
    unittest.main()
