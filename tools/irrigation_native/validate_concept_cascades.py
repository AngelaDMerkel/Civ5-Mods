#!/usr/bin/env python3
"""Validate angular tier crops, exported cascades, and preserved R1-R3 reviews."""
import argparse
import json
import numpy as np
from build_concept_models import OUT, ROOT, read_glb, digest
from validate_concept_revision import validate as validate_revision


def cross2(a,b):
    return a[...,0]*b[...,1]-a[...,1]*b[...,0]


def validate(out):
    report=validate_revision(out,4);folder=out/'concept-models-r4'
    records=json.loads((folder/'models.json').read_text())['models']
    plots=steps=drops=water_vertices=wall_openings=crop_samples=flat_buffers=prop_checks=0
    for rec in records:
        if rec['category'] not in ('tile','assembly'):continue
        name=rec['name'];_,arrays,_=read_glb(folder/name/(name+'.glb'));p=arrays[0]
        for group in rec['groups']:
            if not group['name'].endswith('native_regular_farm'):continue
            prop=p[group['first']:group['first']+group['count']];lo,hi=prop.min(0),prop.max(0)
            for route in rec['routes']:
                points=np.array(route['points'])
                for start,end in zip(points,points[1:]):
                    if min(start[2],end[2])>hi[2]+.10:continue
                    for point in np.linspace(start,end,11):
                        if point[2]>hi[2]+.10:continue
                        distance=np.linalg.norm(point[:2]-np.clip(point[:2],lo[:2],hi[:2]))
                        assert distance>route['width']/2+.055,(name,group['name'],route['name'],'prop blocks water');prop_checks+=1
        if rec['category']!='tile':continue
        if rec['terrain']=='Flat':
            old=name.replace('ConceptR4','ConceptR3');_,prior,_=read_glb(out/'concept-models-r3'/old/(old+'.glb'))
            for a,b in zip(arrays,prior):np.testing.assert_array_equal(a,b);flat_buffers+=1
            continue
        groups={g['name']:g for g in rec['groups']}
        def vertices(name):
            g=groups[name];return p[g['first']:g['first']+g['count']]
        ls=np.array(rec['tier_lines']);zs=rec['tier_heights'];crops=[]
        assert len(rec['tier_plots'])==6 and len(zs)==3
        for plot in rec['tier_plots']:
            k=plot['tier'];points=vertices(plot['group']);crops.extend(points.reshape(-1,3,3))
            # Every exported crop triangle belongs entirely to one flat bench.
            np.testing.assert_allclose(points[:,2],zs[k]+.013,atol=1e-6)
            a,b=ls[k];d,c=ls[k+1];polygon=np.array([a,b,c,d])
            for start,end in zip(polygon,np.roll(polygon,-1,axis=0)):
                edge=end-start;inside=cross2(edge,points[:,:2]-start)/np.linalg.norm(edge)
                assert np.min(inside)>.05,(name,plot['group'],'crop crosses terrace boundary')
            # Both angular parcel shapes retain useful agricultural area.
            tri=points.reshape(-1,3,3);area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1).sum()/2
            assert area>.8,(name,'tiny or missing tier plot',area);plots+=1
        crops=np.array(crops);a=crops[:,0,:2];u=crops[:,1,:2]-a;v=crops[:,2,:2]-a;den=cross2(u,v)
        for route in rec['routes']:
            pts=np.array(route['points'])
            for start,end in zip(pts,pts[1:]):
                direction=end[:2]-start[:2];side=np.array([-direction[1],direction[0]])/np.linalg.norm(direction)
                for point in np.linspace(start,end,5):
                    for offset in (-.5,0,.5):
                        q=point[:2]+side*offset*route['width']-a
                        b=cross2(q,v)/den;c=cross2(u,q)/den
                        inside=(b>=-1e-6)&(c>=-1e-6)&(b+c<=1+1e-6)
                        near=(point[2]-crops[:,0,2]>.03)&(point[2]-crops[:,0,2]<.25)
                        assert not np.any(inside&near),(name,route['name'],'water lies over crops');crop_samples+=1
            if route.get('kind')!='stepped_cascade':continue
            k=route['from_tier'];dz=-np.diff(pts[:,2]);assert dz.max()<=.180001 and np.count_nonzero(dz>.01)>=2
            assert np.count_nonzero(dz<1e-7)>=np.count_nonzero(dz>.01),'missing level treads'
            expected=zs[k]-(zs[k-1] if k else 0.)
            np.testing.assert_allclose(pts[0,2]-pts[-1,2],expected,atol=1e-6)
            steps+=int(np.count_nonzero(dz>.01));drops+=1
            # Measure the opening in actual masonry geometry at this riser.
            front=vertices(f'tier_{k}_retaining_front');edge=ls[k,1]-ls[k,0];axis=edge/np.linalg.norm(edge)
            station=(front[:,:2]-(ls[k,0]+ls[k,1])/2)@axis
            assert np.all(abs(station)>route['width']/2+.07),'wall blocks cascade notch'
            assert station.min()<0<station.max();wall_openings+=1
            if rec['state']=='Wet':
                strip=vertices(route['name']+'_water').reshape(-1,6,3)
                assert len(strip)==len(pts)-1
                np.testing.assert_allclose((strip[:,0]+strip[:,5])/2,pts[:-1],atol=2e-6)
                np.testing.assert_allclose((strip[:,1]+strip[:,2])/2,pts[1:],atol=2e-6);water_vertices+=len(strip)*6
    assert plots==54 and drops==27 and flat_buffers==9
    preserved={}
    for revision in (2,3):
        checkpoint=json.loads((ROOT/f'shared/art/irrigated-farm/v3-civ5-direction/model-review-r{revision}.json').read_text());count=0
        for rec in checkpoint['candidates']:
            for extension,sha in rec['sha256'].items():
                assert digest(out/f'concept-models-r{revision}'/rec['name']/(rec['name']+'.'+extension))==sha;count+=1
        preserved[f'preserved_r{revision}_exports']=count
    report.update(tier_fitted_crop_plots=plots,stepped_cascades=drops,measured_cascade_steps=steps,
                  measured_cascade_water_vertices=water_vertices,open_retaining_notches=wall_openings,
                  hill_crop_channel_clearance_samples=crop_samples,unchanged_flat_buffers=flat_buffers,farm_prop_clearance_samples=prop_checks,**preserved)
    (folder/'cascade-validation.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=type(OUT),default=OUT);a=p.parse_args();print(json.dumps(validate(a.output.resolve()),indent=2))
