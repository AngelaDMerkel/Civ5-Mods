"""Conversion contract tests with original synthetic geometry and textures."""
import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.civ5_gr2.br2 import parse
from tools.civ5_gr2.format import FormatError, Reader, Writer
from tools.civ5_gr2.static import build_graph, convert, verify_conversion

BONE = '0 "World" -1 0 0 0 0 0 0 1 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'
VERTICES = [
    '0 0 0 0 0 1 0.125 0.25 0 0 0 0 255 0 0 0 1 0 0 0 1 0',
    '1 0 0 0 0 1 0.875 0.25 0 0 0 0 255 0 0 0 1 0 0 0 1 0',
    '0 1 0 0 0 1 0.125 0.75 0 0 0 0 255 0 0 0 1 0 0 0 1 0']
BR2 = '\n'.join(['skeleton', BONE, 'meshes:1', 'mesh:"TestMesh"', 'vertices', *VERTICES, 'triangles', '0 1 2', 'end'])


def dds():
    b = bytearray(132);b[:4] = b'DDS '
    struct.pack_into('<I', b, 4, 124)
    struct.pack_into('<II', b, 12, 1, 1)
    struct.pack_into('<I', b, 76, 32)
    struct.pack_into('<I', b, 80, 65)
    struct.pack_into('<5I', b, 88, 32, 255, 65280, 16711680, 4278190080)
    b[128:] = b'\x80\x80\x80\xff'
    return bytes(b)


class StaticTests(unittest.TestCase):
    def test_preserve_geometry_uv_winding_and_rig(self):
        model = parse(BR2)
        data = Writer().encode(build_graph(model, 'Test', 'Test_D.dds', 'Test_S.dds'))
        result = verify_conversion(data, model, 'Test', 'Test_D.dds', 'Test_S.dds')
        self.assertEqual(result[0]['vertices'], 3)
        root = Reader(data).root()
        v = root['VertexDatas'][0]['Vertices'].items[0]
        self.assertEqual(v['TextureCoordinates0'], [0.125, 0.25, 0])
        self.assertEqual(v['Normal'], [0, 0, 1])
        self.assertEqual(root['Meshes'][0]['BoneBindings'][0]['BoneName'], 'World')
        self.assertEqual(root['Meshes'][0]['BoneBindings'][0]['OBBMax'], [1, 1, 0])

    def test_reject_unsupported_input_instead_of_silently_altering(self):
        mutations = {
            'weights': BR2.replace('255 0 0 0', '128 127 0 0', 1),
            'missing_tangent': BR2.replace(VERTICES[0], ' '.join(VERTICES[0].split()[:16])),
            'nonfinite': BR2.replace('0.125', 'nan', 1),
            'bad_index': BR2.replace('0 1 2\nend', '0 1 3\nend'),
            'repeated_index': BR2.replace('0 1 2\nend', '0 1 1\nend'),
            'nonidentity': BR2.replace(BONE, BONE.replace('-1 0 0 0', '-1 1 0 0', 1)),
            'multiple_bones': BR2.replace('meshes:1', BONE.replace('0 "', '1 "', 1)+'\nmeshes:1'),
            'trailing': BR2+'\nanimations',
            'truncated': BR2.rsplit('\n',1)[0],
            'broken_quote': BR2.replace('"World"', '"World'),
            'nul_name': BR2.replace('TestMesh', 'Test\0Mesh'),
            'float32_collapse': BR2.replace(VERTICES[0], '1000000000'+VERTICES[0][1:]).replace(
                VERTICES[1], '1000000001'+VERTICES[1][1:]),
        }
        for label, text in mutations.items():
            with self.subTest(label=label), self.assertRaises(FormatError):
                parse(text)

    def test_preserve_multiple_mesh_bindings(self):
        extra = '\n'.join(['mesh:"Second"','vertices',*VERTICES,'triangles','0 2 1','end'])
        model = parse(BR2.replace('meshes:1','meshes:2').replace('end',extra))
        data = Writer().encode(build_graph(model, 'Test', 'D.dds', 'S.dds'))
        self.assertEqual(len(verify_conversion(data, model, 'Test', 'D.dds', 'S.dds')), 2)

    def test_detect_vertex_or_binding_corruption_after_valid_container_write(self):
        model = parse(BR2)
        for change in ('uv', 'bone', 'texture', 'winding'):
            graph = build_graph(model, 'Test', 'D.dds', 'S.dds')
            if change == 'uv':
                graph['VertexDatas'][0]['Vertices'].items[0]['TextureCoordinates0'][1] = 0.75
            elif change == 'bone':
                graph['Meshes'][0]['BoneBindings'][0].values['BoneName'] = 'Missing'
            elif change == 'texture':
                graph['Materials'][0]['ExtendedData']['ParameterSet1']['ParamDataT'][0].values['String'] = 'Missing.dds'
            else:
                graph['TriTopologies'][0]['Indices16'][0].values['Int16'] = 2
            with self.subTest(change=change), self.assertRaises(FormatError):
                verify_conversion(Writer().encode(graph), model, 'Test', 'D.dds', 'S.dds')

    def test_bundle_reproducibility_and_conflict_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory);source=p/'Test.br2';source.write_text(BR2)
            diffuse, sref = p/'D.dds',p/'S.dds'
            diffuse.write_bytes(dds());sref.write_bytes(dds())
            a = convert(source,p/'one',diffuse,sref)
            b = convert(source,p/'two',diffuse,sref)
            self.assertEqual(a,b)
            self.assertEqual(a['native_game']['status'],'unverified')
            wrapper = ET.parse(p/'one/Test.fxsxml').getroot()
            self.assertEqual([v.attrib['file'] for v in wrapper],['Test.gr2','D.dds','S.dds'])
            for filename in a['files']:
                self.assertEqual((p/'one'/filename).read_bytes(), (p/'two'/filename).read_bytes())
            convert(source,p/'one',diffuse,sref)  # idempotent retry
            (p/'one/Test.gr2').write_bytes(b'other work')
            with self.assertRaisesRegex(FormatError,'refusing to overwrite'):
                convert(source,p/'one',diffuse,sref)
            self.assertEqual((p/'one/Test.gr2').read_bytes(),b'other work')
            with self.assertRaisesRegex(FormatError,'separate from approved sources'):
                convert(source,p,diffuse,sref)

    def test_bad_dds_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);(p/'Test.br2').write_text(BR2)
            (p/'D.dds').write_bytes(dds()[:-1]);(p/'S.dds').write_bytes(dds())
            with self.assertRaisesRegex(FormatError,'DDS payload'):
                convert(p/'Test.br2',p/'out',p/'D.dds',p/'S.dds')
            self.assertFalse((p/'out').exists())


if __name__ == '__main__':
    unittest.main()
