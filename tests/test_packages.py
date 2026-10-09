"""Guard package composition as independently owned mod sources are combined."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from packages import package_files


class PackageCompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.terrain = self.root / 'terrain/src'
        self.irrigation = self.root / 'irrigation/src'
        self.terrain.mkdir(parents=True)
        self.irrigation.mkdir(parents=True)
        self.spec = {'source': self.terrain, 'components': [self.irrigation]}

    def write(self, root, rel, text='source'):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_component_keeps_installed_path_and_own_source(self):
        terrain = self.write(self.terrain, 'Lua/RT_Gameplay.lua')
        irrigation = self.write(self.irrigation, 'Lua/RT_Irrigation.lua')
        self.assertEqual(package_files(self.spec), {
            'Lua/RT_Gameplay.lua': terrain, 'Lua/RT_Irrigation.lua': irrigation,
        })

    def test_duplicate_component_path_is_rejected(self):
        self.write(self.terrain, 'SQL/shared.sql')
        self.write(self.irrigation, 'SQL/shared.sql')
        with self.assertRaisesRegex(ValueError, 'Duplicate package path'):
            package_files(self.spec)

    def test_flattened_vfs_collision_is_case_insensitive(self):
        self.write(self.terrain, 'Lua/first/Helper.lua')
        self.write(self.irrigation, 'Lua/second/helper.lua')
        with self.assertRaisesRegex(ValueError, 'Duplicate VFS name'):
            package_files(self.spec)

    def test_installed_path_collision_is_case_insensitive(self):
        self.write(self.terrain, 'SQL/Rules.sql')
        self.write(self.irrigation, 'SQL/rules.sql')
        with self.assertRaisesRegex(ValueError, 'Duplicate package path'):
            package_files(self.spec)

    def test_only_registered_runtime_roots_and_formats_are_packaged(self):
        runtime = self.write(self.irrigation, 'SQL/farms.sql')
        self.write(self.irrigation, 'README.md')
        self.write(self.irrigation.parent, 'tests/test_farms.lua')
        self.write(self.root, 'shared/references/Reference.xml')
        self.write(self.root, 'tools/builder.py')
        self.assertEqual(package_files(self.spec), {'SQL/farms.sql': runtime})

    def test_missing_component_fails_instead_of_silently_omitting_feature(self):
        self.spec['components'] = [self.root / 'missing/src']
        with self.assertRaisesRegex(ValueError, 'Missing package source directory'):
            package_files(self.spec)


if __name__ == '__main__':
    unittest.main()
