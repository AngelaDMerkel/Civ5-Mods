#!/usr/bin/env python3
"""Check R3 channels against actual crop triangles, and preserve R1/R2 models."""
import argparse
import json
import math
import numpy as np
from build_concept_models import OUT,ROOT,read_glb,digest
from validate_concept_revision import validate as validate_revision

ROT=np.array([[math.cos(.19),-math.sin(.19)],[math.sin(.19),math.cos(.19)]])


def validate(out):
    report=validate_revision(out,3);folder=out/'concept-models-r3'
    manifest=json.loads((folder/'models.json').read_text());alignment=0;clear=0;flanked=0;gentle=0;prop_clearance=0
    for rec in manifest['models']:
        if rec['category']!='tile':continue
        name=rec['name'];_,(p,n,uv),_=read_glb(folder/name/(name+'.glb'))
        if rec['terrain']=='GentleHill':
            walls=next(g for g in rec['groups'] if g['name']=='retaining_wall')
            assert walls['count']==18,'gentle terraces must have three straight wall fronts'
            group=next(g for g in rec['groups'] if g['name']=='crop_surface');crops=p[group['first']:group['first']+group['count']].reshape(-1,3,3)
            top=crops[np.min(crops[:,:,2],axis=1)>.84]
            area=np.linalg.norm(np.cross(top[:,1]-top[:,0],top[:,2]-top[:,0]),axis=1).sum()/2
            assert area>5.,('upper terrace not cultivated',area)
            assert p[:,2].max()<2.,'unexpected high crown';gentle+=1
        if rec['terrain']!='Flat':continue
        group=next(g for g in rec['groups'] if g['name']=='crop_surface');crop=p[group['first']:group['first']+group['count']].reshape(-1,3,3)
        a=crop[:,0,:2];u=crop[:,1,:2]-a;v=crop[:,2,:2]-a;den=u[:,0]*v[:,1]-u[:,1]*v[:,0]
        def covered(xy):
            d=xy-a;b=(d[:,0]*v[:,1]-d[:,1]*v[:,0])/den;c=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/den
            return bool(np.any((b>=-1e-6)&(c>=-1e-6)&(b+c<=1+1e-6)))
        prop=next(g for g in rec['groups'] if g['name']=='native_regular_farm')
        prop_xy=p[prop['first']:prop['first']+prop['count'],:2]
        for route in rec['routes']:
            points=np.array(route['points']);world=(points[:,:2]+rec['parcel_origin'])@ROT
            if route['parcel_axis']=='row':
                y=route['parcel_row']*2.7+.17*math.sin(route['parcel_row']*2.1)
                assert np.max(abs(world[:,1]-y))<1e-5;alignment+=1
            elif route['parcel_axis']=='column':
                row=route['parcel_row'];x=world[:,0].mean();col=round((x-.62*(row%2))/3)
                expected=col*3+.62*(row%2)+.31*math.sin(col*1.8)
                assert np.max(abs(world[:,0]-expected))<1e-5;alignment+=1
            else:assert route['parcel_axis']=='field_margin'
            if route['end']=='closed_field_outlet':
                assert any(g['name']==route['name']+'_closed_end' for g in rec['groups'])
            for start,end in zip(points,points[1:]):
                d=end-start;side=np.array([-d[1],d[0]])/np.linalg.norm(d[:2])
                t=np.clip(((prop_xy-start[:2])@d[:2])/np.dot(d[:2],d[:2]),0,1)
                assert np.min(np.linalg.norm(prop_xy-start[:2]-t[:,None]*d[:2],axis=1))>route['width']/2+.06,(name,'farm prop crosses ditch')
                prop_clearance+=1
                for t in (.25,.5,.75):
                    xy=start[:2]*(1-t)+end[:2]*t
                    for shift in (-.45,0,.45):
                        assert not covered(xy+side*route['width']*shift),(name,route['name'],'crop under ditch');clear+=1
                    if covered(xy+side*.18) and covered(xy-side*.18):flanked+=1
    assert gentle==3 and alignment>50 and flanked>40
    prior=json.loads((ROOT/'shared/art/irrigated-farm/v3-civ5-direction/model-review-r2.json').read_text());preserved=0
    for rec in prior['candidates']:
        for extension,sha in rec['sha256'].items():
            assert digest(out/'concept-models-r2'/rec['name']/(rec['name']+'.'+extension))==sha;preserved+=1
    report.update(exact_parcel_seam_routes=alignment,crop_free_channel_samples=clear,
                  channel_samples_between_crops=flanked,gentle_hill_variants=gentle,preserved_r2_exports=preserved,farm_prop_channel_clearance_checks=prop_clearance)
    (folder/'parcel-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=type(OUT),default=OUT);a=p.parse_args();print(json.dumps(validate(a.output.resolve()),indent=2))
