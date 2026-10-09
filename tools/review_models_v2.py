#!/usr/bin/env python3
"""Lay out unchanged approved art, actual mesh renders and stock references.

These are comparison documents, not new concept artwork. Stock references stay
outside source and mod ZIPs. This script does not repaint any supplied image.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image,ImageDraw,ImageFont,ImageOps
from model_approval_v2 import apply_approval

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'output/art-concepts/2026-10-09/round-3'
MODELS=ROOT/'output/models/revised-v2'
OUT=ROOT/'output/model-review/approved-art-alignment'
BG=(238,233,219);INK=(42,49,43);MUTED=(92,97,83);RULE=(202,193,174)


def font(size):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',size)


def text(sheet,xy,value,size=23,color=INK):
    ImageDraw.Draw(sheet).multiline_text(xy,value,font=font(size),fill=color,spacing=9)


def place(sheet,image,box):
    image=ImageOps.contain(image,(box[2],box[3]),Image.Resampling.LANCZOS)
    x=box[0]+(box[2]-image.width)//2;y=box[1]+(box[3]-image.height)//2
    sheet.paste(image,(x,y),image if image.mode=='RGBA' else None)


def selected(key):
    manifest=json.loads((ART/'selections.json').read_text())
    entry=next(x for x in manifest['selections'] if x['id']==key)
    image=Image.open(ART/entry['source']).convert('RGBA')
    if entry['review_crop']:
        x,y,w,h=entry['review_crop'];image=image.crop((x,y,x+w,y+h))
    return image


def native_icon(file,x,y,w=176):
    return Image.open(ART/'references'/file).convert('RGBA').crop((x,y,x+w,y+w))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    models=json.loads((MODELS/'models.json').read_text())
    apply_approval(models,MODELS)
    approved=models['design_approval']['status']=='approved'
    statuses={m['name']:m['model_approval'] for m in models['models']}
    status_line='All nine source designs approved on 9 October 2026.' if approved else 'Source assets changed since approval; review required.'
    sheet=Image.new('RGB',(1800,1600),BG)
    text(sheet,(36,26),'APPROVED ART → REVISED SOURCE MODELS',34)
    text(sheet,(36,77),'The approved images are unchanged. Centre images render the actual exported geometry and textures.',23,MUTED)
    for x,label in [(36,'APPROVED MOD ART'),(462,'REVISED MODEL'),(1490,'REAL CIV V ART')]:text(sheet,(x,139),label,22)
    ImageDraw.Draw(sheet).line((36,179,1764,179),fill=RULE,width=2)
    text(sheet,(36,200),'Caravansary · A',26)
    place(sheet,selected('caravansary'),(36,246,360,305))
    text(sheet,(36,571),'Build Caravansary · B',23)
    place(sheet,selected('worker'),(55,611,154,144))
    place(sheet,Image.open(MODELS/'approved-well-detail.jpg'),(223,591,230,200))
    text(sheet,(36,793),'Flat canopy · four pale posts',19,MUTED)
    place(sheet,Image.open(MODELS/'RT_Caravansary_Ancient-preview.jpg'),(460,192,1005,638))
    text(sheet,(510,827),'Tall pale gateway · low lodgings · warm cornice · open court',22,MUTED)
    place(sheet,native_icon('buildingportraits256_exp2-decoded.png',40,552),(1500,267,230,230))
    text(sheet,(1490,522),'Stock Caravansary\n(portrait reference)',21,MUTED)
    text(sheet,(1490,626),'Match the readable\nforms and materials;\nretain our chosen\narchitecture.',20,MUTED)
    ImageDraw.Draw(sheet).line((36,880,1764,880),fill=RULE,width=2)
    text(sheet,(36,903),'Ministry · portrait B',26)
    place(sheet,selected('ministry'),(45,950,310,273))
    text(sheet,(36,1241),'Wonder painting · A',23)
    place(sheet,selected('wonder'),(36,1280,404,240))
    place(sheet,Image.open(MODELS/'RT_MinistryOfCoin-preview.jpg'),(460,893,1005,610))
    text(sheet,(490,1520),'Stepped counting house + pale treasury entrance, red banners and bronze seal',21,MUTED)
    place(sheet,native_icon('buildingatlas-decoded.png',808,552),(1500,979,230,230))
    text(sheet,(1490,1235),'Stock Palace\n(portrait reference)',21,MUTED)
    text(sheet,(1490,1343),'Stock artwork is\nshown for review.\nIt is excluded from\nthe model package.',20,MUTED)
    sheet.save(OUT/'approved-architecture-comparison.jpg',quality=95)

    sheet=Image.new('RGB',(1800,1060),BG)
    text(sheet,(36,25),'CIV V MAP STYLE / SOURCE MODEL READABILITY',34)
    text(sheet,(36,77),'Native game reference at left; our standalone source renders at right. Game scale and shaders remain unverified.',22,MUTED)
    text(sheet,(36,138),'REAL CIV V — official Wonders of the Ancient World screenshot',23)
    path=Path('/private/tmp/civ5-irrigation-references/civ5-official-farms.jpg')
    if path.exists():place(sheet,Image.open(path),(36,184,930,554))
    else:raise FileNotFoundError('The original local official screenshot reference is required; never substitute a generated scene.')
    text(sheet,(36,770),'Style cues used in this pass',25)
    text(sheet,(36,818),'Restrained stone, plaster and cloth colours\nFine surface wear and soft cavity shading\nClear rooflines and openings at small sizes\nMatte surfaces with limited metal accents',22,MUTED)
    text(sheet,(1010,138),'ACTUAL REVISED SOURCES — 192 px studies',23)
    names=[('RT_Caravansary_Ancient','Caravansary / A + B'),('RT_MinistryOfCoin','Ministry / B + A'),
           ('RT_Caravansary_Industrial','Industrial / approved'),('RT_IrrigationWorks','Waterworks / approved'),
           ('RT_MotorizedCaravan','Motorized / approved')]
    for i,(name,label) in enumerate(names):
        if statuses[name]!='approved':label=label.split(' / ')[0]+' / review required'
        x=1010+(i%2)*375;y=199+(i//2)*245
        place(sheet,Image.open(MODELS/(name+'-small.png')),(x+60,y,192,152))
        text(sheet,(x+10,y+170),label,21)
    text(sheet,(1010,937),status_line+'\nNew art requires options + Civ V comparison + your selection.',20,MUTED)
    sheet.save(OUT/'civ5-style-comparison.jpg',quality=95)

    # Preserve the approval boundary and reference provenance in a machine-
    # readable review record. Never edit the original selection manifest.
    approval=json.loads((ART/'exports.json').read_text())
    for file,digest in approval['source_sha256'].items():
        assert hashlib.sha256((ART/file).read_bytes()).hexdigest()==digest,file
    for entry in approval['files']:
        assert hashlib.sha256((ROOT/'mod'/entry['file']).read_bytes()).hexdigest()==entry['sha256'],entry['file']
    record={'art_revision':3,'approved_selection_manifest':str((ART/'selections.json').relative_to(ROOT)),
            'all_approved_sources_and_runtime_dds':'SHA-256 unchanged from original export manifest',
            'model_status':status_line+' Native rendering unverified.',
            'additional_art_policy':'Present multiple options with actual Civ V references; user chooses before integration.',
            'model_approval_record':'docs/art/rt-models/approved.json',
            'provisional_models':[m['name'] for m in models['models'] if m['model_approval']!='approved'],
            'stock_reference_policy':'Review only; excluded from mod and source bundles',
            'map_reference_url':'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/99614/ss_4527541f1f4d602a9ab952ce27cd7e17c9329f50.1920x1080.jpg?t=1605830261',
            'style_inspection':['Installed Citadel_Anc_DIFF.dds','Installed Fort_MID_DIFF.dds','Official Wonders of the Ancient World map screenshot','Official Explorers Map Pack desert screenshot']}
    (OUT/'review.json').write_text(json.dumps(record,indent=2)+'\n')
    (OUT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>Approved art — model alignment</title><style>body{background:#eee9db;color:#30382f;font:17px/1.6 system-ui;margin:32px}main{max-width:1500px;margin:auto}img{width:100%;display:block;margin:24px 0}a{color:#365d49}</style><main><h1>Approved art and revised models</h1><p>All nine source model designs were approved on 9 October 2026. Actual source mesh renders appear beside the unchanged approved art and genuine Civ V references. Stock references are review material only and are excluded from source and mod packages. New icons and artwork still require options, comparison and user selection. Native game integration is pending.</p><img src="approved-architecture-comparison.jpg" alt="Caravansary and Ministry models alongside the approved mod art and native Civ V portraits"><img src="civ5-style-comparison.jpg" alt="Official Civ V screenshot and small renders of the revised source models"><p><a href="../../models/revised-v2/index.html">All nine source models and reverse views</a> · <a href="review.json">Review provenance</a> · <a href="https://store.steampowered.com/app/99614/">Official map reference source</a></p></main></html>''')
    page=OUT/'index.html'
    page.write_text(page.read_text().replace('All nine source model designs were approved on 9 October 2026.',status_line))
    print('Comparison documents saved; approved source art and all 11 runtime DDS hashes unchanged.')


if __name__=='__main__':main()
