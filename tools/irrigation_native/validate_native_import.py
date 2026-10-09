#!/usr/bin/env python3
"""Compare exported native GLB buffers and GR2 graphs against installed sources."""
from pathlib import Path
import argparse
import json
import struct
import numpy as np
from native_gr2 import Reader, build_decoder
from native_scene import parts, selected_models, regular_farm_states
from import_native_farms import OUT, semantic, digest


def glb(path):
    raw = Path(path).read_bytes()
    magic, version, size, length, kind = struct.unpack_from('<5I', raw)
    if (magic, version, size, kind) != (0x46546c67, 2, len(raw), 0x4e4f534a):
        raise ValueError('Invalid GLB container')
    doc = json.loads(raw[20:20+length]); blob = raw[28+length:]
    def accessor(index):
        item = doc['accessors'][index]; view = doc['bufferViews'][item['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4'}[item['componentType']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[item['type']]
        data = np.frombuffer(blob, dtype=dtype, count=item['count']*width,
                             offset=view.get('byteOffset', 0)+item.get('byteOffset', 0))
        return data if width == 1 else data.reshape(-1, width)
    return doc, accessor


def validate(output):
    manifest = json.loads((output/'native-import.json').read_text())
    cache = output/'native-local'; decoder = build_decoder(output/'codec')
    checked = []
    for item in manifest['extracted_assets']:
        if digest(cache/Path(item['entry']).name) != item['sha256']:
            raise ValueError('Extract changed: '+item['entry'])
    for record in manifest['models']:
        name = record['name']; folder = output/name
        db = 'conquestdeluxemodels' if 'terrace' in name else 'improvementmodels'
        source = Reader(cache/(name+'.gr2'), cache/(db+'_stringdatabase.gsd'), decoder).root()
        exported = Reader(folder/(name+'-uncompressed.gr2')).root()
        if semantic(source) != semantic(exported):
            raise ValueError('GR2 round-trip mismatch')
        if record.get('construction_states'):
            assert regular_farm_states(source) == record['construction_states']
        selected = selected_models(source, record.get('preview_model_names', [m['Name'] for m in source['Models']]))
        scene = parts(selected); doc, acc = glb(folder/(name+'.glb'))
        assert len(scene) == len(doc['meshes'])
        for part, mesh, node in zip(scene, doc['meshes'], doc['nodes']):
            assert mesh['name'] == part['name']
            assert len(part['groups']) == len(mesh['primitives'])
            np.testing.assert_allclose(np.array(node['matrix']).reshape(4, 4).T, part['transform'], atol=1e-7)
            for group, primitive in zip(part['groups'], mesh['primitives']):
                attrs = primitive['attributes']
                for gltf, native in [('POSITION','Position'), ('NORMAL','Normal'),
                                      ('_CIV5_TEXCOORD0','TextureCoordinates0'), ('_CIV5_BINORMAL','Binormal')]:
                    np.testing.assert_array_equal(acc(attrs[gltf]), part['arrays'][native])
                np.testing.assert_array_equal(acc(attrs['TEXCOORD_0']), part['arrays']['TextureCoordinates0'][:, :2])
                np.testing.assert_array_equal(acc(attrs['TANGENT'])[:, :3], part['arrays']['Tangent'])
                ix = part['indices'][group['TriFirst']*3:(group['TriFirst']+group['TriCount'])*3]
                np.testing.assert_array_equal(acc(primitive['indices']), ix)
        checked.append({'name': name, 'native_vertices': record['vertices'], 'native_triangles': record['triangles'],
                        'gr2_graph_parity': True, 'glb_vertex_uv_index_transform_parity': True})
    return {'checks': checked, 'engine_validation': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    result = validate(args.output)
    (args.output/'native-import-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
