#!/usr/bin/env python3
"""Verify actual concept-model exports, provenance and gravity connectivity."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from build_concept_models import OUT, ROOT, SCALE, digest
from native_gr2 import Reader
from native_scene import parts, selected_models, regular_farm_states, world_arrays
from irrigation_mesh_io import read_glb


def point_segment_distance(p,a,b):
    d=b-a; t=np.clip(np.dot(p-a,d)/np.dot(d,d),0,1)
    return np.linalg.norm(p-a-d*t)


def validate(out, revision=False):
    revision=2 if revision is True else int(revision or 0)
    if revision not in (0,2,3,4,5):raise ValueError('Unsupported mesh revision')
    folder=out/(f'concept-models-r{revision}' if revision else 'concept-models'); manifest=json.loads((folder/'models.json').read_text())
    assert manifest['native_game_validation'] is False and manifest['redistributable'] is False
    for source in manifest['material_sources']:
        assert digest(out/'native-local'/source['file'])==source['sha256']
    assert digest(out/'native-local/medieval_farm1.gr2')==manifest['regular_farm_source_sha256']
    native_root=Reader(out/'medieval_farm1/medieval_farm1-uncompressed.gr2').root()
    source_building=next(p for p in parts(selected_models(native_root,regular_farm_states(native_root)['constructed'])) if all(m['ExtendedData']['ShaderSet']=='BuildingShader' for m in p['materials']))
    source_positions=world_arrays(source_building)[0][source_building['indices']]*.115
    native_count=0; triangles=0; routes_count=0; clearance_count=0; seam_count=0; outcomes=[]
    for rec in manifest['models']:
        name=rec['name'];base=folder/name
        g,(p,n,uv),blob=read_glb(base/(name+'.glb'))
        assert p.shape==(rec['triangles']*3,3)
        assert np.isfinite(np.column_stack((p,n,uv))).all()
        assert np.allclose(np.linalg.norm(n,axis=1),1,atol=2e-7)
        tri=p.reshape(-1,3,3);cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        assert (np.linalg.norm(cross,axis=1)>1e-9).all()
        assert (np.sum(cross*n[::3],axis=1)>0).all(),(name,'winding')
        assert np.allclose([p.min(0),p.max(0)],rec['bounds_z_up'],atol=2e-6)
        assert (uv>=-1e-6).all() and (uv<=1+1e-6).all(),(name,'atlas UV outside image')
        lines=(base/(name+'.br2')).read_text().splitlines()
        rows=np.array([list(map(float,s.split())) for s in lines[lines.index('vertices')+1:lines.index('triangles')]])
        assert rows.shape==(len(p),22)
        np.testing.assert_allclose(rows[:,:3],p,atol=2e-6)
        np.testing.assert_allclose(rows[:,3:6],n,atol=2e-7)
        np.testing.assert_allclose(rows[:,6:8],uv,atol=2e-7)
        for frame in (rows[:,16:19],rows[:,19:22]):
            assert np.allclose(np.linalg.norm(frame,axis=1),1,atol=3e-7)
            assert np.allclose(np.sum(frame*n,axis=1),0,atol=3e-7)
        obj=(base/(name+'.obj')).read_text().splitlines()
        op=np.array([list(map(float,s.split()[1:])) for s in obj if s.startswith('v ')])
        np.testing.assert_allclose(op,p,atol=2e-6)
        if 'native_export' in rec:
            native=parts(Reader(base/(name+'.gr2')).root())
            assert len(native)==1;native=native[0]
            np.testing.assert_allclose(native['arrays']['Position'],p*SCALE,atol=7e-6)
            for key,expected in [('Normal',n),('Tangent',rows[:,16:19]),('Binormal',rows[:,19:22])]:
                np.testing.assert_allclose(native['arrays'][key],expected,atol=3e-7)
            np.testing.assert_allclose(native['arrays']['TextureCoordinates0'][:,:2],uv,atol=2e-7)
            np.testing.assert_array_equal(native['indices'],np.arange(len(p)))
            for item in ET.parse(base/(name+'.fxsxml')).getroot():
                f=item.attrib['file'];assert (base/f).is_file() or (folder/f).is_file()
            native_count+=1
        routes={r['name']:r for r in rec['routes']};assert len(routes)==len(rec['routes'])
        for route in routes.values():
            points=np.array(route['points']);assert (np.diff(points[:,2])<=1e-7).all(),(name,'uphill',route['name'])
            if route.get('upstream'):
                parent=np.array(routes[route['upstream']]['points'])
                distance=min(point_segment_distance(points[0],a,b) for a,b in zip(parent,parent[1:]))
                assert distance<1e-5,(name,route['name'],'disconnected',distance)
            seen=set();r=route
            while r.get('upstream'):
                assert r['name'] not in seen,'cycle';seen.add(r['name']);r=routes[r['upstream']]
            if rec['category'] in ('tile','assembly'):assert r['name']==rec['water_network']['root']
        # Use actual exported terrain triangles, not the builder height helper.
        terrain=[]
        for group in rec['groups']:
            if group['name'].endswith('terrain_surface'):
                terrain.extend(p[group['first']:group['first']+group['count']].reshape(-1,3,3))
        if terrain:
            terrain=np.array(terrain);a=terrain[:,0,:2];u=terrain[:,1,:2]-a;v=terrain[:,2,:2]-a;den=u[:,0]*v[:,1]-u[:,1]*v[:,0]
            for route in routes.values():
                for start,end in zip(np.array(route['points']),np.array(route['points'])[1:]):
                    d=end-start;length=np.linalg.norm(d[:2]);assert length>1e-8
                    side=np.array([-d[1],d[0]])/length
                    for point in np.linspace(start,end,5):
                        for shift in (-.5,0,.5):
                            xy=point[:2]+side*route['width']*shift;w=xy-a
                            b=(w[:,0]*v[:,1]-w[:,1]*v[:,0])/den;c=(u[:,0]*w[:,1]-u[:,1]*w[:,0])/den
                            ids=np.flatnonzero((b>=-1e-7)&(c>=-1e-7)&(b+c<=1+1e-7))
                            if len(ids):
                                z=np.max(terrain[ids,0,2]*(1-b[ids]-c[ids])+terrain[ids,1,2]*b[ids]+terrain[ids,2,2]*c[ids])
                                assert point[2]>=z+.045,(name,route['name'],'terrain clearance',point[2]-z)
                                clearance_count+=1
        if rec.get('terrain')=='Flat':
            if revision>=3:
                assert len(routes)>8 and all(r['kind']=='parcel_canal' for r in routes.values())
            else:
                assert len(routes)==(2 if revision else 3)
                assert all(r['end']=='closed_field_outlet' for r in routes.values())
        if rec['category']=='tile':
            group=next(g for g in rec['groups'] if g['name']=='native_regular_farm')
            prop=p[group['first']:group['first']+group['count']]
            np.testing.assert_allclose(prop-prop[0],source_positions-source_positions[0],atol=2e-6)
            assert any(g['name'].endswith('_water') for g in rec['groups'])==(rec['state']=='Wet')
        if rec['category']=='assembly':
            def sample(group,xy):
                positions=p[group['first']:group['first']+group['count']].reshape(-1,3,3)
                tex=uv[group['first']:group['first']+group['count']].reshape(-1,3,2)
                for tr,t in zip(positions,tex):
                    a=tr[1,:2]-tr[0,:2];b=tr[2,:2]-tr[0,:2];d=xy-tr[0,:2];det=a[0]*b[1]-a[1]*b[0]
                    w=(d[0]*b[1]-d[1]*b[0])/det;v=(a[0]*d[1]-a[1]*d[0])/det
                    if w>=-1e-7 and v>=-1e-7 and w+v<=1+1e-7:return t[0]*(1-w-v)+t[1]*w+t[2]*v
            groups={g['name']:g for g in rec['groups']}
            for i,tile in enumerate(rec['tiles']):
                for other in rec['tiles'][i+1:]:
                    a,b=np.array(tile['center']),np.array(other['center']);delta=b-a;distance=np.linalg.norm(delta)
                    if abs(distance-60/SCALE)>1e-6:continue
                    normal=delta/distance;side=np.array([-normal[1],normal[0]])
                    left=groups[f'tile_{tile["q"]}_{tile["r"]}_crop_surface'];right=groups[f'tile_{other["q"]}_{other["r"]}_crop_surface']
                    for offset in np.linspace(-2.6,2.6,31):
                        point=(a+b)/2+side*offset
                        x,y=sample(left,point-normal*1e-6),sample(right,point+normal*1e-6)
                        if x is None or y is None:continue
                        np.testing.assert_allclose(x,y,atol=3e-6);seam_count+=1
            assert seam_count>=20
        triangles+=rec['triangles'];routes_count+=len(routes)
        outcomes.append({'name':name,'triangles':rec['triangles'],'native_readback':'native_export' in rec})
    assert len(manifest['models'])==24 and native_count==(0 if revision else 23)
    if revision:
        assert manifest['revision']==revision and manifest['native_exports']==0
        assert not list(folder.rglob('*.gr2')) and not list(folder.rglob('*.dds')) and not list(folder.rglob('*.fxsxml'))
    with Image.open(folder/'RT_IF_Diffuse.png') as packed:
        from build_concept_models import NAMES
        for source in manifest['material_sources']:
            i=NAMES.index(source['material']);slot=packed.crop(((i%4)*512,(i//4)*512,(i%4+1)*512,(i//4+1)*512))
            expected=Image.open(out/'native-local'/source['file']).convert('RGBA');expected.putalpha(255)
            expected=expected.resize((512,512),Image.Resampling.NEAREST)
            assert np.array_equal(np.asarray(slot),np.asarray(expected))
    # DDS mip zero and GLB embedded material must match the packed reference pixels.
    if not revision:
        with Image.open(folder/'RT_IF_Diffuse.png') as png,Image.open(folder/'RT_IF_Concept_Diff.dds') as dds:
            assert np.array_equal(np.asarray(png.convert('RGBA')),np.asarray(dds.convert('RGBA')))
    report={'models':len(outcomes),'native_gr2_readbacks':native_count,'triangles':triangles,'routes':routes_count,'terrain_clearance_samples':clearance_count,'shared_crop_seam_samples':seam_count,'provenance_verified':True,'engine_test':False,'dynamic_placement_test':False,'results':outcomes}
    (folder/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return {k:v for k,v in report.items() if k!='results'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();print(json.dumps(validate(args.output.resolve()),indent=2))
