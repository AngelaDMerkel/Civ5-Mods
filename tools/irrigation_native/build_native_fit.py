#!/usr/bin/env python3
"""Fit original irrigation geometry to the decoded native Terrace Farm mesh."""
from pathlib import Path
import argparse
import base64
import copy
import json
import math
import sys
import numpy as np
from PIL import Image
from native_gr2 import Reader
from gr2_writer import Writer
from native_scene import parts, world_arrays, write_glb, review_glb
from import_native_farms import OUT
from build_overlays import channel, Mesh, original, make_atlas, export, unit
from irrigation_mesh_io import render_glb, read_glb
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model_io_v2 import save_dds_mips

IDENTITY = [0, 0., 0., 0., 0., 0., 0., 1., 1., 0., 0., 0., 1., 0., 0., 0., 1.]


class Surface:
    def __init__(self, scene):
        self.triangles = np.concatenate([world_arrays(p)[0][p['indices']].reshape(-1, 3, 3) for p in scene])
        t = self.triangles
        self.det = (t[:, 1, 1]-t[:, 2, 1])*(t[:, 0, 0]-t[:, 2, 0])+(t[:, 2, 0]-t[:, 1, 0])*(t[:, 0, 1]-t[:, 2, 1])
        self.valid = abs(self.det) > 1e-7

    def height(self, x, y):
        t = self.triangles[self.valid]; den = self.det[self.valid]
        a = ((t[:, 1, 1]-t[:, 2, 1])*(x-t[:, 2, 0])+(t[:, 2, 0]-t[:, 1, 0])*(y-t[:, 2, 1]))/den
        b = ((t[:, 2, 1]-t[:, 0, 1])*(x-t[:, 2, 0])+(t[:, 0, 0]-t[:, 2, 0])*(y-t[:, 2, 1]))/den
        c = 1-a-b; hit = (a >= -1e-7) & (b >= -1e-7) & (c >= -1e-7)
        if not hit.any():
            raise ValueError(f'No native surface at {x:.3f}, {y:.3f}')
        return float(np.max((a*t[:, 0, 2]+b*t[:, 1, 2]+c*t[:, 2, 2])[hit]))


def subdivide(points, spacing=1.0):
    result = []
    for a, b in zip(points, points[1:]):
        count = max(1, math.ceil(np.linalg.norm(np.array(a)[:2]-np.array(b)[:2])/spacing))
        result.extend(np.linspace(a, b, count, endpoint=False))
    return np.array(result+[points[-1]])


def fitted_mesh(surface, wet=True):
    mesh = Mesh('RT_IF_Terrace_NativeFit'+('' if wet else '_Dry'))
    # Measured midpoints of the existing upper retaining-wall caps in native
    # Incan_Farm06 and Incan_Farm07; no replacement parcel geometry or crop UVs.
    header = subdivide([(3.7, 11.56, 14.78), (-5.82, 11.56, 14.765),
                        (-12.61, 6.73, 14.75), (-14.03, 3.52, 14.735)])
    channel(mesh, header, 'native_upper_header', width=.44, wet=wet, stone=True,
            upstream='native_supply_aqueduct')
    # Reuse the existing aqueduct builder, uniformly scaled to the native cap
    # width. Only pier feet sample native geometry; the waterline is one grade.
    scale = 2.2
    bridge = Mesh('native_bridge')
    start = np.array((10.25, 23.30, 14.95)); end = header[0]
    original.bridge(bridge, start/scale, end/scale,
                    ground=lambda x, y: surface.height(x*scale, y*scale)/scale,
                    wet=wet, part='native_supply_aqueduct')
    for p, n, uv, mat, name in bridge.faces:
        mesh.faces.append((p*scale, n, uv, mat, name))
    for route in bridge.routes:
        mesh.routes.append(dict(route, points=(np.array(route['points'])*scale).tolist(),
                                width=route['width']*scale, upstream=None, end='header_joint'))
    mesh.meta = {'category': 'native_fit', 'source': 'incan_terrace_farm.gr2',
                 'native_authoring_units': True, 'native_game_validation': False,
                 'terrain_fit_scope': 'constructed terrace source mesh only; engine deformation excluded',
                 'open_source_socket': start.tolist(), 'closed_exposed_outlet': header[-1].tolist(),
                 'base_geometry_changed': False, 'original_bridge_uniform_scale': scale}
    return mesh


