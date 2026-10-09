"""Batch preflight, fixture isolation and validation evidence regressions."""
import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from test_civ5_gr2_static import BR2, dds
from tools.civ5_gr2.batch import batch, verify_bundle
from tools.civ5_gr2.format import FormatError
from tools.civ5_gr2.harness import harness, FIXTURE_ID


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=Path(self.temp.name)
        for name,data in [('A.br2',BR2.encode()),('B.br2',BR2.encode()),('D.dds',dds()),('S.dds',dds())]:
            (self.p/name).write_bytes(data)
        def pin(name):
            return {'path':name,'sha256':hashlib.sha256((self.p/name).read_bytes()).hexdigest()}
        self.spec={'version':1,'assets':[{'name':n,'source':pin(n+'.br2'),'diffuse':pin('D.dds'),'sref':pin('S.dds')} for n in ['A','B']]}
        self.manifest=self.p/'batch.json';self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.spec))

    def test_reproducible_batch_and_revalidation(self):
        a=batch(self.manifest,self.p/'one');b=batch(self.manifest,self.p/'two')
        self.assertEqual(a,b)
        self.assertEqual(len(a['assets']),2)
        self.assertEqual(a['native_game']['status'],'unverified')
        verify_bundle(self.p/'one/A/A.conversion.json',self.p/'A.br2')
        (self.p/'one/A/D.dds').write_bytes(b'changed')
        with self.assertRaisesRegex(FormatError,'bundle hash mismatch'):
            verify_bundle(self.p/'one/A/A.conversion.json',self.p/'A.br2')

    def test_all_input_hashes_checked_before_output(self):
        (self.p/'B.br2').write_text(BR2+'\n// changed')
        with self.assertRaisesRegex(FormatError,'input hash mismatch'):
            batch(self.manifest,self.p/'out')
        self.assertFalse((self.p/'out').exists())

    def test_failed_later_conversion_does_not_expose_partial_batch(self):
        (self.p/'B.br2').write_text('not BR2')
        self.spec['assets'][1]['source']['sha256']=hashlib.sha256(b'not BR2').hexdigest();self.save()
        with self.assertRaises(FormatError):batch(self.manifest,self.p/'out')
        self.assertFalse((self.p/'out').exists())
        self.assertEqual(list(self.p.glob('.civ5-gr2-batch-*')),[])

    def test_case_insensitive_model_and_texture_collisions(self):
        self.spec['assets'][1]['name']='a';self.save()
        with self.assertRaisesRegex(FormatError,'duplicate batch model'):
            batch(self.manifest,self.p/'out')
        self.spec['assets'][1]['name']='B'
        (self.p/'other').mkdir();(self.p/'other/D.dds').write_bytes(b'other')
        self.spec['assets'][1]['diffuse']={'path':'other/D.dds','sha256':hashlib.sha256(b'other').hexdigest()};self.save()
        with self.assertRaisesRegex(FormatError,'conflicting texture VFS'):
            batch(self.manifest,self.p/'out')

    def test_fixture_uses_generated_manifest_and_no_production_relationships(self):
        batch(self.manifest,self.p/'out')
        report=harness(self.p/'out/A/A.conversion.json',self.p/'A.br2',self.p/'fixture')
        self.assertEqual(report['native_game']['status'],'unverified')
        mod=ET.parse(self.p/'fixture/GR2 Static Render Test.modinfo').getroot()
        self.assertEqual(mod.get('id'),FIXTURE_ID)
        self.assertEqual(len(mod.find('References')),0)
        self.assertEqual(len(mod.find('Blocks')),0)
        self.assertEqual(len(mod.find('Dependencies')),1)
        self.assertEqual([e.get('type') for e in mod.find('EntryPoints')],['InGameUIAddin','MapScript'])
        for e in mod.find('Files'):
            self.assertEqual(e.get('md5'),hashlib.md5((self.p/'fixture'/e.text).read_bytes()).hexdigest().upper())
        scene=(self.p/'fixture/Lua/CG2_Scene.lua').read_text()
        self.assertNotIn('__HASH__',scene)
        self.assertIn('CG2_STATIC_TEST_V1',scene)


if __name__=='__main__':unittest.main()
