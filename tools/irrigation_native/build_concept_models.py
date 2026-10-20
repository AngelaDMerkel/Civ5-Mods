#!/usr/bin/env python3
"""Real mesh candidates for the selected concept; native-derived, local review only.

V3 supplies terrain/terraces and rigid spans. Native DDS pixels and regular Farm1
geometry are used only in ignored outputs, never a playable/source-art package.
"""
from pathlib import Path
import argparse
import base64
import copy
import hashlib
import io
import struct
import json
import math
import sys
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent/'irrigation_v3'))
import build_irrigation_meshes as v3
import natural_farms as natural
from irrigation_mesh_io import Mesh, NAMES, atlas_uv, export, read_glb, render_glb, unit
from build_overlays import channel, curve
from native_gr2 import Reader
from native_scene import parts, selected_models, regular_farm_states, world_arrays, review_glb
from gr2_writer import Writer
from build_native_fit import overlay_graph, replace_texture_refs
sys.path.insert(0, str(HERE.parent))
from model_io_v2 import save_dds_mips

OUT = ROOT/'output/models/irrigated-farm-native-fit'
SCALE = 30/v3.A  # Matches the existing native terrain fixture's 30-unit apothem.
MATERIALS = {
    'stone': ('incan_terrace_diff.dds', (.01,.01,.49,.34)),
    'coping': ('incan_terrace_diff.dds', (.01,.383,.49,.405)),
    'water': ('river_diffuse.dds', (0,0,1,1)),
    'soil': ('afri_desert_d.dds', (0,0,1,1)),
    'earth': ('afri_desert_d.dds', (0,0,1,1)),
    'rock': ('afri_mountain_base_d.dds', (0,0,1,1)),
    'barley': ('crops_africa_01_d.dds', (0,0,1,1)),
    'vegetables': ('crops_africa_07_d.dds', (0,0,1,1)),
    'legumes': ('crops_africa_04_d.dds', (0,0,1,1)),
    'stubble': ('crops_africa_02_d.dds', (0,0,1,1)),
    'dry_crop': ('crops_africa_06_d.dds', (0,0,1,1)),
    'plaster': ('ancient_farm_diff.dds', (0,0,1,1)),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_rgba_mips(image, path):
    """Uncompressed native DDS with full mip chain and preserved foliage alpha."""
    level=image.convert('RGBA');payload=[];header=None
    while True:
        stream=io.BytesIO();level.save(stream,format='DDS');raw=stream.getvalue()
        if header is None:header=bytearray(raw[:128])
        payload.append(raw[128:])
        if level.size==(1,1):break
        level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS)
    struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,28,len(payload))
    struct.pack_into('<I',header,108,0x1000|0x8|0x400000)
    path.write_bytes(header+b''.join(payload))