def replace_texture_refs(value, replacements):
    if isinstance(value, dict):
        for k, v in value.items():
            if not k.startswith('_'):
                value[k] = replace_texture_refs(v, replacements)
    elif isinstance(value, list):
        return [replace_texture_refs(v, replacements) for v in value]
    elif isinstance(value, str):
        name = value.replace('\\', '/').rsplit('/', 1)[-1].lower()
        return replacements.get(name, value)
    return value


def overlay_graph(source, mesh):
    """Use the native rigid schema/material setup with only original overlay vertices."""
    model = copy.deepcopy(next(m for m in source['Models'] if m['Name'] == 'Incan_Farm06'))
    model['Name'] = mesh.name; model['InitialPlacement'] = IDENTITY.copy()
    skeleton = model['Skeleton']; skeleton['Name'] = mesh.name
    for bone in skeleton['Bones']:
        bone['Name'] = mesh.name; bone['Transform'] = IDENTITY.copy()
        bone['InverseWorldTransform'] = np.eye(4).flatten().tolist()
    target = model['MeshBindings'][0]['Mesh']; target['Name'] = mesh.name
    for b in target['BoneBindings']:
        b['BoneName'] = mesh.name
    material = target['MaterialBindings'][0]['Material']; material['Name'] = 'RT_IF_NativeIrrigation'
    replace_texture_refs(material, {'incan_terrace_diff.dds': 'RT_IF_Native_Diff.dds',
                                    'incan_terrace_sref.dds': 'RT_IF_Native_SREF.dds'})
    vd = target['PrimaryVertexData']; template = vd['Vertices'][0]; vertices = []
    for positions, normal, uvs, _, _ in mesh.faces:
        uvs = uvs.copy(); uvs[:, 1] = 1-uvs[:, 1]
        e1, e2 = positions[1]-positions[0], positions[2]-positions[0]
        d1, d2 = uvs[1]-uvs[0], uvs[2]-uvs[0]
        det = d1[0]*d2[1]-d1[1]*d2[0]
        if abs(det) < 1e-12:
            raise ValueError('Degenerate irrigation UV triangle')
        tangent = unit((e1*d2[1]-e2*d1[1])/det)
        binormal = unit((-e1*d2[0]+e2*d1[0])/det)
        for p, uv in zip(positions, uvs):
            vertices.append(dict(template, Position=p.tolist(), Normal=normal.tolist(),
                                 Tangent=tangent.tolist(), Binormal=binormal.tolist(),
                                 TextureCoordinates0=[*uv.tolist(), 0.]))
    vd['Vertices'] = vertices
    top = target['PrimaryTopology']; group = dict(top['Groups'][0], MaterialIndex=0, TriFirst=0, TriCount=len(mesh.faces))
    top['Groups'] = [group]
    it = top['Indices16'][0]
    if len(vertices) > 65535:
        raise ValueError('Overlay exceeds 16-bit native topology')
    top['Indices16'] = [dict(it, Int16=i) for i in range(len(vertices))]
    root = dict(source, FromFileName=mesh.name+'.obj', Textures=[], Materials=[material], Skeletons=[skeleton],
                VertexDatas=[vd], TriTopologies=[top], Meshes=[target], Models=[model], TrackGroups=[], Animations=[])
    return root


