#!/usr/bin/env python3
"""Build unapproved source revisions as offline editable meshes; never convert native art."""
import argparse
import base64
import json
from pathlib import Path
import shutil
import numpy as np
from build_concept_models import HERE, OUT, digest, remap, Reader, v3, natural, Mesh, export, read_glb, render_glb
from concept_revision_geometry import geometry, scene, curved_bridge, MAX_GRADE, MAX_TURN

def build(out,quick=False,revision=2):
    if revision not in (2,3,4):raise ValueError('Unsupported review revision')
    mesh_geometry,mesh_scene=geometry,scene
    if revision==3:
        from concept_parcel_geometry import geometry as mesh_geometry, scene as mesh_scene
    if revision==4:
        from concept_cascade_geometry import geometry as mesh_geometry, scene as mesh_scene
    prefix=f'RT_IF_ConceptR{revision}_'
    folder=out/f'concept-models-r{revision}';folder.mkdir(exist_ok=True)
    previous=out/'concept-models';old=json.loads((previous/'models.json').read_text())
    # Reuse the exact native-pixel review atlas; this pass makes no DDS or GR2.
    shutil.copyfile(previous/'RT_IF_Diffuse.png',folder/'RT_IF_Diffuse.png')
    regular=Reader(out/'medieval_farm1/medieval_farm1-uncompressed.gr2').root()
    with mesh_geometry(regular):
        meshes=[natural.tile(kind,state) for kind in v3.KINDS for state in ('Wet','Dry')]
        meshes += [natural.tile(kind,lod=1) for kind in v3.KINDS]
        meshes += [m for m in v3.parts() if m.meta['category'] in ('connector','source') and 'Aqueduct' not in m.name]
        for kind,length,height in [('Short',3.4,1.05),('Long',6.,1.8),('Mountain',4.7,2.6)]:
            for lod in (0,1):
                m=Mesh('RT_IF_Aqueduct_'+kind+('_LOD1' if lod else ''));m.lod=lod
                curved_bridge(m,[[-length/2,0,height],[length/2,0,height-length*.008]],lambda x,y:0,'aqueduct',lod=lod)
                m.meta=dict(category='connector',lod=lod,variant=kind);meshes.append(m)
        meshes.append(mesh_scene())
    cards=[];records=[]
    for m in meshes:
        if not m.name.startswith(prefix):m.name=m.name.replace('RT_IF_',prefix,1)
        seen={}
        for route in m.routes:
            name=route['name'];seen[name]=seen.get(name,0)+1
            if seen[name]>1:route['name']=name+'_'+str(seen[name])
        remap(m)
        m.meta.update(native_game_validation=False,design_status=f'unapproved revision {revision}; awaiting user review',
                      source_geometry='authored broad benches/parcels; genuine regular Farm1 building')
        rec=export(m,folder);records.append(rec)
        _,(p,n,uv),_=read_glb(folder/m.name/(m.name+'.glb'))
        cards.append(dict(name=m.name,label=m.name.removeprefix(prefix).replace('_',' · '),
                          category=rec['category'],triangles=rec['triangles'],bounds=rec['bounds_z_up'],groups=rec['groups'],
                          data=base64.b64encode(np.concatenate((p,n,uv),axis=1).astype('<f4').tobytes()).decode()))
        print(m.name,rec['triangles'],'triangles',flush=True)
    cards.sort(key=lambda c:0 if c['category']=='assembly' else 1)
    html=(HERE.parent/'irrigation_v3/irrigation_viewer.html').read_text().replace('__ASSET_DATA__',json.dumps(cards,separators=(',',':'))).replace('__ATLAS_DATA__','data:image/png;base64,'+base64.b64encode((folder/'RT_IF_Diffuse.png').read_bytes()).decode())
    html=html.replace('Original source meshes',f'Revision {revision} · unapproved models').replace('Irrigated farm · v3','Irrigation · revised geometry').replace('Source kit only. Native GR2 conversion, terrain fitting and game placement remain pending.','Offline mesh review. Native conversion, game testing and integration remain on hold.')
    if revision>=3:html=html.replace('TECHNICAL_NOTES.txt','review.html').replace('Design &amp; conversion notes','Review &amp; model status')
    (folder/'index.html').write_text(html)
    manifest={k:old[k] for k in ('material_sources','regular_farm_source_sha256','stock_uv_note','crop_family_note','original_materials_retained')}
    manifest.update(models=records,revision=revision,native_game_validation=False,redistributable=False,
                    model_approval='unapproved; revised geometry requested, no native conversion authorized',
                    native_exports=0,source_units='normalized radius-six fixture; engine fit unverified',
                    atlas_sha256=digest(folder/'RT_IF_Diffuse.png'),aqueduct_max_grade=MAX_GRADE,aqueduct_max_turn_degrees=MAX_TURN,
                    previous_candidates='concept-models; original geometry and approval checkpoint preserved')
    (folder/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (folder/'review.html').write_text((HERE/{2:'concept_revision_review.html',3:'concept_parcel_review.html',4:'concept_cascade_review.html'}[revision]).read_text())
    if not quick:render(folder,revision)
    return folder


def render(folder,revision=2):
    for kind in v3.KINDS:
        name=f'RT_IF_ConceptR{revision}_{kind}_Wet';path=folder/name/(name+'.glb')
        render_glb(path,1000,750,shadow_bias=.065).save(folder/(kind+'-preview.png'))
        render_glb(path,260,195,shadow_bias=.065).save(folder/(kind+'-distance.png'))
        print('Rendered',kind,flush=True)
    if revision>=3:
        name=f'RT_IF_ConceptR{revision}_Flat_Wet'
        render_glb(folder/name/(name+'.glb'),1000,1000,azimuth=-90,elevation=89.9,shadow_bias=.065).save(folder/'parcel-plan-preview.png')
    if revision==4:
        name='RT_IF_ConceptR4_SteepHill_Wet';path=folder/name/(name+'.glb')
        render_glb(path,1200,950,azimuth=-90,elevation=30,shadow_bias=.065).save(folder/'cascade-front-preview.png')
        render_glb(path,1000,1000,azimuth=-90,elevation=89.9,shadow_bias=.065).save(folder/'tier-plan-preview.png')
    name=f'RT_IF_ConceptR{revision}_ConnectedDistrict';path=folder/name/(name+'.glb')
    render_glb(path,1600,1120,azimuth=-74,elevation=47,shadow_bias=.065).save(folder/'connected-district-preview.png')
    render_glb(path,1600,750,azimuth=-90,elevation=9,shadow_bias=.065).save(folder/'aqueduct-profile-preview.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--quick',action='store_true');parser.add_argument('--render-only',action='store_true');parser.add_argument('--revision',type=int,choices=[2,3,4],default=2);a=parser.parse_args()
    if a.render_only:render(a.output.resolve()/f'concept-models-r{a.revision}',a.revision)
    else:print(build(a.output.resolve(),a.quick,a.revision))