def pack_materials(cache, folder):
    """Pack unchanged source pixels; alpha in terrain DDS is blend data, not holes."""
    original = ROOT/'shared/art/irrigated-farm/mesh-v3-review/painted-atlas.png'
    atlas = Image.open(original).convert('RGBA').resize((2048,2048),Image.Resampling.LANCZOS)
    records = []
    for name, (file, rect) in MATERIALS.items():
        source = cache/file
        im = Image.open(source).convert('RGBA')
        im.putalpha(255)
        # No recolouring or repainted details. Native 256/512 pixels are packed
        # with nearest sampling; UV rectangles select masonry within its atlas.
        im = im.resize((512,512),Image.Resampling.NEAREST)
        i = NAMES.index(name); atlas.paste(im, ((i%4)*512,(i//4)*512))
        records.append({'material':name,'file':file,'sha256':digest(source),'uv_rectangle':rect})
    atlas.save(folder/'RT_IF_Diffuse.png')
    save_rgba_mips(atlas,folder/'RT_IF_Concept_Diff.dds')
    save_dds_mips(Image.new('RGB',(64,64),(0,0,0)),folder/'RT_IF_Concept_SREF.dds')
    return records


def remap(mesh):
    result = []
    for p,n,uv,mat,part in mesh.faces:
        if mat in MATERIALS:
            i=NAMES.index(mat); t=uv.copy(); t[:,1]=1-t[:,1]
            t=(t*4-[i%4,i//4]-16/512)/(1-32/512)
            if mat in ('stone','coping'):
                # The old masonry used repeating world coordinates. Keep each
                # triangle within a real masonry region of the native atlas.
                t-=np.floor(t.min(0)); t/=np.maximum(t.max(0),1)
            x0,y0,x1,y1=MATERIALS[mat][1]
            t=np.array([x0,y0])+t*[x1-x0,y1-y0]
            t=(t+[i%4,i//4])/4; t[:,1]=1-t[:,1]; uv=t
        result.append((p,n,uv,mat,part))
    mesh.faces=result


def farm_function(native_root):
    state=regular_farm_states(native_root)['constructed']
    candidates=parts(selected_models(native_root,state))
    building=next(p for p in candidates if all(m['ExtendedData']['ShaderSet']=='BuildingShader' for m in p['materials']))
    p,_=world_arrays(building); center=(p.min(0)+p.max(0))/2;center[2]=p[:,2].min()
    size=.115; p=(p-center)*size
    uv=building['arrays']['TextureCoordinates0'][:,:2]
    def place(mesh,x,y,z,state):
        if state in ('Construction','Pillaged'):return
        for indices in building['indices'].reshape(-1,3):
            tri=p[indices]+[x,y,z]; normal=unit(np.cross(tri[1]-tri[0],tri[2]-tri[0]))
            tex=uv[indices].copy();delta=tex[1:]-tex[0]
            if abs(np.linalg.det(delta))<1e-10:
                # Stock solid-colour caps collapse their UVs. A sub-texel offset
                # gives BR2 a defined tangent frame without changing the silhouette.
                tex[1,0]+=.0001;tex[2,1]+=.0001
            mesh.faces.append((tri,normal,atlas_uv(tex,'plaster'),'plaster','native_regular_farm'))
    return place


def sparse_network(mesh,kind,wet):
    if kind=='Flat':
        # Walk selected staggered parcel seams in the same world frame as v3.
        rotate=lambda p: natural.flat_rotate(np.asarray(p))
        main=curve([rotate(p) for p in [(-2.5,3.6,.14),(-2.4,2.4,.138),(-2.75,1.2,.135),(-2.65,0,.132),(-2.25,-1.2,.128),(-2.5,-2.4,.125),(-2.45,-3.6,.12)]],steps=4)
        branches=[]
        for index,end in [(4,(2.8,2.4,.131)),(12,(3.5,0,.125))]:
            start=main[index];finish=rotate(end)
            points=curve([start,(start+finish)/2+[0,.13,0],finish],steps=5)
            branches.append(points)
        channel(mesh,main,'flat_supply',width=.27,wet=wet,
                gaps=[(p[0],p[1]-p[0]) for p in branches],bank_material='stone',bank_scale=.35)
        for i,p in enumerate(branches):
            channel(mesh,p,f'flat_header_{i}',width=.20,wet=wet,upstream='flat_supply',start_clearance=.27,bank_material='stone',bank_scale=.35)
        return
    rings=natural.terrace_rings(kind);top=len(rings)-2;root=natural.inlet(kind)
    h=natural.header(kind,top);feed=[root,np.array((*h[0,:2],root[2]))+[.10,0,0],h[0]]
    natural.trough(mesh,feed,'mountain_receiver_drop',wet,.23)
    for k in range(top,-1,-1):
        arc=natural.header(kind,k);z=rings[k][1]
        spans=[i for i in range(len(arc)-1) if natural.gully(i,k)]
        parent='mountain_receiver_drop' if k==top else f'drop_{k+1}_{k}'
        natural.trough(mesh,arc,f'bench_{k}_contour',wet,.19,parent=parent,spans=spans)
        # Finish the exposed contour end within the plot; no cut-off open gutter.
        cap=Mesh('cap');cap.box((0,0,-.015),(.06,.19+2*v3.WALL_WIDTH,.14),'coping',f'bench_{k}_closed_end')
        angle=math.degrees(math.atan2(*(arc[-1]-arc[-2])[:2][::-1]))
        mesh.append(cap,arc[-1],angle)
        mesh.routes[-1]['end']='closed_field_outlet'
        for i in spans:
            v3.bridge(mesh,arc[i],arc[i+1],ground=lambda x,y:z-.32,wet=wet,lod=mesh.lod,part=f'bench_{k}_aqueduct_{i}')
            mesh.routes[-1]['upstream']=f'bench_{k}_contour'
        if k:
            lower=natural.header(kind,k-1)[0];edge=(rings[k][0][0]+rings[k][0][1])/2;center=rings[k][0].mean(0);u=unit(edge-center)
            drop=[arc[0],(*(edge-u*.10),arc[0,2]),(*(edge+u*.035),arc[0,2]),(*(edge+u*.12),lower[2]),lower]
            natural.trough(mesh,drop,f'drop_{k}_{k-1}',wet,.23,parent=f'bench_{k}_contour')


def export_native(mesh, record, folder, reader, source):
    scaled=copy.deepcopy(mesh)
    scaled.faces=[(p*SCALE,n,uv,mat,part) for p,n,uv,mat,part in mesh.faces]
    graph=overlay_graph(source,scaled)
    replace_texture_refs(graph,{'rt_if_native_diff.dds':'RT_IF_Concept_Diff.dds','rt_if_native_sref.dds':'RT_IF_Concept_SREF.dds'})
    target=graph['Meshes'][0]
    # Match smooth GLB terrain normals and orthogonal BR2 tangent frames.
    lines=(folder/mesh.name/(mesh.name+'.br2')).read_text().splitlines()
    rows=np.array([list(map(float,line.split())) for line in lines[lines.index('vertices')+1:lines.index('triangles')]])
    for vertex,row in zip(target['PrimaryVertexData']['Vertices'],rows):
        vertex.update(Normal=row[3:6].tolist(),Tangent=row[16:19].tolist(),Binormal=row[19:22].tolist())
    p=rows[:,:3]*SCALE
    for binding in target['BoneBindings']:
        if 'OBBMin' in binding:binding['OBBMin']=p.min(0).tolist()
        if 'OBBMax' in binding:binding['OBBMax']=p.max(0).tolist()
    path=folder/mesh.name/(mesh.name+'.gr2');Writer(reader).write(path,graph)
    actual=parts(Reader(path).root())[0]
    np.testing.assert_allclose(actual['arrays']['Position'],p,atol=3e-6)
    np.testing.assert_allclose(actual['arrays']['Normal'],rows[:,3:6],atol=2e-7)
    np.testing.assert_allclose(actual['arrays']['TextureCoordinates0'][:,:2],rows[:,6:8],atol=2e-7)
    np.testing.assert_allclose(actual['arrays']['Tangent'],rows[:,16:19],atol=2e-7)
    np.testing.assert_allclose(actual['arrays']['Binormal'],rows[:,19:22],atol=2e-7)
    np.testing.assert_array_equal(actual['indices'],np.arange(len(p)))
    (folder/mesh.name/(mesh.name+'.fxsxml')).write_text('<?xml version="1.0" encoding="utf-8"?>\n<Asset>\n'
        f'  <Mesh file="{mesh.name}.gr2"/>\n  <Texture file="RT_IF_Concept_Diff.dds"/>\n  <Texture file="RT_IF_Concept_SREF.dds"/>\n</Asset>\n')
    record['native_export']={'gr2':str(path.relative_to(folder)),'scale':SCALE,'readback':True,'engine_test':False}


def build(out, quick):
    folder=out/'concept-models';folder.mkdir(exist_ok=True)
    sources=pack_materials(out/'native-local',folder)
    reader=Reader(out/'incan_terrace_farm/incan_terrace_farm-uncompressed.gr2'); source=reader.root()
    regular=Reader(out/'medieval_farm1/medieval_farm1-uncompressed.gr2').root()
    old=(natural.network,natural.farmstead,natural.field_patches,natural.palm)
    base_palm=natural.palm
    def smaller_palm(lod=0):
        palm=base_palm(lod);palm.faces=[(p*.65,n,uv,mat,part) for p,n,uv,mat,part in palm.faces];return palm
    natural.palm=smaller_palm
    natural.network=sparse_network; natural.farmstead=farm_function(regular)
    base_fields=natural.field_patches
    natural.field_patches=lambda *a,**kw:base_fields(*a,**kw,texture_repeat=2.4,parcel_margin=.018)
    try:
        meshes=[natural.tile(kind,state) for kind in v3.KINDS for state in ('Wet','Dry')]
        meshes += [natural.tile(kind,lod=1) for kind in v3.KINDS]
        meshes += [m for m in v3.parts() if m.meta['category'] in ('connector','source')]
        meshes += [natural.scene()]
    finally:natural.network,natural.farmstead,natural.field_patches,natural.palm=old
    records=[];cards=[]
    for mesh in meshes:
        mesh.name=mesh.name.replace('RT_IF_','RT_IF_Concept_',1)
        if mesh.meta['category']=='connector':
            seen={}
            for route in mesh.routes:
                key=route['name'];seen[key]=seen.get(key,0)+1
                if seen[key]>1:route['name']=key+'_'+str(seen[key])
        remap(mesh)
        mesh.meta.update(native_game_validation=False,design_status='review candidate from selected concept',source_geometry='v3 terrain and authored fields; actual regular Farm1 building')
        record=export(mesh,folder)
        if record['category']!='assembly':export_native(mesh,record,folder,reader,source)
        records.append(record)
        _,(p,n,uv),_=read_glb(folder/mesh.name/(mesh.name+'.glb'))
        cards.append({'name':mesh.name,'label':mesh.name.removeprefix('RT_IF_Concept_').replace('_',' · '),'category':record['category'],'triangles':record['triangles'],'bounds':record['bounds_z_up'],'groups':record['groups'],'data':base64.b64encode(np.concatenate((p,n,uv),axis=1).astype('<f4').tobytes()).decode()})
        print(mesh.name,record['triangles'],'triangles',flush=True)
    cards.sort(key=lambda c:0 if c['category']=='assembly' else 1)
    html=(HERE.parent/'irrigation_v3/irrigation_viewer.html').read_text().replace('__ASSET_DATA__',json.dumps(cards,separators=(',',':'))).replace('__ATLAS_DATA__','data:image/png;base64,'+base64.b64encode((folder/'RT_IF_Diffuse.png').read_bytes()).decode())
    html=html.replace('Original source meshes','Actual mesh review · native-derived local candidates').replace('Irrigated farm · v3','Selected concept · models').replace('Source kit only. Native GR2 conversion, terrain fitting and game placement remain pending.','GLB/OBJ/BR2 and experimental GR2 exports. Native game loading, terrain fit and dynamic placement remain unverified.')
    (folder/'index.html').write_text(html)
    (folder/'review.html').write_text((HERE/'concept_model_review.html').read_text())
    manifest={'models':records,'native_game_validation':False,'redistributable':False,'material_sources':sources,'regular_farm_source_sha256':digest(out/'native-local/medieval_farm1.gr2'),'stock_uv_note':'Degenerate solid-colour cap UVs offset by 0.0001 for defined export tangents; source geometry preserved under uniform scale/translation.','crop_family_note':'Actual Crops_Africa pixels; exact desert regional selection unverified. Parcel geometry remains authored.','original_materials_retained':['foliage','wood'],'source_units':'v3 radius 6; native candidates scaled to 30-unit apothem; in-game fit unverified'}
    (folder/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'TECHNICAL_NOTES.txt').write_text('Selected concept: actual meshes with native crop/masonry/terrain pixels and regular Farm1 geometry.\nV3 partial terraces and spans; sparse connected carriers, closed exposed ends.\nLocal reference-derived candidates only. No engine acceptance or runtime adjacency.\nGLB/OBJ/BR2 use normalized source units. GR2 uses 30-unit-apothem native fixture scale.\nThe connected district is an assembly review, not one native tile asset.\nConstruction/pillaged variants and floodplain transitions remain in the earlier library; this pass covers four terrain families wet/dry plus LOD and components.\n')
    if not quick:
        for kind in v3.KINDS:
            name=f'RT_IF_Concept_{kind}_Wet'
            render_glb(folder/name/(name+'.glb'),1000,750,shadow_bias=.065).save(folder/(kind+'-preview.png'))
            render_glb(folder/name/(name+'.glb'),260,195,shadow_bias=.065).save(folder/(kind+'-distance.png'))
        reference=folder/'native-farm1-source.glb'
        review_glb(parts(selected_models(regular,regular_farm_states(regular)['constructed'])),out/'native-local',reference)
        render_glb(reference,1000,750,elevation=50,shadow_bias=.12).save(folder/'native-farm1-source-preview.png')
        name='RT_IF_Concept_ConnectedDistrict'
        render_glb(folder/name/(name+'.glb'),1600,1120,azimuth=-74,elevation=47,shadow_bias=.065).save(folder/'connected-district-preview.png')
    return folder


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--quick',action='store_true');args=parser.parse_args()
    print(build(args.output.resolve(),args.quick))
