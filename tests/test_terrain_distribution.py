"""Keep the actual standard Terrain manifest independent of external products."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build import manifest, modbuddy
from packages import BNW_ID, PACKAGES, RT_ID, package_files


class TerrainDistributionTests(unittest.TestCase):
    def test_standard_release_requires_only_bnw_and_ships_no_engine_or_installer(self):
        spec = next(item for item in PACKAGES if item['id'] == RT_ID)
        files = package_files(spec)
        mod = manifest(files, spec)
        dependencies = list(mod.find('Dependencies'))
        self.assertEqual([(entry.tag, entry.get('id').lower()) for entry in dependencies],
                         [('Dlc', BNW_ID.lower())])
        self.assertIsNone(mod.find('./Dependencies/Mod'))
        self.assertEqual(mod.findtext('./Properties/SupportsMac'), '1')
        self.assertEqual(mod.findtext('./Properties/SupportsSinglePlayer'), '1')
        # This is a content package. Native editions must have their own explicit
        # distribution boundary instead of adding a launcher/library here.
        content_types = {'.lua', '.sql', '.xml', '.dds', '.gr2', '.fxsxml', '.ftsxml'}
        self.assertTrue(files)
        for name in files:
            self.assertIn(Path(name).suffix.lower(), content_types, name)
        self.assertEqual(mod.find('./EntryPoints/EntryPoint').get('type'), 'InGameUIAddin')
        # Validate the project path too; Workshop staging must preserve the same
        # dependency contract as the locally installable folder manifest.
        project = modbuddy(files, mod, spec)
        ns = {'ms': 'http://schemas.microsoft.com/developer/msbuild/2003'}
        import xml.etree.ElementTree as ET
        project_deps = ET.fromstring(project.findtext('ms:PropertyGroup/ms:Dependencies', namespaces=ns))
        self.assertEqual([(entry.tag, entry.get('id').lower()) for entry in project_deps],
                         [('Dlc', BNW_ID.lower())])


if __name__ == '__main__':
    unittest.main()
