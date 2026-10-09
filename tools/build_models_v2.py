#!/usr/bin/env python3
"""Rebuild four requested RT assets. Farms deferred; outposts owned elsewhere."""
from pathlib import Path
import json
import math
import zipfile
import html
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from model_geometry_v2 import Mesh,caravansary,ministry,irrigation,truck,crate,well
from model_io_v2 import make_atlas,export,render
from model_approval_v2 import apply_approval

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/models/revised-v2'


def station_state(base,state):
    m=Mesh(base.name+'_'+state)
    remove={'roof','awning','well_water','well_rope','well_winch','well_post','well_canopy','well_canopy_trim','cornice','gate_coping','gate_cornice','gate_frieze','service_sign','lantern','chimney','lodge_parapet','lodge_cornice'}
    for p,n,mat,part in base.faces:
        if part in remove:continue
        q=p.copy()
        if state=='UnderConstruction':
            q[:,2]*=.57
            if part in ('door','window','crate','barrel','barrel_hoop'):continue
        else:
            if part in ('gate_spandrel','gate_impost'):continue
            center=q.mean(axis=0)
            if part in ('gateway_wing','gate_pilaster','gateway_arch','gate_pier') and center[0]<-.9:continue
            # Shared vertices must receive the same displacement. A per-face
            # height factor tears otherwise watertight walls into triangles.
            q[:,2]*=.47+.14*(np.sin(q[:,0]*.7+q[:,1]*.9)+1)/2
            if mat in ('timber','woodlight','canvas','goldcloth'):mat='charcoal'
            elif mat not in ('steel','glass'):mat='rubble'
        if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))>1e-9:m.face(q,mat,part)
    if state=='UnderConstruction':
        for x in (-4.13,4.13):
            for y in (-2.8,-.1,2.65):m.box((x,y,1.52),(.095,.095,3.04),'timber','scaffold_post',0)
            for z in (1,2.35):
                m.box((x,0,z),(.4,6.02,.085),'woodlight','scaffold_deck',0)
                m.beam((x,-2.8,z-.6),(x,-.1,z+.65),.055,'timber','scaffold_brace')
                m.beam((x,-.1,z+.65),(x,2.65,z-.6),.055,'timber','scaffold_brace')
        for i in range(4):m.box((1.72+i*.24,-1.45,.16),(.19,1.7,.27),'limestone','stone_delivery')
        crate(m,1.85,.8,.7)
    else:
        if base.name.endswith('Industrial'):
            m.box((2.09,3.1,1.45),(.41,.41,1.7),'rubble','broken_chimney')
        for i in range(18):
            x=-2.4+(i%3)*.34;y=-2.8+(i//3)*.63;h=.12+.065*(i%3)
            q=Mesh('rubble');q.box((0,0,h/2),(.34,.48,h),'rubble','debris');m.append(q,(x,y,0),i*29)
        for a,b in [((-2.8,-2.65,.08),(-1.45,-1.5,.2)),((2.4,2,.07),(1.4,1.4,.26))]:m.beam(a,b,.09,'charcoal','fallen_beam')
    return m


def font(size):
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',size)


def gallery(records):
    selected=[r for r in records if r['state']=='Constructed' and r.get('era')!='Industrial']
    sheet=Image.new('RGB',(1600,1380),(225,220,205));draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(selected):
        x=i%2*800;y=i//2*690
        im=Image.open(OUT/r['preview']).resize((800,633),Image.Resampling.LANCZOS)
        sheet.paste(im,(x,y+30));draw.text((x+25,y+12),r['label'],fill='#333d34',font=font(25))
        draw.text((x+25,y+656),str(r['triangles'])+' triangles · textured source mesh',fill='#5a6258',font=font(18))
    sheet.save(OUT/'four-additions-preview.jpg',quality=94)
    cards=[]
    for r in records:
        n=r['name'];cards.append(f'<article data-kind="{r["category"]}"><h2>{html.escape(r["label"])}</h2><p>{r["state"]} · {r["triangles"]:,} triangles</p><a href="{r["preview"]}"><img src="{r["preview"]}" alt="Actual {html.escape(r["label"])} source mesh"></a><footer><a href="{n}/{n}.glb">GLB</a> · <a href="{n}/{n}.obj">OBJ</a> · <a href="{n}/{n}.br2">BR2</a> · <a href="{n}-reverse.jpg">Reverse view</a></footer></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Realistic Terrain — revised 3D sources</title><style>
body{margin:0;background:#e1dccd;color:#333d34;font:16px/1.55 system-ui}main{max-width:1500px;margin:auto;padding:32px}h1,h2{font-family:Georgia,serif;font-weight:400}h1{font-size:44px;margin-bottom:12px}h2{font-size:25px;margin:12px 18px 0}p{max-width:1050px}article p{margin:2px 18px;font-size:14px;color:#616859}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}article{border:1px solid #c2bca8}img{width:100%;display:block}a{color:#34634b}footer{padding:15px 18px}button{padding:9px 16px;margin:0 8px 20px 0;border:1px solid #a3ac99;background:#eee9dc;color:#333d34;cursor:pointer}button[aria-pressed=true]{background:#334c3c;color:white}aside{border-left:3px solid #667759;padding:2px 18px;margin:25px 0}small{color:#616859}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:16px}}
</style><main><small>REALISTIC TERRAIN / APPROVED-ART ALIGNMENT / PASS 3</small><h1>Approved architecture, translated to the map</h1><p>Original textured meshes: Caravansary (early and industrial service depots), Ministry of Coin, Irrigation Works, and Motorized Caravan. Construction and pillaged states accompany both Caravansary eras. Irrigated farms are deferred. Resource Outpost assets are handled separately and were not changed.</p><p>The early Caravansary follows approved gateway A and well B. The Ministry combines portrait B’s stepped counting house with painting A’s treasury entrance. __MODEL_APPROVAL__ No new icons or paintings were created.</p><p>Every model now has its own padded UV atlas, subtle cavity shading and ground weathering baked into the exported diffuse texture. Small previews check readability at 192 pixels; this is not a calibrated in-game zoom.</p><aside><p><b>These images render the exported geometry and UVs.</b> They are not concept paintings or Civ V screenshots. The neutral ground, cast shadows and contact shading are preview lighting. The source models have no tile-shaped bases. Native GR2 conversion, unit rig/animation integration and in-game scale checks remain pending. Current playable mods retain their stock model references.</p></aside><details><summary>Compare with a real Civ V map screenshot</summary><p>Native game reference from <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=237640016">Zigzagzigal’s Siam guide</a>. This is game artwork, not one of our renders. It shows the map’s subdued colours, texture density and scale. The external image requires an internet connection; it is not bundled as a local asset.</p><img style="max-width:1100px" src="https://images.akamai.steamusercontent.com/ugc/796315596042088995/A3907BC72A9BB875E1A7B502F2A124AB5656B6EF/" alt="Real Civilization V map and city screen, external comparison reference"></details><div id="filters"><button data-filter="all" aria-pressed="true">All models</button><button data-filter="station" aria-pressed="false">Caravansaries</button><button data-filter="city" aria-pressed="false">City buildings</button><button data-filter="unit" aria-pressed="false">Motorized Caravan</button></div><div class="grid">'''+''.join(cards)+'''</div><p><a href="models.json">Coverage manifest</a> · <a href="CONVERSION.txt">Conversion and limitations</a> · <a href="RT_Surface.png">Diffuse atlas</a> · <a href="RT_Surface_Normal.png">Normal map</a> · <a href="RT_Surface_Specular.png">Specular map</a></p><script>document.querySelectorAll('button[data-filter]').forEach(b=>b.onclick=()=>{document.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.querySelectorAll('article').forEach(a=>a.hidden=b.dataset.filter!=='all'&&a.dataset.kind!==b.dataset.filter)});</script></main></html>'''
    approved=all(r.get('model_approval')=='approved' for r in records)
    status='All nine source model designs were approved by the user on 9 October 2026.' if approved else 'Some source meshes have changed since the recorded design approval and require review.'
    (OUT/'index.html').write_text(page.replace('__MODEL_APPROVAL__',status))


def main():
    OUT.mkdir(parents=True,exist_ok=True);atlas=make_atlas(OUT);items=[]
    for industrial in (False,True):
        base=caravansary(industrial);era='Industrial' if industrial else 'Ancient'
        for state,m in [('Constructed',base)]+[(s,station_state(base,s)) for s in ('UnderConstruction','Pillaged')]:
            items.append((m,{'label':'Caravansary · '+('industrial depot' if industrial else 'roadside gateway'),'category':'station','state':state,'era':era,'database_type':'IMPROVEMENT_RT_RELIEF_STATION'}))
    for builder,label,category,db in [(ministry,'Ministry of Coin','city','BUILDING_CARAVANSARY'),(irrigation,'Irrigation Works','city','BUILDING_RT_IRRIGATION_WORKS'),(truck,'Motorized Caravan','unit','UNIT_RT_MOTORIZED_CARAVAN')]:
        items.append((builder(),{'label':label,'category':category,'state':'Constructed','database_type':db}))
    records=[]
    for m,metadata in items:
        r=export(m,OUT,atlas);r.update(metadata);r['preview']=m.name+'-preview.jpg'
        render(m,atlas).save(OUT/r['preview'],quality=95)
        render(m,atlas,width=720,height=570,azimuth=133).save(OUT/(m.name+'-reverse.jpg'),quality=93)
        if r['state']=='Constructed':
            render(m,atlas,width=512,height=420,terrain=True).save(OUT/(m.name+'-terrain.jpg'),quality=92)
            render(m,atlas,width=960,height=760,terrain=True,elevation=42).resize((192,152),Image.Resampling.LANCZOS).save(OUT/(m.name+'-small.png'))
        if r['database_type']=='BUILDING_CARAVANSARY':
            r['art_reference']='Approved Ministry portrait B massing + wonder painting A entry details'
        elif r.get('era')=='Ancient':
            r['art_reference']='Approved Caravansary portrait A gateway + Build Caravansary B well canopy'
        else:
            r['art_reference']='Model design approved directly on 2026-10-09; no separate custom 2D artwork'
        r['model_approval']='pending_hash_comparison'
        records.append(r);print(m.name+': '+str(r['triangles'])+' triangles',flush=True)
    manifest={'stage':'Approved-art alignment pass; textured source meshes; native integration pending','art_revision':3,'approval_policy':'Any additional icons/artwork require multiple options alongside genuine Civ V references and explicit user selection before integration. Existing selections are preserved. Approval applies only to source assets matching the recorded hashes.','scope':['Caravansary','Ministry of Coin','Irrigation Works building','Motorized Caravan'],'deferred':['Irrigated and dry farms (user deferred)','Resource Outposts and era variants (separate thread; unchanged)'],'runtime_status':'No mod runtime references changed. No GR2 files. Native unit animations/rigging are not certified.','coordinates':'OBJ/BR2 Z up; GLB Y up. No terrain plinth. Scale is authoring scale, not calibrated game units.','textures':['RT_Surface.png','RT_Surface.dds','RT_Surface_Normal.png','RT_Surface_Normal.dds','RT_Surface_Specular.png','RT_Surface_Specular.dds'],'texture_note':'Root maps are the original material library. Each model has its own UV-baked diffuse/normal/specular textures; exports use those local textures. Diffuse and specular DDS include all BC1 mip levels.','preview_lighting':'Rasterized exported source triangles and baked atlas UVs; directional shadow map and screen-space contact occlusion. Preview ground is not part of exported meshes.','style_references':['Installed Civ V Citadel_Anc_DIFF and Fort_MID_DIFF (inspection only)','Official Wonders of the Ancient World and Explorers Map Pack screenshots (review only)'],'models':records}
    apply_approval(manifest,OUT)
    detail=Mesh('well_detail');well(detail,0,0)
    render(detail,atlas,width=420,height=420).save(OUT/'approved-well-detail.jpg',quality=95)
    (OUT/'models.json').write_text(json.dumps(manifest,indent=2)+'\n');gallery(records)
    (OUT/'CONVERSION.txt').write_text('''REALISTIC TERRAIN — REVISED MODEL SOURCES V2

Scope confirmed 9 October 2026: Caravansary, Ministry of Coin, Irrigation Works
building, Motorized Caravan. Irrigated farms deferred. Resource Outposts and their
approved era variants are being handled in another thread; their files are unchanged.

Approved-art alignment, pass 3
- Caravansary portrait A: tall smooth sandstone portal, lower flat-roof lodgings,
  warm cornice, real arch opening. Build action B: four-post pale flat well canopy.
- Ministry portrait B: asymmetric tall right block and lower left counting wing,
  slit windows, gold awning. Painting A: pale treasury pilasters, broad steps,
  red banners, bronze olive-branch seal and low green entry roof.
- Existing industrial depot, waterworks and lorry get the same restrained material
  treatment. The user approved all nine source designs on 9 October 2026.
  approval.json records the exact mesh and texture hashes; subsequent changes
  require a new design review. Native integration remains pending.
- Any ADDITIONAL icons or artwork must follow the established process: multiple
  alternatives alongside genuine Civ V references, then user selection before
  integration. Do not treat these model revisions as approval of new 2D artwork.

Nine meshes: early and industrial Caravansary x constructed/construction/pillaged,
plus Ministry of Coin, Irrigation Works and Motorized Caravan. Ordinary Caravan,
roads and unchanged native terrain use existing game graphics. Technology portraits,
worker glyphs and wonder paintings are 2D assets and do not need separate map meshes.

All geometry and material pixels are original. No Civ V assets are redistributed.
OBJ/MTL has named parts and unique padded planar UV charts per model. GLB embeds
the same baked diffuse texture used in the renders. Each model has 2048px diffuse,
derived micro-normal and material-specific specular PNG/DDS maps. Static cavity
shading (8 rays at 3 samples per chart) and ground weathering are baked into the
diffuse; directional cast shadows remain preview lighting only. Diffuse/specular
DDS use BC1 with 12 mip levels; normal DDS is uncompressed. Root RT_Surface maps
are the original material library, not the per-model runtime texture. The normal/specular textures require calibration for the native shader;
they are not automatically applied in the GLB preview. BR2 uses a rigid World bone.
The lorry has six individually named wheel groups for later rigging. It is an
editable unit mesh, not a certified native animated Civ V unit. No animation has
been invented or substituted for a real native export.

Previews use the actual exported triangles and UVs, plus directional cast shadows
and contact shading. Ground in previews is a lighting/display surface only. Model
exports do not contain a tile-shaped terrain pedestal. UVs, geometry, source archive
integrity and package scope can be checked with tools/validate_models_v2.py.

Remaining native pipeline
1. Review/import OBJ or GLB in Blender. Preserve named pieces, origin and UVs.
2. Calibrate scale against a locally owned Civ V landmark or civilian unit.
3. On a supported Nexus Buddy installation, import BR2 and bind the correct
   native shader/diffuse/normal/specular material. Export genuine GR2 and wrappers.
4. Map the two Caravansary eras and all three states in ArtDefine_Landmarks.
   Connect only IMPROVEMENT_RT_RELIEF_STATION; do not override native Fort art.
5. Ministry and Irrigation Works are CITY BUILDINGS. Use city art placement,
   not improvement spawning. Test that layouts remain inside the city footprint.
6. Rig Motorized Caravan wheels/body and bind or author genuine native idle,
   movement and loss animations; export unit art and FXSXML definitions. Active
   Lua-simulated trade routes still have no native map-unit rendering; this mesh
   supplies the idle map unit only unless that system is separately extended.
7. Verify flat/hill terrain, all views, small map scale, era/state transitions,
   pillage/repair, city placement, unit selection/movement, save/reload and logs.
8. Only then install runtime art, update art SQL/VFS manifests and rebuild mods.

No native art integration or executable installation was performed here. Existing
playable releases keep their working stock models. This is an authoring bundle,
not a Workshop-ready replacement package.

Reproduce with NumPy/Pillow:
python tools/build_models_v2.py
python tools/validate_models_v2.py

Native tool reference:
https://github.com/Sukritact/Nexus-Buddy-2-Blender-Scripts
''')
    with zipfile.ZipFile(ROOT/'dist/RT-Revised-Model-Sources-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,'RT-Revised-Model-Sources-v2/'+p.relative_to(OUT).as_posix())
    print('Saved '+str(len(records))+' models to '+str(OUT),flush=True)

if __name__=='__main__':main()
