#!/usr/bin/env python3
"""Add irrigation to the real resource-free Farm1/2/3 assets for local testing.

Stock fields remain the responsibility of the FARM layout handler. This builder
never invents crop parcels or replaces farm_types.xml. Proprietary source-derived
candidates stay in the ignored local output, outside every release source root.
"""
from pathlib import Path
import argparse
import copy
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from native_gr2 import Reader
from gr2_writer import Writer
from native_scene import (parts, selected_models, regular_farm_states, transform,
                          diffuse, world_arrays, write_glb, review_glb)
from import_native_farms import OUT, digest
from audit_native_layout import audit
from build_native_fit import replace_texture_refs
from build_overlays import Mesh, curve, channel, unit, export, make_atlas
from irrigation_mesh_io import render_glb
from model_io_v2 import save_dds_mips

ART = 'ART_DEF_IMPROVEMENT_RT_IF_REGULAR_CANDIDATE'
DIFF = 'RT_IF_Regular_Diff.dds'
SREF = 'RT_IF_Regular_SREF.dds'


def constructed(root):
    return selected_models(root, regular_farm_states(root)['constructed'])


def building(root):
    model = constructed(root)['Models'][0]
    matches = [b['Mesh'] for b in model['MeshBindings']
               if all(m['Material']['ExtendedData']['ShaderSet'] == 'BuildingShader'
                      for m in b['Mesh']['MaterialBindings'])]
    if len(matches) != 1:
        raise ValueError('Expected one inspected regular farm building mesh')
    return model, matches[0]


def irrigation(scene, name, wet=True):
    # Route around the stock farmstead, never through its buildings. Actual crop
    # parcel fitting requires the engine's FARM output and is not inferred here.
    decals = [p for p in scene if 'Deca' in p['name']]
    if len(decals) != 1:
        raise ValueError('Expected one stock farmstead decal')
    z = float(world_arrays(decals[0])[0][:, 2].max()) + .32
    main = curve([(-18, 11.6, z), (-12.6, 11.1, z-.01),
                  (-4, 11.8, z-.03), (6, 11.3, z-.05), (17, 10.9, z-.07)])
    join = main[5]
    branch = curve([join, (-13, 5, join[2]-.015), (-12.5, -3, join[2]-.035),
                    (-13.1, -11, join[2]-.055)])
    mesh = Mesh(name)
    channel(mesh, main, 'regular_carrier', width=.90, wet=wet, bank_scale=3.,
            profile_scale=2.2, bank_material='coping', gaps=((join, branch[1]-join),))
    channel(mesh, branch, 'regular_branch', width=.70, wet=wet, bank_scale=2.6,
            profile_scale=2.2, bank_material='coping', upstream='regular_carrier', start_clearance=.65)
    mesh.meta = {'category': 'regular_farm_candidate', 'wet': wet,
                 'source_socket': main[0].tolist(), 'source_socket_connected': False,
                 'parcel_fit_verified': False, 'native_engine_test': False,
                 'scope': 'Regular farmstead irrigation fitting; surrounding native crops supplied by FARM in game.'}
    return mesh


def enhance(source, mesh):
    """Append a material group to the constructed mesh; retain all stock states.

    New vertices use the existing model's local transform and rigid bone. No new
    model/state names are introduced, and stock vertices/UVs/indices stay intact.
    """
    root = copy.deepcopy(source)
    model, target = building(root)
    material = copy.deepcopy(target['MaterialBindings'][0]['Material'])
    material['Name'] = 'RT_IF_RegularIrrigation'
    refs = {}
    for item in material['Maps']:
        texture = item['Map'].get('Texture')
        if texture:
            name = texture['FromFileName'].replace('\\', '/').rsplit('/', 1)[-1].lower()
            if item['Usage'] == 'Diffuse': refs[name] = DIFF
            elif item['Usage'] == 'BuildingSREF': refs[name] = SREF
            else: raise ValueError('Unreviewed native building texture usage')
    replace_texture_refs(material, refs)
    root['Materials'].append(material)
    material_index = len(target['MaterialBindings'])
    target['MaterialBindings'].append(dict(target['MaterialBindings'][0], Material=material))
    vertices = target['PrimaryVertexData']['Vertices']
    template = vertices[0]; first_vertex = len(vertices)
    placement = transform(model['InitialPlacement'])
    inv = np.linalg.inv(placement)
    for positions, normal, uvs, _, _ in mesh.faces:
        positions = positions @ inv[:3, :3].T + inv[:3, 3]
        normal = unit(normal @ placement[:3, :3])
        uvs = uvs.copy(); uvs[:, 1] = 1-uvs[:, 1]
        e1, e2 = positions[1]-positions[0], positions[2]-positions[0]
        d1, d2 = uvs[1]-uvs[0], uvs[2]-uvs[0]
        det = d1[0]*d2[1]-d1[1]*d2[0]
        if abs(det) < 1e-12: raise ValueError('Degenerate irrigation UV triangle')
        tangent = unit((e1*d2[1]-e2*d1[1])/det)
        binormal = unit((-e1*d2[0]+e2*d1[0])/det)
        for point, uv in zip(positions, uvs):
            vertices.append(dict(template, Position=point.tolist(), Normal=normal.tolist(),
                                 Tangent=tangent.tolist(), Binormal=binormal.tolist(),
                                 TextureCoordinates0=[*uv.tolist(), 0.]))
    top = target['PrimaryTopology']
    if top['Indices'] or len(vertices) > 65535:
        raise ValueError('Regular candidate requires 16-bit native topology')
    first_triangle = len(top['Indices16'])//3
    top['Indices16'] += [dict(top['Indices16'][0], Int16=i) for i in range(first_vertex, len(vertices))]
    top['Groups'].append(dict(top['Groups'][0], MaterialIndex=material_index,
                              TriFirst=first_triangle, TriCount=len(mesh.faces)))
    return root


