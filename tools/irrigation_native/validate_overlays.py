#!/usr/bin/env python3
"""Check the actual overlay exports and adjacency contract independently."""
import argparse
import json
import numpy as np
from build_overlays import OUT, original, curve, select_edges
from irrigation_mesh_io import read_glb
from validate_irrigation_meshes import read_obj


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=type(OUT),default=OUT)
    out=parser.parse_args().output.resolve()
    manifest=json.loads((out/'models.json').read_text())
    records=manifest['models'];assert len(records)==16
    positions={};closed=0;route_count=0
    for rec in records:
        name=rec['name'];folder=out/name
        p,n,uv,faces,parts=read_obj(folder/(name+'.obj'));positions[name]=p
        assert len(p)==len(n)==len(uv)==rec['triangles']*3
        assert np.isfinite(p).all() and np.isfinite(uv).all()
        tri=p.reshape(-1,3,3);cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        assert (np.linalg.norm(cross,axis=1)>1e-8).all(),name
        assert (np.sum(cross*n[::3],axis=1)>0).all(),name
        assert np.allclose(np.linalg.norm(n,axis=1),1,atol=2e-7)
        tex=uv.reshape(-1,3,2);a,b=tex[:,1]-tex[:,0],tex[:,2]-tex[:,0]
        assert (np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])>1e-12).all()
        g,(gp,gn,guv),_=read_glb(folder/(name+'.glb'))
        assert np.allclose(gp,p,atol=2e-6) and np.allclose(gn,n,atol=2e-7)
        assert np.allclose(guv,np.c_[uv[:,0],1-uv[:,1]],atol=2e-7)
        lines=(folder/(name+'.br2')).read_text().splitlines()
        start=lines.index('vertices')+1;end=lines.index('triangles')
        br=np.array([list(map(float,s.split())) for s in lines[start:end]])
        assert np.allclose(br[:,:3],p) and np.allclose(br[:,3:6],n)
        assert np.allclose(br[:,6:8],guv,atol=2e-7)
        for direction in (br[:,16:19],br[:,19:22]):
            assert np.allclose(np.linalg.norm(direction,axis=1),1,atol=2e-7)
            assert np.allclose(np.sum(direction*n,axis=1),0,atol=2e-7)
        assert not any('crop_surface' in s or 'terrain_surface' in s or 'foliage' in s for s in parts)
        if name.endswith('_Dry'):assert not any(s.endswith('_water') for s in parts)
        routes={r['name']:r for r in rec['routes']};route_count+=len(routes)
        for r in routes.values():
            pts=np.array(r['points']);assert (np.diff(pts[:,2])<=1e-8).all()
            if r.get('upstream'):
                assert r['upstream'] in routes
                upstream=np.array(routes[r['upstream']]['points'])
                assert np.min(np.linalg.norm(upstream-pts[0],axis=1))<1e-7
            if r.get('end')=='closed_field_outlet':
                caps=tri[np.array([s==r['name']+'_terminal' for s in parts])]
                assert len(caps)>=3,'Missing closed outlet geometry'
                assert caps[:,:,2].min()<pts[-1,2]<caps[:,:,2].max()
                closed+=1
        if rec['category']=='edge':
            at_edge=p[np.abs(p[:,0]-original.A)<1e-6]
            if rec['connected']:
                assert len(at_edge)>0 and 'edge_terminal' not in parts
                # A counterpart translated to the next center and rotated 180
                # degrees has the same open cross section at the shared edge.
                counterpart=at_edge*np.array([-1,-1,1])+[2*original.A,0,0]
                left={tuple(v) for v in np.round(at_edge,6)}
                right={tuple(v) for v in np.round(counterpart,6)}
                assert left==right,'Opposite socket gap'
            else:assert p[:,0].max()<original.A-.70,'Closed end crosses an exposed edge'
    # Preserve the good aqueduct; compare every exported position/normal/UV to
    # the unchanged v3 builder rather than merely checking a triangle count.
    preserved=0
    for mesh in original.parts():
        if mesh.name not in positions:continue
        mesh.faces.sort(key=lambda f:f[4]);p,n,uv=mesh.arrays()
        _,(gp,gn,guv),_=read_glb(out/mesh.name/(mesh.name+'.glb'))
        assert np.allclose(gp,p,atol=2e-6) and np.allclose(gn,n,atol=2e-7)
        assert np.allclose(guv,np.c_[uv[:,0],1-uv[:,1]],atol=2e-7)
        preserved+=1
    layouts=json.loads((out/'edge-layouts.json').read_text())
    assert len(layouts)==729 and {r['neighbors'] for r in layouts}==set(range(64))
    pairs=set()
    for r in layouts:
        pair=(r['neighbors'],r['water_links']);assert pair not in pairs;pairs.add(pair)
        for i in range(6):
            opened=r['ends'][str(i)]=='open_joint'
            assert opened==bool(r['water_links']&(1<<i))
            assert not opened or r['neighbors']&(1<<i)
    for neighbors in range(64):
        for water in range(64):
            if water&~neighbors:
                try:select_edges(neighbors,water)
                except ValueError:pass
                else:raise AssertionError('Open connection to an absent farm')
    try:curve([(0,0,0),(1,0,1)])
    except ValueError:pass
    else:raise AssertionError('Uphill spline accepted')
    report={'result':'PASS','models':len(records),'closed_outlets':closed,
            'routes':route_count,'preserved_aqueduct_and_intake_models':preserved,
            'neighbor_water_combinations':len(layouts),'native_game_validation':False,
            'native_terrain_clearance':'pending native base import; not tested'}
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
