#!/usr/bin/env python3
"""Validate exported terrain-case meshes, hydraulic joins and native preservation."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from native_gr2 import Reader
from build_regular_farms import constructed
from native_scene import parts, world_arrays
from build_native_fit import Surface
from import_native_farms import OUT
from validate_native_import import glb

EXPECTED = {'terrace', 'flat_desert', 'flat_grassland', 'floodplain',
            'terrace_flat', 'floodplain_desert', 'mountain_terrace'}


def exported_scene(path):
    doc, acc = glb(path)
    scene = []
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        mesh = doc['meshes'][node['mesh']]
        for primitive in mesh['primitives']:
            attrs = primitive['attributes']
            scene.append({'name': mesh['name'], 'arrays': {
                'Position': acc(attrs['POSITION']), 'Normal': acc(attrs['NORMAL']),
                'TextureCoordinates0': acc(attrs['_CIV5_TEXCOORD0'])},
                'indices': acc(primitive['indices']),
                'transform': np.array(node['matrix']).reshape(4, 4).T})
    return scene


def validate(output):
    folder = output/'terrain-review'
    manifest = json.loads((folder/'terrain-cases.json').read_text())
    assert {c['key'] for c in manifest['cases']} == EXPECTED
    assert not manifest['native_engine_test']
    assert manifest['prominence']['terrace_water_width'] >= 2*manifest['prominence']['previous_terrace_water_width']
    for record in manifest['source_assets']:
        assert hashlib.sha256((output/'native-local'/record['entry']).read_bytes()).hexdigest() == record['sha256']
    native = parts(Reader(output/'incan_terrace_farm/incan_terrace_farm-uncompressed.gr2').root())
    props = parts(constructed(Reader(output/'medieval_farm1/medieval_farm1-uncompressed.gr2').root()))
    # The default review must show actual native source, with no authored hill
    # or crop polygons silently included in the supposed original comparison.
    html = (folder/'index.html').read_text()
    cards = json.loads(html.split('const ASSETS=',1)[1].split(';\nconst ATLAS=',1)[0])
    assert [c['name'] for c in cards[:3]] == ['native_source','native_added','additions_only']
    source = cards[0]
    assert {g['name'] for g in source['groups']} == {p['name'] for p in native}
    source_positions = np.frombuffer(base64.b64decode(source['data']),dtype='<f4').reshape(-1,8)[:,:3]
    original_positions = np.concatenate([world_arrays(p)[0][p['indices']] for p in native])
    np.testing.assert_allclose(source_positions, original_positions, atol=2e-6)
    source_combined = exported_scene(folder/'terrace-source-with-irrigation.glb')
    assert len(source_combined) == len(native)+1
    for original, exported in zip(native,source_combined):
        for attr in ('Position','Normal','TextureCoordinates0'):
            np.testing.assert_array_equal(original['arrays'][attr],exported['arrays'][attr])
        np.testing.assert_array_equal(original['indices'],exported['indices'])
        np.testing.assert_array_equal(original['transform'],exported['transform'])
    originals = {p['name']: p for p in native+props}
    reports = []
    for case in manifest['cases']:
        scene = exported_scene(folder/(case['key']+'-combined.glb'))
        context = scene[:-1]
        preserved = 0
        for p in context:
            match = originals.get(p['name'].removeprefix('native_flat_'))
            if match is None:
                continue
            for attr in ('Position', 'Normal', 'TextureCoordinates0'):
                np.testing.assert_array_equal(p['arrays'][attr], match['arrays'][attr])
            np.testing.assert_array_equal(p['indices'], match['indices'])
            np.testing.assert_array_equal(p['transform'][:3, :3], match['transform'][:3, :3])
            if not p['name'].startswith('native_flat_'):
                np.testing.assert_array_equal(p['transform'], match['transform'])
            preserved += 1
        assert preserved
        # Water in the reference river is a source, not a solid obstacle.
        solid = [p for p in context if p['name'] != 'native_river_source']
        surface = Surface(solid)
        source_cavity = Surface([p for p in solid if p['name'] != 'authored_rocky_source_terrain'])
        for record in (case['record'], case['dry_record']):
            name = record['name']; dry = name.endswith('_Dry')
            part, = parts(Reader(folder/(name+'.gr2')).root())
            a = part['arrays']; p = a['Position']; ix = part['indices']
            assert all(np.isfinite(v).all() for v in a.values())
            np.testing.assert_array_equal(ix, np.arange(len(p)))
            np.testing.assert_allclose(np.linalg.norm(a['Normal'], axis=1), 1, atol=1e-6)
            tri = p.reshape(-1, 3, 3)
            cross = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
            assert np.linalg.norm(cross, axis=1).min() > 1e-8
            assert (np.sum(cross*a['Normal'][::3], axis=1) > 0).all()
            t = a['TextureCoordinates0'][:, :2].reshape(-1, 3, 2)
            du, dv = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]
            assert np.abs(du[:, 0]*dv[:, 1]-du[:, 1]*dv[:, 0]).min() > 1e-12
            exported, = exported_scene(folder/(name+'.glb'))
            for attr in ('Position', 'Normal', 'TextureCoordinates0'):
                np.testing.assert_array_equal(exported['arrays'][attr], a[attr])
            assert record['triangles'] == len(tri)
            assert sum(g['count'] for g in record['groups']) == len(p)
            assert not any('crop' in g['name'] or 'terrain' in g['name'] for g in record['groups'])
            for item in ET.parse(folder/(name+'.fxsxml')).getroot():
                assert (folder/item.attrib['file']).is_file()
            routes = {r['name']: r for r in record['routes']}
            roots = {r['route'] for r in record['external_inputs']}
            assert len(roots) == 1
            assert roots == {r['name'] for r in routes.values() if not r.get('upstream')}
            for route in routes.values():
                points = np.array(route['points'])
                assert (np.diff(points[:, 2]) <= 1e-8).all(), (name, route['name'], 'uphill')
                seen = set(); current = route
                while current.get('upstream'):
                    assert current['name'] not in seen, 'Hydraulic cycle'
                    seen.add(current['name']); current = routes[current['upstream']]
                assert current['name'] in roots
                if route.get('upstream'):
                    upstream = np.array(routes[route['upstream']]['points'])
                    assert np.linalg.norm(upstream-points[0], axis=1).min() < 1e-6, (name, route['name'], 'disconnected')
                if route['end'] == 'closed_field_outlet':
                    group, = [g for g in record['groups'] if g['name'] == route['name']+'_terminal']
                    cap = p[group['first']:group['first']+group['count']]
                    assert len(cap) >= 9 and cap[:, 2].min() < points[-1, 2] < cap[:, 2].max()
            for seam in record['shared_ports']:
                source, target = routes[seam['from']], routes[seam['to']]
                np.testing.assert_allclose(source['points'][-1], seam['point'], atol=1e-7)
                np.testing.assert_allclose(target['points'][0], seam['point'], atol=1e-7)
                sw = source.get('widths', [source['width']])[-1]
                tw = target.get('widths', [target['width']])[0]
                assert abs(sw-tw) < 1e-8 and source['end'] == 'open_joint'
            water = [g for g in record['groups'] if g['name'].endswith('_water')]
            assert bool(water) != dry
            gaps, outside, cavity_samples = [], 0, 0
            # Independent barycentric samples from actual GR2 triangles. Includes
            # both water edges; centerline-only tests miss terrain intersections.
            for group in water:
                for triangle in p[group['first']:group['first']+group['count']].reshape(-1, 3, 3):
                    for i in range(5):
                        for j in range(5-i):
                            sample = (triangle[0]*i+triangle[1]*j+triangle[2]*(4-i-j))/4
                            target = source_cavity if group['name'] == 'mountain_intake_water_water' else surface
                            try:
                                ground = target.height(*sample[:2])
                            except ValueError:
                                ground = 0.; outside += 1
                            gap = float(sample[2]-ground)
                            assert gap >= .025, (name, group['name'], sample.tolist(), gap)
                            if group['name'] == 'mountain_intake_water_water':
                                cavity_samples += 1
                            gaps.append(gap)
            reports.append({'name': name, 'triangles': len(tri), 'native_parts_preserved': preserved,
                            'routes': len(routes), 'water_samples': len(gaps),
                            'minimum_water_clearance': min(gaps) if gaps else None,
                            'outside_fixture_samples': outside, 'concealed_intake_samples': cavity_samples,
                            'shared_ports': len(record['shared_ports'])})
    return {'result': 'PASS', 'cases': len(EXPECTED), 'models': reports,
            'native_geometry_uv_preservation': True, 'default_comparison_excludes_authored_terrain_and_parcels': True, 'gr2_glb_parity': True,
            'gravity_and_source_connectivity': True, 'engine_validation': False,
            'scope': 'Authored fixture terrain; concealed mountain intake excluded from rock clearance only.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    result = validate(args.output.resolve())
    (args.output/'terrain-review/validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
