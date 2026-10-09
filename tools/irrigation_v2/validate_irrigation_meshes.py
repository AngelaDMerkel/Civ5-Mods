#!/usr/bin/env python3
"""Independent checks of exported geometry, UVs, BR2, GLB, seams and water grade."""
from pathlib import Path
import json
import argparse
import math
import shlex
import struct
import zipfile
import numpy as np
from PIL import Image
from irrigation_mesh_io import read_glb

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1] if HERE.name=='irrigation_v2' else HERE.parent
OUT=ROOT/'output/models/irrigated-farm-v2' if HERE.name=='irrigation_v2' else ROOT


def read_obj(path):
    p=[];n=[];uv=[];faces=[];parts=[];part=''
    for line in path.read_text().splitlines():
        if line.startswith('v '):p.append(list(map(float,line.split()[1:])))
        elif line.startswith('vn '):n.append(list(map(float,line.split()[1:])))
        elif line.startswith('vt '):uv.append(list(map(float,line.split()[1:])))
        elif line.startswith('g '):part=line[2:]
        elif line.startswith('f '):
            faces.append([list(map(int,v.split('/'))) for v in line.split()[1:]]);parts.append(part)
    return np.array(p),np.array(n),np.array(uv),np.array(faces),parts


def ray_hits(p,origin,direction):
    tri=p.reshape(-1,3,3);e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
    h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.sum(e1*h,axis=1)
    good=np.abs(det)>1e-8;inv=np.zeros_like(det);inv[good]=1/det[good]
    s=origin-tri[:,0];u=inv*np.sum(s*h,axis=1);q=np.cross(s,e1)
    v=inv*np.sum(q*direction,axis=1);t=inv*np.sum(e2*q,axis=1)
    return int(np.sum(good&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-6)))


