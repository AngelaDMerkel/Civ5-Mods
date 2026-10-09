#!/usr/bin/env python3
"""Check source mesh/transfer-file integrity, not native GR2 compatibility."""
from pathlib import Path
import json
import math
import shlex
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/models/first-pass'


def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(a): return math.sqrt(sum(x*x for x in a))


def main():
    manifest=json.loads((OUT/'models.json').read_text())
    assert len(manifest['models']) == 8
    for model in manifest['models']:
        name=model['name']; folder=OUT/name
        obj=(folder/(name+'.obj')).read_text().splitlines()
        positions=[list(map(float,l.split()[1:])) for l in obj if l.startswith('v ')]
        normals=[list(map(float,l.split()[1:])) for l in obj if l.startswith('vn ')]
        uvs=[list(map(float,l.split()[1:])) for l in obj if l.startswith('vt ')]
        faces=[l.split()[1:] for l in obj if l.startswith('f ')]
        assert len(positions)==model['vertices']==len(normals)==len(uvs)
        assert len(faces)==model['triangles'] and len(positions)==len(faces)*3
        for face in faces:
            assert len(face)==3
            indices=[list(map(int,v.split('/'))) for v in face]
            for v,t,n in indices: assert 1<=v<=len(positions) and 1<=t<=len(uvs) and 1<=n<=len(normals)
            p=[positions[i[0]-1] for i in indices]
            normal=cross([b-a for a,b in zip(p[0],p[1])],[b-a for a,b in zip(p[0],p[2])])
            assert length(normal)>1e-8, f'Degenerate triangle: {name}'
            assert sum(a*b for a,b in zip(normal,normals[indices[0][2]-1]))>0, f'Winding/normal mismatch: {name}'
        assert all(abs(length(n)-1)<2e-6 for n in normals)
        assert all(math.isfinite(v) for p in positions for v in p)
        assert all(0<=c<=1 for uv in uvs for c in uv)
        assert (folder/'../RT_MapPalette.png').resolve().is_file()
        br=(folder/(name+'.br2')).read_text().splitlines()
        assert br[1]=='skeleton' and len(shlex.split(br[2]))==26 and br[3]=='meshes:1'
        start=br.index('vertices')+1; end=br.index('triangles')
        vertices=[list(map(float,l.split())) for l in br[start:end]]
        assert len(vertices)==len(positions) and len(br[end+1:-1])==len(faces) and br[-1]=='end'
        for row in vertices:
            assert len(row)==22 and row[8:16]==[0,0,0,0,255,0,0,0]
            assert abs(length(row[3:6])-1)<2e-6 and abs(length(row[16:19])-1)<2e-6
            assert abs(sum(n*t for n,t in zip(row[3:6],row[16:19])))<2e-6
        data=(folder/(name+'.glb')).read_bytes()
        magic,version,total=struct.unpack_from('<3I',data)
        assert (magic,version,total)==(0x46546c67,2,len(data))
        size,kind=struct.unpack_from('<2I',data,12); assert kind==0x4e4f534a
        gltf=json.loads(data[20:20+size]); size2,kind=struct.unpack_from('<2I',data,20+size)
        assert kind==0x004e4942 and 28+size+size2==len(data)
        assert gltf['buffers'][0]['byteLength']<=size2
        for view in gltf['bufferViews']: assert view['byteOffset']+view['byteLength']<=size2
        for acc in gltf['accessors']: assert acc['count']==len(positions)
        assert 'uri' not in gltf['images'][0], 'GLB texture must be embedded'
        print(f'{name}: {len(faces)} triangles; OBJ normals/UVs, rigid BR2 weights, embedded GLB valid')
    with zipfile.ZipFile(ROOT/'dist/Map-Model-Sources-v1.zip') as archive:
        files=[p for p in OUT.rglob('*') if p.is_file()]
        assert len(archive.namelist())==len(files)
        for p in files: assert archive.read('Map-Model-Sources-v1/'+p.relative_to(OUT).as_posix())==p.read_bytes()
    print('Source model archive matches files. GR2 conversion and game rendering are not verified.')


if __name__=='__main__': main()
