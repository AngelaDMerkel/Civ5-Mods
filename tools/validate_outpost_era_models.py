#!/usr/bin/env python3
"""Check portable mesh geometry and archive integrity, not native GR2 rendering."""
from pathlib import Path
import json
import shlex
import struct
import zipfile
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/models/outpost-eras-v1'


def main():
    manifest=json.loads((OUT/'models.json').read_text())
    approvals=json.loads((ROOT/manifest['approval_source']).read_text())['selections']
    records=manifest['models'];assert len(records)==24
    assert len({r['name'] for r in records})==24
    assert not list(OUT.rglob('*.gr2')), 'Source bundle must not pretend to contain native GR2'
    signatures={}
    for selection in approvals:
        variants=[r for r in records if r['era']==selection['era']]
        assert {r['state'] for r in variants}=={'Constructed','UnderConstruction','Pillaged'}
        assert all(r['concept']==selection['concept'] and r['era_type']==selection['eraType'] for r in variants)
    with Image.open(OUT/'RO_Era_Diffuse.png') as atlas:assert atlas.size==(1024,1024)
    with Image.open(OUT/'RO_Era_Diffuse.dds') as atlas:assert atlas.size==(1024,1024)
    for r in records:
        name=r['name'];folder=OUT/name
        lines=(folder/(name+'.obj')).read_text().splitlines()
        p=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('v ')])
        n=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('vn ')])
        uv=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('vt ')])
        f=[l.split()[1:] for l in lines if l.startswith('f ')]
        assert len(f)==r['triangles'] and len(p)==r['vertices']==len(f)*3
        assert 100<len(f)<6000,(name,'triangle budget')
        assert p.shape==n.shape and len(uv)==len(p)
        assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()
        assert (uv>0).all() and (uv<1).all()
        assert np.allclose(np.linalg.norm(n,axis=1),1,atol=2e-7)
        assert p[:,2].min()>-1e-6 and p[:,2].max()<7.5,(name,'height/ground')
        assert np.abs(p[:,:2]).max()<4.6,(name,'footprint')
        assert np.allclose(np.stack((p.min(axis=0),p.max(axis=0))),r['bounds_z_up'])
        expected=np.arange(1,len(p)+1).reshape(-1,3)
        for face,ids in zip(f,expected):
            assert [list(map(int,x.split('/'))) for x in face]==[[i,i,i] for i in ids]
        triangles=p.reshape(-1,3,3)
        cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        assert (np.linalg.norm(cross,axis=1)>1e-8).all(),(name,'degenerate triangle')
        assert (np.sum(cross*n[::3],axis=1)>0).all(),(name,'winding')
        # A conservative triangle AABB test establishes an unobstructed center
        # through the entire mesh height. It does not certify native unit scale.
        lo=triangles.min(axis=1);hi=triangles.max(axis=1)
        intrudes=(lo[:,:2]<1-1e-7).all(axis=1)&(hi[:,:2]>-1+1e-7).all(axis=1)
        assert not intrudes.any(),(name,'central garrison square obstructed')
        assert 'map_Kd '+name+'_diffuse.png' in (folder/(name+'.mtl')).read_text()
        with Image.open(OUT/r['diffuse']) as atlas:assert atlas.size==(1024,1024)
        with Image.open(OUT/r['diffuse_dds']) as atlas:assert atlas.size==(1024,1024)
        dds=(OUT/r['diffuse_dds']).read_bytes()
        assert dds[:4]==b'DDS ' and dds[84:88]==b'DXT1'
        assert struct.unpack_from('<I',dds,28)[0]==11
        expected_dds_bytes=sum(max(1,(max(1,1024>>i)+3)//4)**2*8 for i in range(11))
        assert len(dds)==128+expected_dds_bytes
        assert r['texture_bake']['charts']>0 and r['texture_bake']['texels_per_source_unit']>=10
        br=(folder/(name+'.br2')).read_text().splitlines()
        assert br[1]=='skeleton' and len(shlex.split(br[2]))==26 and br[3]=='meshes:1'
        start=br.index('vertices')+1;end=br.index('triangles')
        vertices=np.array([[float(x) for x in l.split()] for l in br[start:end]])
        assert vertices.shape==(len(p),22) and br[-1]=='end'
        assert np.allclose(vertices[:,:3],p) and np.allclose(vertices[:,3:6],n)
        assert np.allclose(vertices[:,6],uv[:,0]) and np.allclose(vertices[:,7],1-uv[:,1])
        assert (vertices[:,8:16]==[0,0,0,0,255,0,0,0]).all()
        tangent=vertices[:,16:19];bitangent=vertices[:,19:22]
        assert np.allclose(np.linalg.norm(tangent,axis=1),1,atol=2e-7)
        assert np.allclose(np.linalg.norm(bitangent,axis=1),1,atol=2e-7)
        assert np.allclose(np.sum(n*tangent,axis=1),0,atol=2e-7)
        assert np.allclose(np.sum(n*bitangent,axis=1),0,atol=2e-7)
        assert np.allclose(np.sum(tangent*bitangent,axis=1),0,atol=2e-7)
        ids=np.array([[int(x) for x in l.split()] for l in br[end+1:-1]])
        assert np.array_equal(ids,expected-1)
        raw=(folder/(name+'.glb')).read_bytes()
        assert struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw))
        size,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
        gltf=json.loads(raw[20:20+size]);binsize,kind=struct.unpack_from('<II',raw,20+size)
        assert kind==0x004e4942 and 28+size+binsize==len(raw)
        blob=raw[28+size:];assert gltf['buffers'][0]['byteLength']<=len(blob)
        for view in gltf['bufferViews']:assert view['byteOffset']+view['byteLength']<=len(blob) and view['byteOffset']%4==0
        arrays=[]
        for acc in gltf['accessors']:
            assert acc['componentType']==5126 and acc['count']==len(p)
            view=gltf['bufferViews'][acc['bufferView']]
            dim={'VEC2':2,'VEC3':3}[acc['type']]
            data=np.frombuffer(blob,dtype='<f4',count=len(p)*dim,offset=view['byteOffset']).reshape(-1,dim)
            assert np.allclose(data.min(axis=0),acc['min']) and np.allclose(data.max(axis=0),acc['max'])
            arrays.append(data)
        assert np.allclose(arrays[0],p,atol=2e-7) and np.allclose(arrays[1],n,atol=2e-7)
        assert np.allclose(arrays[2][:,0],uv[:,0]) and np.allclose(arrays[2][:,1],1-uv[:,1])
        assert 'uri' not in gltf['images'][0]
        view=gltf['bufferViews'][gltf['images'][0]['bufferView']]
        assert blob[view['byteOffset']:view['byteOffset']+view['byteLength']]==(OUT/r['diffuse']).read_bytes()
        signatures.setdefault(r['era'],set()).add((len(p),tuple(p.sum(axis=0))))
        with Image.open(OUT/r['preview']) as preview:assert preview.size==(760,650)
        print(f'{name}: {len(f)} triangles, OBJ/GLB/BR2 agree, center clear')
    assert len(signatures)==8 and all(len(v)==3 for v in signatures.values()), 'State geometry must differ'
    with zipfile.ZipFile(ROOT/'dist/Outpost-Era-Model-Sources-v1.zip') as archive:
        files=[p for p in OUT.rglob('*') if p.is_file()]
        assert len(archive.namelist())==len(files)
        for p in files:assert archive.read('Outpost-Era-Model-Sources-v1/'+p.relative_to(OUT).as_posix())==p.read_bytes()
    print('24 source mesh states and archive verified. GR2 conversion and game rendering remain unverified.')


if __name__=='__main__':main()
