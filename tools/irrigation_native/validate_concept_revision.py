#!/usr/bin/env python3
"""Validate revised exports, measured span grades/joins, and preserved R1 hashes."""
import argparse
import json
import math
import numpy as np
from build_concept_models import OUT, ROOT, digest, read_glb
from validate_concept_models import validate as validate_exports


def validate(out):
    report=validate_exports(out,revision=True);folder=out/'concept-models-r2'
    manifest=json.loads((folder/'models.json').read_text());span_count=0;max_grade=0;max_turn=0;vertex_checks=0;junction_checks=0
    assert manifest['aqueduct_max_grade']==.02 and manifest['aqueduct_max_turn_degrees']==15.
    for rec in manifest['models']:
        name=rec['name'];_,(p,_,_),_=read_glb(folder/name/(name+'.glb'))
        routes={r['name']:r for r in rec['routes']}
        for r in routes.values():
            if r.get('kind')=='terrace_canal':
                cap=any(g['name']==r['name']+'_closed_end' for g in rec['groups'])
                if r['end']=='closed_field_outlet':assert cap,(name,r['name'],'missing end cap')
                else:
                    assert not cap
                    assert any(q.get('upstream')==r['name'] and np.linalg.norm(np.array(q['points'][0])-r['points'][-1])<1e-6 for q in routes.values()),(name,r['name'],'unconnected open end')
            if r.get('kind')!='aqueduct':continue
            pts=np.array(r['points']);d=np.diff(pts,axis=0);length=np.linalg.norm(d[:,:2],axis=1);grades=-d[:,2]/length
            assert (grades>=-1e-7).all() and (grades<=.02+1e-7).all(),(name,r['name'],'steep span',max(grades))
            max_grade=max(max_grade,float(max(grades)));span_count+=1
            directions=d[:,:2]/length[:,None]
            if len(directions)>1:
                turn=np.degrees(np.arccos(np.clip(np.sum(directions[:-1]*directions[1:],axis=1),-1,1)))
                assert max(turn)<=15.+1e-5,(name,r['name'],'acute span bend',max(turn));max_turn=max(max_turn,float(max(turn)))
            # The exported water strip must actually occupy the declared graded
            # centerline. Checking metadata alone would miss a tilted mesh deck.
            group=next(g for g in rec['groups'] if g['name']==r['name']+'_water')
            vertices=p[group['first']:group['first']+group['count']].reshape(-1,6,3)
            assert len(vertices)==len(pts)-1
            for tri,a,b in zip(vertices,pts,pts[1:]):
                np.testing.assert_allclose((tri[0]+tri[5])/2,a,atol=2e-6)
                np.testing.assert_allclose((tri[1]+tri[2])/2,b,atol=2e-6);vertex_checks+=6
        if rec['category']=='assembly':
            for link in rec['feeder_graph']:
                span=np.array(routes[link['span']]['points']);receiver=np.array(routes[link['receiver']]['points'])
                dest=next(r for r in routes.values() if r.get('upstream')==link['receiver']);dest=np.array(dest['points'])
                for u,v in [(span[-1]-span[-2],receiver[1]-receiver[0]),(receiver[-1]-receiver[-2],dest[1]-dest[0])]:
                    angle=math.degrees(math.acos(float(np.clip(np.dot(u[:2],v[:2])/np.linalg.norm(u[:2])/np.linalg.norm(v[:2]),-1,1))))
                    assert angle<=15.+1e-5,('receiver tangent',link,angle);junction_checks+=1
    frozen=json.loads((ROOT/'shared/art/irrigated-farm/v3-civ5-direction/model-review.json').read_text())
    preserved=0
    for rec in frozen['candidates']:
        for extension,sha in rec['sha256'].items():
            assert digest(out/'concept-models'/rec['name']/(rec['name']+'.'+extension))==sha;preserved+=1
    report.update(aqueduct_spans=span_count,max_aqueduct_grade_percent=100*max_grade,
                  max_aqueduct_slope_degrees=math.degrees(math.atan(max_grade)),max_span_turn_degrees=max_turn,
                  measured_water_vertices=vertex_checks,aligned_receiver_junctions=junction_checks,preserved_previous_exports=preserved,
                  native_exports=0,model_approval='unapproved')
    (folder/'revision-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=type(OUT),default=OUT);a=p.parse_args();print(json.dumps(validate(a.output.resolve()),indent=2))
