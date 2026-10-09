"""Keep the user's model approval bound to the exact reviewed source assets."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
APPROVAL=ROOT/'shared/art/rt-models/approved.json'


def apply_approval(manifest,out):
    approval=json.loads(APPROVAL.read_text())
    for model in manifest['models']:
        selected=approval['models'].get(model['name'])
        current=model['files']+model['textures']
        matches=bool(selected) and set(current)==set(selected['sha256'])
        if matches:
            matches=all(hashlib.sha256((out/file).read_bytes()).hexdigest()==digest
                        for file,digest in selected['sha256'].items())
        model['model_approval']='approved' if matches else 'changed_since_approval'
        model['approved_on']=approval['approved_on'] if matches else None
    manifest['design_approval']={
        'status':'approved' if all(m['model_approval']=='approved' for m in manifest['models']) else 'review_required',
        'record':'approval.json',
        'approved_on':approval['approved_on'],
        'scope':'Visual design of the nine reviewed source meshes; native integration and rendering remain pending.'}
    (out/'approval.json').write_text(json.dumps(approval,indent=2)+'\n')
