#!/usr/bin/env python3
"""Validate revised source geometry, complete requested scope and archive parity.

This cannot certify native GR2, engine rendering or the not-yet-built unit rig.
"""
from pathlib import Path
import json
import shlex
import struct
import zipfile
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/models/revised-v2'


def main():
    manifest=json.loads((OUT/'models.json').read_text());records=manifest['models']
    assert manifest['art_revision']==3
    assert len(records)==9 and len({r['name'] for r in records})==9
    expected={'IMPROVEMENT_RT_RELIEF_STATION':6,'BUILDING_CARAVANSARY':1,'BUILDING_RT_IRRIGATION_WORKS':1,'UNIT_RT_MOTORIZED_CARAVAN':1}
    assert {key:sum(r['database_type']==key for r in records) for key in expected}==expected
    assert all(r['database_type'] in expected for r in records)
    assert not list(OUT.rglob('*.gr2')), 'Source bundles must not invent native GR2'
    for era in ('Ancient','Industrial'):
        variants=[r for r in records if r.get('era')==era]
        assert {r['state'] for r in variants}=={'Constructed','UnderConstruction','Pillaged'}
    for file in manifest['textures']:
        with Image.open(OUT/file) as image:assert image.size==(2048,2048)
    with Image.open(OUT/'RT_Surface_Normal.png') as image:
        rgb=np.array(image);assert rgb[:,:,0].std()>1 and rgb[:,:,1].std()>1, 'Normal must contain surface relief'
    for r in records:
        name=r['name'];folder=OUT/name
        lines=(folder/(name+'.obj')).read_text().splitlines()
        p=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('v ')])
        n=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('vn ')])
        uv=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('vt ')])
        f=[l.split()[1:] for l in lines if l.startswith('f ')]
        assert len(f)==r['triangles'] and len(p)==r['vertices']==len(f)*3
        assert 500<len(f)<12000,(name,'triangle budget')
        assert p.shape==n.shape and len(uv)==len(p)
        assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()
        assert (uv>0).all() and (uv<1).all()
        assert np.allclose(np.linalg.norm(n,axis=1),1,atol=2e-7)
        assert p[:,2].min()>-1e-6 and p[:,2].max()<7.5,(name,'height/ground')
        assert np.abs(p[:,:2]).max()<4.6,(name,'footprint')
        assert np.allclose(np.stack((p.min(axis=0),p.max(axis=0))),r['bounds_z_up'])
        ids=np.arange(1,len(p)+1).reshape(-1,3)
        for face,indices in zip(f,ids):assert [list(map(int,x.split('/'))) for x in face]==[[i,i,i] for i in indices]
        tris=p.reshape(-1,3,3);cross=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
        assert (np.linalg.norm(cross,axis=1)>1e-8).all(),(name,'degenerate geometry')
        assert (np.sum(cross*n[::3],axis=1)>0).all(),(name,'winding')
        uvtri=uv.reshape(-1,3,2);e=uvtri[:,1]-uvtri[:,0];d=uvtri[:,2]-uvtri[:,0]
        assert (np.abs(e[:,0]*d[:,1]-e[:,1]*d[:,0])>1e-12).all(),(name,'degenerate UV')
        if r['category']=='station':
            low=tris.min(axis=1);high=tris.max(axis=1)
            overlaps=(low[:,:2]<.85-1e-7).all(axis=1)&(high[:,:2]>-.85+1e-7).all(axis=1)
            assert not overlaps.any(),(name,'central garrison position obstructed')
        if r['category']=='unit':assert len([part for part in r['parts'] if part.startswith('wheel_')])==6
        assert 'map_Kd '+name+'_Diffuse.png' in (folder/(name+'.mtl')).read_text()
        assert len(r['textures'])==6 and r['surface_bake']['charts']>0
        for file in r['textures']:
            with Image.open(OUT/file) as image:assert image.size==(2048,2048)
            if file.endswith(('Diffuse.dds','Specular.dds')):
                raw=(OUT/file).read_bytes()
                assert raw[84:88]==b'DXT1' and struct.unpack_from('<I',raw,28)[0]==12
                assert len(raw)==128+sum(max(1,2048//(2**i)//4)**2*8 for i in range(12))
        br=(folder/(name+'.br2')).read_text().splitlines()
        assert br[1]=='skeleton' and len(shlex.split(br[2]))==26 and br[3]=='meshes:1'
        start=br.index('vertices')+1;end=br.index('triangles')
        data=np.array([[float(x) for x in l.split()] for l in br[start:end]])
        assert data.shape==(len(p),22) and br[-1]=='end'
        assert np.allclose(data[:,:3],p) and np.allclose(data[:,3:6],n)
        assert np.allclose(data[:,6],uv[:,0]) and np.allclose(data[:,7],1-uv[:,1])
        assert (data[:,8:16]==[0,0,0,0,255,0,0,0]).all()
        t=data[:,16:19];b=data[:,19:22]
        assert np.allclose(np.linalg.norm(t,axis=1),1,atol=2e-7) and np.allclose(np.linalg.norm(b,axis=1),1,atol=2e-7)
        for a,c in [(t,b),(t,n),(b,n)]:assert np.allclose(np.sum(a*c,axis=1),0,atol=2e-7)
        assert np.array_equal(np.array([[int(x) for x in l.split()] for l in br[end+1:-1]]),ids-1)
        raw=(folder/(name+'.glb')).read_bytes();assert struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw))
        size,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
        gltf=json.loads(raw[20:20+size]);binsize,kind=struct.unpack_from('<II',raw,20+size)
        assert kind==0x004e4942 and 28+size+binsize==len(raw)
        blob=raw[28+size:];assert gltf['buffers'][0]['byteLength']<=len(blob)
        for view in gltf['bufferViews']:assert view['byteOffset']+view['byteLength']<=len(blob) and view['byteOffset']%4==0
        arrays=[]
        for acc in gltf['accessors']:
            assert acc['componentType']==5126 and acc['count']==len(p)
            view=gltf['bufferViews'][acc['bufferView']];dim={'VEC2':2,'VEC3':3}[acc['type']]
            data=np.frombuffer(blob,dtype='<f4',count=len(p)*dim,offset=view['byteOffset']).reshape(-1,dim)
            assert np.allclose(data.min(axis=0),acc['min']) and np.allclose(data.max(axis=0),acc['max'])
            arrays.append(data)
        assert np.allclose(arrays[0],p,atol=2e-7) and np.allclose(arrays[1],n,atol=2e-7)
        assert np.allclose(arrays[2][:,0],uv[:,0]) and np.allclose(arrays[2][:,1],1-uv[:,1])
        assert 'uri' not in gltf['images'][0]
        view=gltf['bufferViews'][gltf['images'][0]['bufferView']]
        assert blob[view['byteOffset']:view['byteOffset']+view['byteLength']]==(folder/(name+'_Diffuse.png')).read_bytes()
        with Image.open(OUT/r['preview']) as image:assert image.size==(960,760)
        with Image.open(OUT/(name+'-reverse.jpg')) as image:assert image.size==(720,570)
        if r['state']=='Constructed':
            with Image.open(OUT/(name+'-small.png')) as image:assert image.size==(192,152)
        print(f'{name}: {len(f)} triangles; geometry, UVs, normals, tangents and all exports agree')
    with zipfile.ZipFile(ROOT/'dist/RT-Revised-Model-Sources-v2.zip') as archive:
        files=[p for p in OUT.rglob('*') if p.is_file()]
        assert len(archive.namelist())==len(files)
        for p in files:assert archive.read('RT-Revised-Model-Sources-v2/'+p.relative_to(OUT).as_posix())==p.read_bytes()
    print('All four requested assets covered by nine source meshes. Farms/outposts excluded. Archive matches. Native game rendering remains unverified.')

if __name__=='__main__':main()
