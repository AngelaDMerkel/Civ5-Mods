"""Reuse the offline mesh viewer for the terrain and connection review cases."""
from pathlib import Path
import base64
import json
import math
import numpy as np
from irrigation_mesh_io import read_glb


def build_viewer(folder,cases):
    cards=[];atlas=None
    for case in cases:
        doc,(p,n,uv),blob=read_glb(folder/(case['key']+'-review.glb'))
        image=doc['bufferViews'][doc['images'][0]['bufferView']]
        png=blob[image['byteOffset']:image['byteOffset']+image['byteLength']]
        if atlas is None:atlas=png
        elif atlas!=png:raise ValueError('Review atlases differ between terrain cases')
        groups=[];first=0
        for part in case['context']:
            count=len(part['indices'])
            kind='terrain' if any(x in part['name'] for x in ('ground','terrain','river','bank_decal','authored_hill')) else 'farm'
            groups.append({'name':part['name'],'first':first,'count':count,'kind':kind});first+=count
        groups += [dict(g,first=g['first']+first,kind='irrigation') for g in case['record']['groups']]
        name=case['record']['name']
        cards.append({'name':case['key'],'label':'Diagnostic fixture: '+case['label'],'category':'authored fixture — not stock farm layout',
                      'description':case['description'],'triangles':len(p)//3,
                      'view':[math.radians(v) for v in case['view_degrees']],
                      'overlayTriangles':case['record']['triangles'],'groups':groups,
                      'bounds':[p.min(0).tolist(),p.max(0).tolist()],
                      'files':{'glb':case['key']+'-combined.glb','obj':name+'/'+name+'.obj',
                               'br2':name+'/'+name+'.br2','gr2':name+'.gr2'},
                      'data':base64.b64encode(np.column_stack((p,n,uv)).astype('<f4').tobytes()).decode()})
    # Source-only comparison deliberately omits every authored terrain/parcel.
    # Copy the actual decoded GR2 vertex buffers; never reconstruct native fields.
    terrace=next((c for c in cards if c['name']=='terrace'),None)
    if terrace:
        data=np.frombuffer(base64.b64decode(terrace['data']),dtype='<f4').reshape(-1,8)
        comparisons=[]
        for key,label,kinds,description in [
            ('native_source','Native terrace — unchanged source',{'farm'},'Original Incan Terrace Farm vertices and UVs, before game terrain contouring. No authored hill or new plots.'),
            ('native_added','Native terrace — irrigation added',{'farm','irrigation'},'The same source mesh plus separate irrigation geometry. Native fields and walls are unchanged; game contouring remains unverified.'),
            ('additions_only','Irrigation geometry only',{'irrigation'},'Only the proposed irrigation vertices. No source farm, crop texture or terrain geometry.')]:
            blocks=[];groups=[];first=0
            for g in terrace['groups']:
                if g['kind'] not in kinds:continue
                blocks.append(data[g['first']:g['first']+g['count']])
                groups.append(dict(g,first=first));first+=g['count']
            packed=np.concatenate(blocks);positions=packed[:,:3]
            files=dict(terrace['files'])
            if key=='native_source':files={'glb':'../incan_terrace_farm/incan_terrace_farm.glb'}
            elif key=='native_added':files={'glb':'terrace-source-with-irrigation.glb'}
            else:files['glb']='RT_IF_Terrace.glb'
            comparisons.append(dict(terrace,name=key,label=label,category='native source comparison',
                description=description,triangles=len(packed)//3,
                overlayTriangles=terrace['overlayTriangles'] if 'irrigation' in kinds else 0,
                groups=groups,files=files,bounds=[positions.min(0).tolist(),positions.max(0).tolist()],
                data=base64.b64encode(packed.tobytes()).decode()))
        cards=comparisons+cards
    template=Path(__file__).resolve().parent.parent/'irrigation_v3/irrigation_viewer.html'
    html=template.read_text().replace('__ASSET_DATA__',json.dumps(cards,separators=(',',':')))
    html=html.replace('__ATLAS_DATA__','data:image/png;base64,'+base64.b64encode(atlas).decode())
    html=html.replace('Irrigated Farm — Mesh Studio','Native irrigation — terrain and transitions')
    html=html.replace('Original source meshes','Civ V native art · terrain and junctions')
    html=html.replace('Irrigated farm · v3','Native farm source comparison')
    html=html.replace('</header>','</header><p style="margin:16px 30px;max-width:1000px;line-height:1.45">Source meshes before Civ V terrain contouring. The seven <strong>diagnostic fixtures are not original game farm layouts</strong>; their authored plots and terrain are not the accepted design baseline.</p>')
    html=html.replace('Mesh / assembly','Source comparison / diagnostic fixtures')
    html=html.replace('<label class="check"><input id="trees" type="checkbox" checked>Vegetation</label>',
                      '<label class="check"><input id="terrain" type="checkbox" checked>Terrain context</label><label class="check"><input id="trees" type="checkbox" checked>Farm / crop layer</label><label class="check"><input id="irrigation" type="checkbox" checked>Irrigation additions</label>')
    html=html.replace('<a id="br2">BR2</a>','<a id="br2">BR2</a><a id="gr2">GR2*</a>')
    html=html.replace('Source kit only. Native GR2 conversion, terrain fitting and game placement remain pending.',
                      'Native Terrace Farm meshes, Farm props and crop/floodplain textures. Flat parcel layouts and surrounding terrain are authored test fixtures. GR2 exports are experimental; these are not in-game captures.')
    html=html.replace('Z-up source · 2048² original atlas · No external dependencies',
                      'Level or descending water · Closed exposed outlets · Runtime adjacency pending')
    html=html.replace("${active.triangles.toLocaleString()} triangles</strong><br>${(active.triangles*3).toLocaleString()} exported vertices<br>${active.category} · one atlas material",
                      "${active.overlayTriangles.toLocaleString()} irrigation triangles</strong><br>${active.description}")
    html=html.replace("for(const ext of ['glb','obj','br2']){by(ext).href=active.name+'/'+active.name+'.'+ext;by(ext).download=active.name+'.'+ext}",
                      "for(const ext of ['glb','obj','br2','gr2']){const path=active.files[ext];by(ext).hidden=!path;if(path){by(ext).href=path;by(ext).download=path.split('/').pop()}}")
    html=html.replace("if(!by('trees').checked&&/(palm|fruit|date_bunch)/.test(g.name))return false;",
                      "if(!by('trees').checked&&g.kind==='farm')return false;if(!by('terrain').checked&&g.kind==='terrain')return false;if(!by('irrigation').checked&&g.kind==='irrigation')return false;")
    html=html.replace("['wire','clay','trees','water'].forEach", "['wire','clay','trees','water','terrain','irrigation'].forEach")
    html=html.replace('yaw=-1.25,pitch=.73','yaw=.96,pitch=.99').replace('yaw=-1.25;pitch=.73','yaw=.96;pitch=.99')
    html=html.replace('active=ASSETS[i];const data=', 'active=ASSETS[i];[yaw,pitch]=active.view;const data=')
    html=html.replace('yaw=.96;pitch=.99;zoom=1;', '[yaw,pitch]=active.view;zoom=1;')
    (folder/'index.html').write_text(html)
    (folder/'TECHNICAL_NOTES.txt').write_text('''CORRECTION: authored terrain fixtures are not the accepted native-art baseline.
The default comparisons show unchanged native source, source plus irrigation,
and irrigation alone. No authored support terrain enters those comparisons.
Source geometry is shown before Civ V terrain contouring, not in-game.

Seven diagnostic terrain fitting cases using real Civ V farm assets and textures.
Terrace and ordinary Farm prop vertices/UVs are kept unchanged. The flat crop
textures are native; their parcel placement and terrain context are authored
fixtures, not extracted engine terrain geometry or an in-game capture.

Prominence: terrace carrier width 0.90, up from 0.44 native authoring units.
Flat carriers are 1.15 units, with one 0.82 branch. Taller bank relief improves
readability without adding a lattice of tiny channels. The enlarged aqueduct
uses the existing source design. Most crop boundaries stay dry.

Connected cases show terrace-to-flat descent, river/floodplain-to-desert handoff,
and a mountain intake with a descending aqueduct to the native terraces.
Connections are local mesh/height contracts, not dynamic game art selection.

GLB downloads include local native reference art and must not be redistributed.
OBJ/BR2/GR2 exports are original irrigation additions. GR2* is experimental:
geometry and water checks do not prove game loading, shaders or terrain warping.
''')
