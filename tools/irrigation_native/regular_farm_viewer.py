"""Native regular farm comparison; deliberately omit fabricated crop parcels."""
from pathlib import Path
import base64
import json
import numpy as np
from irrigation_mesh_io import read_glb
from build_review_library import BANNER


def build_viewer(folder, views):
    cards=[]; atlas=None
    for source,record,scene in views:
        name=record['name']
        doc,(p,n,uv),blob=read_glb(folder/(name+'-review.glb'))
        image=doc['bufferViews'][doc['images'][0]['bufferView']]
        png=blob[image['byteOffset']:image['byteOffset']+image['byteLength']]
        if atlas is None: atlas=png
        elif atlas!=png: raise ValueError('Regular review texture atlases differ')
        # The added group follows the native decal and building triangles.
        base_count=len(p)-record['triangles']*3
        groups=[{'name':'native_farmstead','first':0,'count':base_count,'kind':'farm'}]
        groups += [dict(g,first=g['first']+base_count,kind='irrigation') for g in record['groups']]
        cards.append({'name':name,'label':source['name'].replace('_',' ').title()+' + irrigation',
                      'category':'actual regular farm source + candidate irrigation',
                      'triangles':len(p)//3,'overlayTriangles':record['triangles'],
                      'bounds':[p.min(0).tolist(),p.max(0).tolist()], 'groups':groups,
                      'files':{'glb':name+'.glb','gr2':name+'.gr2'},
                      'data':base64.b64encode(np.column_stack((p,n,uv)).astype('<f4').tobytes()).decode()})
    html=(Path(__file__).resolve().parent.parent/'irrigation_v3/irrigation_viewer.html').read_text()
    html=html.replace('__ASSET_DATA__',json.dumps(cards,separators=(',',':')))
    html=html.replace('__ATLAS_DATA__','data:image/png;base64,'+base64.b64encode(atlas).decode())
    html=html.replace('Irrigated Farm — Mesh Studio','Regular Civ V farm — irrigation candidate')
    html=html.replace('Original source meshes','Original regular Farm1/2/3 artwork')
    html=html.replace('Irrigated farm · v3','Regular farm + irrigation')
    html=html.replace('</header>','</header><p style="margin:16px 30px;max-width:1000px">Actual regular farm buildings and ground decals. <strong>Civ V supplies the surrounding crop fields through its FARM layout handler; those fields are absent from this asset preview.</strong> Turn off irrigation to inspect the original farmstead. <a href="../terrain-review/index.html">Terrace comparison and earlier diagnostics</a>.</p>')
    html=html.replace('>Vegetation</label>','>Irrigation additions</label>')
    html=html.replace('<a id="obj">OBJ</a><a id="br2">BR2</a>','<a id="gr2">GR2 candidate</a>')
    html=html.replace('Source kit only. Native GR2 conversion, terrain fitting and game placement remain pending.',
                      'Native-derived local test candidates. Stock crop textures and FARM layout are retained in the proposed bindings. Actual field seams, terrain contouring and source connections need game testing.')
    html=html.replace('Z-up source · 2048² original atlas · No external dependencies',
                      'Original buildings and decals · Sparse added channels · Native test pending')
    html=html.replace("if(!by('trees').checked&&/(palm|fruit|date_bunch)/.test(g.name))return false;",
                      "if(!by('trees').checked&&g.kind==='irrigation')return false;")
    html=html.replace("for(const ext of ['glb','obj','br2']){by(ext).href=active.name+'/'+active.name+'.'+ext;by(ext).download=active.name+'.'+ext}",
                      "for(const ext of ['glb','gr2']){by(ext).href=active.files[ext];by(ext).download=active.files[ext]}")
    html=html.replace('yaw=-1.25,pitch=.73','yaw=.96,pitch=1.13').replace('yaw=-1.25;pitch=.73','yaw=.96;pitch=1.13')
    if (folder.parent/'library/catalog.json').is_file():
        html=html.replace('<body>','<body>'+BANNER,1)
    (folder/'index.html').write_text(html)
    (folder/'TECHNICAL_NOTES.txt').write_text('''Regular resource-free farms, not wheat Farm props.
Source: installed Medieval_Farm1/2/3 and Modern_Farm1/2/3 GR2 + FXSXML.
Original farmstead decals, buildings, materials, UVs and construction states retained.
Original irrigation geometry is appended only to the constructed building mesh.
Wet and dry candidates preserve the stock half-built and pillaged states.
The proposed art rows retain FARM, TerrainContour=1, native era/state/scale values.
No crop texture, farm_types.xml, procedural parcel or terrain replacement is provided.
The native engine must select and place the ordinary fields on desert.
This offline view does NOT show a complete desert tile or verified parcel seams.
Upstream socket is not runtime-connected; exposed downstream ends are capped.
Derived native candidates are local references and must not be redistributed.
Native loading, materials, construction-state selection and game terrain deformation
remain untested. The existing production Farm fallback is unchanged.
''')