def candidate_wrapper(source, output, name):
    root = ET.parse(source).getroot()
    root.find('Mesh').set('file', name+'.gr2')
    for texture in (DIFF, SREF): ET.SubElement(root, 'Texture', file=texture)
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(output/(name+'.fxsxml'), encoding='utf-8', xml_declaration=True)


def art_definitions(report, output):
    root = ET.Element('GameData')
    types = ET.SubElement(root, 'ArtDefine_LandmarkTypes')
    row = ET.SubElement(types, 'Row')
    for k,v in dict(Type=ART, LandmarkType='Improvement', FriendlyName='Regular irrigated farm candidate').items():
        ET.SubElement(row,k).text=v
    rows = ET.SubElement(root, 'ArtDefine_Landmarks')
    for original in report['ordinary_farm_rows']:
        if original['ResourceType'] != 'ART_DEF_RESOURCE_NONE': continue
        name = Path(original['FXSXML']).stem.lower()
        row = ET.SubElement(rows, 'Row')
        for k,v in dict(Era=original['Era'], State=original['State'], Scale=original['fScale'],
                        ImprovementType=ART, LayoutHandler=original['LayoutHandler'],
                        ResourceType=original['ResourceType'], Model='RT_IF_'+name+'.fxsxml',
                        TerrainContour='1' if original['bTerrainContour']=='True' else '0').items():
            ET.SubElement(row,k).text=v
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(output/'RT_IF_RegularCandidate.xml', encoding='utf-8', xml_declaration=True)


def build(out, quick=False):
    manifest = json.loads((out/'native-import.json').read_text())
    folder = out/'regular-farm-review'; folder.mkdir(exist_ok=True)
    cache = out/'native-local'; make_atlas(folder)
    save_dds_mips(Image.open(folder/'RT_IF_Diffuse.png'), folder/DIFF)
    save_dds_mips(Image.new('RGB', (64,64), (0,0,0)), folder/SREF)
    for name in (DIFF,SREF): (cache/name.lower()).write_bytes((folder/name).read_bytes())
    records=[]; views=[]
    regular = [r for r in manifest['models'] if r.get('construction_states')]
    if len(regular)!=6: raise ValueError('Re-run native import to obtain all regular variants')
    texture_names = sorted({diffuse(m) for rec in regular
                            for p in parts(constructed(Reader(out/rec['name']/(rec['name']+'-uncompressed.gr2')).root()))
                            for m in p['materials']} | {DIFF.lower()})
    for rec in regular:
        name=rec['name']; reader=Reader(out/name/(name+'-uncompressed.gr2')); source=reader.root()
        scene=parts(constructed(source))
        for wet in (True,False):
            target='RT_IF_'+name+('' if wet else '_Dry')
            mesh=irrigation(scene,target,wet); record=export(mesh,folder)
            candidate=enhance(source,mesh); path=folder/(target+'.gr2'); Writer(reader).write(path,candidate)
            actual=Reader(path).root()
            # Check visible float32 arrays here; the validator checks the full stock graph.
            for expected,readback in zip(parts(constructed(candidate)),parts(constructed(actual))):
                for key in expected['arrays']:
                    np.testing.assert_array_equal(expected['arrays'][key],readback['arrays'][key])
            candidate_wrapper(cache/(name+'.fxsxml'),folder,target)
            native_scene=parts(constructed(actual))
            write_glb(native_scene,cache,folder/(target+'.glb'))
            record.update(source=name, source_sha256=rec['source_sha256'], candidate_sha256=digest(path),
                          constructed_model=rec['preview_model_names'][0], construction_states=rec['construction_states'])
            records.append(record)
            if wet:
                review=folder/(target+'-review.glb')
                review_glb(native_scene,cache,review,texture_names=texture_names,cell=1024,columns=4)
                views.append((rec,record,native_scene))
                if not quick and name in ('medieval_farm1','modern_farm1'):
                    render_glb(review,1100,760,azimuth=55,elevation=65,shadow_bias=.12).save(folder/(name+'-preview.png'))
                    render_glb(review,300,210,azimuth=55,elevation=65,shadow_bias=.12).save(folder/(name+'-distance.png'))
    art_definitions(audit(out),folder)
    result={'native_engine_test':False,'redistributable':False,'models':records,
            'crop_policy':'Use stock FARM handler, farm_types.xml and textures; no crop override or authored parcel replacement.',
            'source_socket_policy':'Local candidates have an open upstream socket; runtime source/neighbor connection remains pending.'}
    (folder/'regular-farms.json').write_text(json.dumps(result,indent=2)+'\n')
    from regular_farm_viewer import build_viewer
    build_viewer(folder,views)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--quick',action='store_true')
    args=parser.parse_args()
    result=build(args.output.resolve(),args.quick)
    print(json.dumps({'candidates':len(result['models']),'folder':str(args.output/'regular-farm-review'),'native_engine_test':False}))