def verify_fit(mesh, surface):
    clearances = []
    for route in mesh.routes:
        points = np.array(route['points'])
        if (np.diff(points[:, 2]) > 1e-7).any():
            raise ValueError('Uphill water')
        for a, b in zip(points, points[1:]):
            delta = b-a; side = unit((-delta[1], delta[0], 0))
            for p in np.linspace(a, b, max(3, math.ceil(np.linalg.norm(delta)/.1))):
                for across in (-.5, 0, .5):
                    sample = p+side*route['width']*across
                    gap = sample[2]-surface.height(*sample[:2])
                    if gap < .07:
                        raise ValueError(f'Water intersects native geometry: {route["name"]}, {sample}, clearance {gap}')
                    if route['name'] == 'native_upper_header' and gap > .4:
                        raise ValueError('Header leaves native wall cap')
                    clearances.append(gap)
    routes = {r['name']: r for r in mesh.routes}
    np.testing.assert_allclose(routes['native_supply_aqueduct']['points'][-1], routes['native_upper_header']['points'][0])
    assert routes['native_upper_header']['end'] == 'closed_field_outlet'
    return {'sampled_water_clearance_min': min(clearances), 'sampled_water_clearance_max': max(clearances),
            'water_samples': len(clearances), 'gravity_and_connection': True, 'native_engine_test': False}