def seam_uv(triangles,uvs,xy):
    for t,uv in zip(triangles,uvs):
        if (xy<t[:,:2].min(axis=0)-1e-6).any() or (xy>t[:,:2].max(axis=0)+1e-6).any():continue
        a,b,c=t[:,:2];matrix=np.column_stack((b-a,c-a))
        if abs(np.linalg.det(matrix))<1e-9:continue
        w=np.linalg.solve(matrix,xy-a)
        if w.min()>=-1e-5 and w.sum()<=1+1e-5:return uv[0]*(1-w.sum())+uv[1]*w[0]+uv[2]*w[1]
    raise AssertionError(('no crop face at seam',xy))


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT)
    OUT=parser.parse_args().output.resolve()
    manifest=json.loads((OUT/'models.json').read_text());records=manifest['models'];counts={}
    assert len(records)==36
    exported={}
    for r in records:
        name=r['name'];folder=OUT/name
        p,n,uv,faces,parts=read_obj(folder/(name+'.obj'))
        exported[name]=(p,n,uv,parts)
        assert p.shape==n.shape and len(uv)==len(p)==r['triangles']*3
        assert len(faces)==r['triangles']
        expected=np.arange(1,len(p)+1).reshape(-1,3)
        assert np.array_equal(faces,np.repeat(expected[:,:,None],3,axis=2))
        assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()
        assert (uv>0).all() and (uv<1).all()
        assert np.allclose(np.linalg.norm(n,axis=1),1,atol=2e-7)
        tr=p.reshape(-1,3,3);cross=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0])
        assert (np.linalg.norm(cross,axis=1)>1e-8).all(),(name,'zero-area triangle')
        assert (np.sum(cross*n[::3],axis=1)>0).all(),(name,'winding mismatch')
        assert np.allclose([p.min(axis=0),p.max(axis=0)],r['bounds_z_up'],atol=1e-7)
        # UV Jacobians must remain nondegenerate for native tangent-space export.
        tex=uv.reshape(-1,3,2);d1=tex[:,1]-tex[:,0];d2=tex[:,2]-tex[:,0]
        assert (np.abs(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0])>1e-12).all()
        br=(folder/(name+'.br2')).read_text().splitlines()
        assert br[1]=='skeleton' and len(shlex.split(br[2]))==26 and br[3]=='meshes:1'
        start=br.index('vertices')+1;end=br.index('triangles')
        vertices=np.array([list(map(float,line.split())) for line in br[start:end]])
        assert vertices.shape==(len(p),22)
        assert np.allclose(vertices[:,:3],p) and np.allclose(vertices[:,3:6],n)
        assert np.allclose(vertices[:,6:8],np.column_stack((uv[:,0],1-uv[:,1])))
        assert (vertices[:,8:16]==[0,0,0,0,255,0,0,0]).all()
        tan,bit=vertices[:,16:19],vertices[:,19:22]
        for a in (tan,bit):
            assert np.allclose(np.linalg.norm(a,axis=1),1,atol=2e-7)
            assert np.allclose(np.sum(a*n,axis=1),0,atol=2e-7)
        assert np.allclose(np.sum(tan*bit,axis=1),0,atol=2e-7)
        assert np.array_equal(np.array([list(map(int,s.split())) for s in br[end+1:-1]]),expected-1)
        assert br[-1]=='end'
        raw=(folder/(name+'.glb')).read_bytes()
        assert struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw))
        g,arrays,blob=read_glb(folder/(name+'.glb'))
        assert np.allclose(arrays[0],p,atol=2e-6) and np.allclose(arrays[1],n,atol=2e-7)
        assert np.allclose(arrays[2],np.column_stack((uv[:,0],1-uv[:,1])),atol=2e-7)
        for view in g['bufferViews']:
            assert view['byteOffset']%4==0 and view['byteOffset']+view['byteLength']<=len(blob)
        im=g['bufferViews'][g['images'][0]['bufferView']]
        assert blob[im['byteOffset']:im['byteOffset']+im['byteLength']]==(OUT/'RT_IF_Diffuse.png').read_bytes()
        assert sum(gr['count'] for gr in r['groups'])==len(p)
        for route in r['routes']:
            points=np.array(route['points']);assert (np.diff(points[:,2])<=1e-7).all(),(name,'uphill water')
        if r['category']=='tile':
            assert r['triangles']<14000,(name,'budget')
            assert not any('foundation' in part or 'pedestal' in part for part in parts)
            if r['state']!='Wet':assert not any(part.endswith('_water') for part in parts)
            else:assert any(part.endswith('_water') for part in parts)
            counts.setdefault(r['terrain'],{})[(r['state'],r['lod'])]=r['triangles']
        if name=='RT_IF_Aqueduct_Short':
            assert ray_hits(p,np.array((-.85,-2,.35)),np.array((0,1,0)))==0,'Arch opening is blocked'
        print(name,r['triangles'],'triangles: formats, UVs, normals and grade verified')
    for kind,states in counts.items():
        assert states[('Wet',1)]<states[('Wet',0)],(kind,'LOD does not reduce geometry')
        assert set(states)=={('Wet',0),('Dry',0),('Construction',0),('Pillaged',0),('Wet',1)}
    socket=json.loads((OUT/'connectors.json').read_text())
    assert {r['mask'] for r in socket['layouts']}==set(range(64))
    assert socket['canonical_count']==14
    for entry in socket['layouts']:
        mask=entry['canonical_mask'];k=entry['rotation_steps'];rot=((mask<<k)|(mask>>(6-k)))&63 if k else mask
        assert rot==entry['mask'] and entry['edges']==[i for i in range(6) if rot&(1<<i)]
    # Independently assemble opposite edge sockets at all six orientations.
    a=socket['apothem']
    for edge in range(6):
        angle=edge*math.pi/3;normal=np.array((math.cos(angle),math.sin(angle)))
        left=a*normal;right=2*a*normal+a*np.array((math.cos(angle+math.pi),math.sin(angle+math.pi)))
        assert np.allclose(left,right,atol=1e-12)
    assembly=next(r for r in records if r['category']=='assembly')
    reached={-1};links=list(assembly['feeder_graph'])
    while links:
        progress=False
        for link in links[:]:
            if link['parent'] in reached:
                assert link['start'][2]>=link['end'][2]
                assert np.allclose(link['end'],assembly['tiles'][link['child']]['inlet'])
                reached.add(link['child']);links.remove(link);progress=True
        assert progress,'Disconnected/cyclic feeder graph'
    assert reached=={-1,*range(len(assembly['tiles']))}
    # Crop UVs on both sides of actual exported shared edges must coincide.
    p,n,uv,parts=exported[assembly['name']];tri=p.reshape(-1,3,3);tex=uv.reshape(-1,3,2)
    seam_count=0
    for i,tile in enumerate(assembly['tiles']):
        for other in assembly['tiles'][i+1:]:
            c0,c1=np.array(tile['center']),np.array(other['center']);delta=c1-c0
            if abs(np.linalg.norm(delta)-2*a)>1e-6:continue
            middle=(c0+c1)/2;normal=delta/np.linalg.norm(delta);side=np.array((-normal[1],normal[0]))
            mask0=np.array([s==f'tile_{tile["q"]}_{tile["r"]}_crop_surface' for s in parts])
            mask1=np.array([s==f'tile_{other["q"]}_{other["r"]}_crop_surface' for s in parts])
            for offset in [-2.2,-1.1,.17,1.25,2.35]:
                xy=middle+side*offset
                u0=seam_uv(tri[mask0],tex[mask0],xy-normal*1e-6)
                u1=seam_uv(tri[mask1],tex[mask1],xy+normal*1e-6)
                assert np.allclose(u0,u1,atol=2e-6),(tile,other,'UV seam',u0,u1)
                seam_count+=1
    assert seam_count>=20
    # Check the actual feeder deck against the sampled terrace surfaces, not
    # merely endpoint elevations. Includes the channel's entire outer width.
    from build_irrigation_meshes import surface_height, in_poly, HEX, WATER_WIDTH, WALL_WIDTH, WATER_DEPTH, bridge
    from irrigation_mesh_io import Mesh
    clear_samples=0
    for link in assembly['feeder_graph']:
        start,end=np.array(link['start']),np.array(link['end']);delta=end-start
        side=np.array((-delta[1],delta[0]));side/=np.linalg.norm(side)
        for t in np.linspace(.01,.99,101):
            point=start+delta*t
            for shift in [-WATER_WIDTH/2-WALL_WIDTH,0,WATER_WIDTH/2+WALL_WIDTH]:
                xy=point[:2]+side*shift
                for tile in assembly['tiles']:
                    local=xy-tile['center']
                    if in_poly(local,HEX):
                        h=surface_height(tile['kind'],*local)
                        assert point[2]-WATER_DEPTH-.055>=h-1e-6,(link,'deck intersects terrace',point,h)
                        clear_samples+=1
    try:bridge(Mesh('invalid'),(0,0,1),(2,0,2))
    except ValueError:pass
    else:raise AssertionError('Uphill span accepted')
    with Image.open(OUT/'RT_IF_Diffuse.png') as atlas:assert atlas.size==(2048,2048)
    report={'models':len(records),'total_triangles':sum(r['triangles'] for r in records),
            'crop_seam_samples':seam_count,'feeder_clearance_samples':clear_samples,
            'adjacency_masks':64,'rotational_classes':14,'native_game_validation':False,
            'result':'PASS: source mesh/export/UV/grade checks; GR2 and in-game behavior untested'}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
