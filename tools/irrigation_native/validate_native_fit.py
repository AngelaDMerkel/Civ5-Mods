#!/usr/bin/env python3
"""Check fitted GR2/GLB geometry, source preservation, water and native wrappers."""
from pathlib import Path
import argparse
import json
import struct
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from native_gr2 import Reader
from native_scene import parts
from import_native_farms import OUT
from validate_native_import import glb
from build_native_fit import Surface, verify_fit


def validate(output):
    base = parts(Reader(output/'incan_terrace_farm/incan_terrace_farm-uncompressed.gr2').root())
    surface = Surface(base); folder = output/'irrigation-fit'
    combined, acc = glb(folder/'native-terrace-with-irrigation.glb')
    # The combined editable file must retain every native vertex and UV verbatim.
    assert len(combined['meshes']) == len(base)+1
    for part, mesh, node in zip(base, combined['meshes'], combined['nodes']):
        assert part['name'] == mesh['name']
        np.testing.assert_array_equal(acc(mesh['primitives'][0]['attributes']['POSITION']), part['arrays']['Position'])
        np.testing.assert_array_equal(acc(mesh['primitives'][0]['attributes']['_CIV5_TEXCOORD0']), part['arrays']['TextureCoordinates0'])
        np.testing.assert_array_equal(acc(mesh['primitives'][0]['indices']), part['indices'])
        np.testing.assert_allclose(np.array(node['matrix']).reshape(4, 4).T, part['transform'], atol=1e-7)
    reports = []
    for suffix in ('', '_Dry'):
        name = 'RT_IF_Terrace_NativeFit'+suffix
        source = Reader(folder/(name+'.gr2')).root(); scene = parts(source)
        assert len(scene) == 1 and scene[0]['name'] == name
        part = scene[0]; a = part['arrays']; p = a['Position']; ix = part['indices']
        assert all(np.isfinite(values).all() for values in a.values())
        assert len(ix) == len(p) and len(ix) % 3 == 0
        np.testing.assert_array_equal(ix, np.arange(len(p)))
        np.testing.assert_allclose(np.linalg.norm(a['Normal'], axis=1), 1, atol=1e-6)
        triangles = p.reshape(-1, 3, 3)
        areas = np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]), axis=1)
        assert areas.min() > 1e-8
        doc, exported = glb(folder/(name+'-native.glb'))
        attrs = doc['meshes'][0]['primitives'][0]['attributes']
        np.testing.assert_array_equal(exported(attrs['POSITION']), p)
        np.testing.assert_array_equal(exported(attrs['_CIV5_TEXCOORD0']), a['TextureCoordinates0'])
        record = json.loads((folder/name/(name+'.json')).read_text())
        assert record['triangles'] == len(triangles)
        assert sum(g['count'] for g in record['groups']) == len(p)
        assert any(g['name'] == 'native_upper_header_terminal' for g in record['groups'])
        proxy = type('Routes', (), {'routes': record['routes']})()
        flow = verify_fit(proxy, surface)
        water = [g for g in record['groups'] if g['name'].endswith('_water')]
        assert bool(water) == (not suffix)
        samples = []
        for group in water:
            for tri in p[group['first']:group['first']+group['count']].reshape(-1, 3, 3):
                for sample in [*tri, tri.mean(axis=0)]:
                    gap = float(sample[2]-surface.height(*sample[:2]))
                    assert gap >= .07, (name, sample, gap)
                    samples.append(gap)
        for item in ET.parse(folder/(name+'.fxsxml')).getroot():
            assert (folder/item.attrib['file']).is_file()
        reports.append({'name': name, 'triangles': len(triangles), 'gr2_glb_parity': True,
                        'closed_outlet_geometry': True, 'route_checks': flow,
                        'actual_exported_water_samples': len(samples),
                        'actual_exported_water_clearance_min': min(samples) if samples else None})
    for name, size in [('RT_IF_Native_Diff.dds', 2048), ('RT_IF_Native_SREF.dds', 64)]:
        path = folder/name; raw = path.read_bytes()
        assert raw[:4] == b'DDS ' and raw[84:88] == b'DXT1'
        assert struct.unpack_from('<I', raw, 28)[0] == int(np.log2(size))+1
        expected = 128+sum(max(1, (size//(2**i)+3)//4)**2*8 for i in range(int(np.log2(size))+1))
        assert len(raw) == expected
        assert Image.open(path).size == (size, size)
    return {'native_source_vertices_uvs_indices_transforms_unchanged': True,
            'dds_mipchains_and_fxsxml_references': True, 'models': reports,
            'engine_validation': False, 'flat_farm_overlay': 'not implemented; native crop-decal placement still requires engine work'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args(); result = validate(args.output)
    (args.output/'irrigation-fit/native-export-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