def build_viewer(folder, review, native, overlay):
    doc, (p, n, uv), blob = read_glb(review)
    base_count = sum(len(item['indices']) for item in native)
    data = np.column_stack((p, n, uv)).astype('<f4')
    base_groups = [{'name': 'native_fields', 'first': 0, 'count': base_count}]
    overlay_groups = overlay['groups']
    specs = [
        ('combined', 'Native terrace + fitted irrigation', data,
         base_groups+[dict(g, first=g['first']+base_count) for g in overlay_groups],
         {'glb': 'native-terrace-with-irrigation.glb'}),
        ('source', 'Original Civ V Terrace Farm', data[:base_count], base_groups,
         {'glb': '../incan_terrace_farm/incan_terrace_farm.glb'}),
        ('overlay', 'Irrigation additions only', data[base_count:], overlay_groups,
         {'glb': overlay['name']+'-native.glb', 'obj': overlay['name']+'/'+overlay['name']+'.obj',
          'br2': overlay['name']+'/'+overlay['name']+'.br2', 'gr2': overlay['name']+'.gr2'})]
    cards = []
    for name, label, a, groups, files in specs:
        cards.append({'name': name, 'label': label, 'category': 'native mesh inspection',
                      'triangles': len(a)//3, 'bounds': [a[:, :3].min(0).tolist(), a[:, :3].max(0).tolist()],
                      'groups': groups, 'files': files, 'data': base64.b64encode(a.tobytes()).decode()})
    image = doc['bufferViews'][doc['images'][0]['bufferView']]
    png = blob[image['byteOffset']:image['byteOffset']+image['byteLength']]
    html = (Path(__file__).resolve().parent.parent/'irrigation_v3/irrigation_viewer.html').read_text()
    html = html.replace('__ASSET_DATA__', json.dumps(cards, separators=(',', ':')))
    html = html.replace('__ATLAS_DATA__', 'data:image/png;base64,'+base64.b64encode(png).decode())
    html = html.replace('Irrigated Farm — Mesh Studio', 'Civ V native farm — mesh fitting')
    html = html.replace('Original source meshes', 'Actual native mesh + original irrigation')
    html = html.replace('Irrigated farm · v3', 'Native farm · first fitting')
    html = html.replace('one atlas material', 'local inspection atlas')
    html = html.replace('Source kit only. Native GR2 conversion, terrain fitting and game placement remain pending.',
                        'Native source mesh fitted; experimental GR2 exported. Engine loading and terrain deformation remain untested. Tall wall skirts belong to the native mesh and are normally hidden by game terrain.')
    html = html.replace('Z-up source · 2048² original atlas · No external dependencies',
                        'Native geometry and crop UVs retained · Local source preview, not an in-game capture')
    html = html.replace('>Vegetation</label>', '>Vegetation (no separate crop geometry)</label>')
    html = html.replace('<a id="br2">BR2</a>', '<a id="br2">BR2</a><a id="gr2">GR2*</a>')
    html = html.replace("for(const ext of ['glb','obj','br2']){by(ext).href=active.name+'/'+active.name+'.'+ext;by(ext).download=active.name+'.'+ext}",
                        "for(const ext of ['glb','obj','br2','gr2']){by(ext).style.display=active.files[ext]?'':'none';by(ext).href=active.files[ext]||'#';by(ext).download=(active.files[ext]||'').split('/').pop()}")
    (folder/'index.html').write_text(html)
    (folder/'TECHNICAL_NOTES.txt').write_text(
        'Actual native Terrace Farm source geometry, textures and UVs are retained.\n'
        'Native geometry is local reference material; do not redistribute this review folder.\n'
        'Only irrigation additions use original project geometry and painted materials.\n'
        'The channel follows measured upper wall caps in Incan_Farm06 and Incan_Farm07.\n'
        'The supply aqueduct has one descending grade; its piers sample actual native surfaces.\n'
        'The open high socket requires an upstream water source or matching connector.\n'
        'The header closes within the farm; most parcel seams stay dry.\n'
        'GR2* is an experimental native-format export, checked by readback, not by the game.\n'
        'No terrain deformation, source/neighbor selection, game integration or new design approval is claimed.\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args(); out = args.output.resolve()
    reader = Reader(out/'incan_terrace_farm/incan_terrace_farm-uncompressed.gr2')
    source = reader.root(); base = parts(source); surface = Surface(base)
    folder = out/'irrigation-fit'; folder.mkdir(exist_ok=True)
    make_atlas(folder)
    save_dds_mips(Image.open(folder/'RT_IF_Diffuse.png'), folder/'RT_IF_Native_Diff.dds')
    save_dds_mips(Image.new('RGB', (64, 64), (0, 0, 0)), folder/'RT_IF_Native_SREF.dds')
    # Only the local reference renderer needs native textures alongside originals.
    texture_dir = out/'native-local'
    for name in ('RT_IF_Native_Diff.dds', 'RT_IF_Native_SREF.dds'):
        (texture_dir/name.lower()).write_bytes((folder/name).read_bytes())
    results = []
    for wet in (True, False):
        mesh = fitted_mesh(surface, wet)
        result = verify_fit(mesh, surface)
        record = export(mesh, folder)
        obj = folder/mesh.name/(mesh.name+'.obj')
        obj.write_text(obj.read_text().replace('Normalized units, not engine-calibrated.',
                       'Native Terrace Farm authoring units; engine fitting not yet verified.'))
        graph = overlay_graph(source, mesh)
        path = folder/(mesh.name+'.gr2'); Writer(reader).write(path, graph)
        actual = Reader(path).root()
        # Float32 serialization is required; compare the exported mesh numerically.
        actual_scene = parts(actual); expected_scene = parts(graph)
        for a, b in zip(actual_scene, expected_scene):
            for key in a['arrays']:
                np.testing.assert_array_equal(a['arrays'][key], b['arrays'][key])
        write_glb(actual_scene, texture_dir, folder/(mesh.name+'-native.glb'))
        (folder/(mesh.name+'.fxsxml')).write_text('<?xml version="1.0" encoding="utf-8"?>\n<Asset>\n'
            f'  <Mesh file="{mesh.name}.gr2"/>\n  <Texture file="RT_IF_Native_Diff.dds"/>\n'
            '  <Texture file="RT_IF_Native_SREF.dds"/>\n</Asset>\n')
        result.update(name=mesh.name, triangles=record['triangles'], native_gr2_readback=True)
        results.append(result)
        if wet:
            combined = base+actual_scene
            write_glb(combined, texture_dir, folder/'native-terrace-with-irrigation.glb')
            native_review = folder/'native-terrace-with-irrigation-review.glb'
            review_glb(combined, texture_dir, native_review)
            build_viewer(folder, native_review, base, record)
            if not args.quick:
                render_glb(native_review, 1200, 900, azimuth=55, elevation=55).save(folder/'native-fit-preview.png')
                render_glb(native_review, 300, 225, azimuth=55, elevation=55).save(folder/'native-fit-distance.png')
    (folder/'fit-validation.json').write_text(json.dumps({'models': results, 'status': 'native-source fit; not yet engine-tested'}, indent=2)+'\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
