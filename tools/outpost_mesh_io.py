"""Portable source mesh exports and honest renders of the exported triangles."""
from pathlib import Path
import html
import io
import json
import math
import struct
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from build_models import norm
from outpost_surface_bake import bake

MATERIALS={
 'stone':(149,146,129),'limestone':(210,195,161),'brick':(151,90,60),
 'timber':(100,70,43),'woodlight':(148,112,70),
 'thatch':(181,148,80),'slate':(68,80,86),'tile':(155,78,50),
 'copper':(101,132,112),'concrete':(168,169,157),'olive':(93,103,70),
 'steel':(73,80,79),'glass':(40,60,66),'blue':(69,102,135),
 'charcoal':(45,46,41),'sandbag':(166,150,110),'roofmetal':(90,101,104),
 'solar':(40,69,95),'rubble':(128,117,99),'plaster':(197,187,157),
 'gabion':(140,132,108),'soil':(137,119,85),'reserved_a':(115,110,98),
 'reserved_b':(128,128,128),'reserved_c':(180,180,180)
}
NAMES=list(MATERIALS)
GRID=5;CELL=256;GUTTER=12


def save_dds_mips(image,path):
    """Opaque legacy DXT1 with a complete mip chain for distance filtering."""
    level=image.convert('RGB');payload=[];header=None
    while True:
        stream=io.BytesIO();level.save(stream,format='DDS',pixel_format='DXT1')
        raw=stream.getvalue();assert raw[84:88]==b'DXT1'
        expected=max(1,(level.width+3)//4)*max(1,(level.height+3)//4)*8
        assert len(raw[128:])==expected
        if header is None:header=bytearray(raw[:128])
        payload.append(raw[128:])
        if level.size==(1,1):break
        level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS)
    struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,20,len(payload[0]))
    struct.pack_into('<I',header,28,len(payload))
    struct.pack_into('<I',header,108,0x1000|0x8|0x400000)
    path.write_bytes(header+b''.join(payload))


def make_atlas(out):
    source=Path(__file__).resolve().parents[1]/'shared/art/outpost-era-concepts-v1/material-library-v1.png'
    with Image.open(source) as image:
        atlas=image.convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
    atlas.save(out/'RO_Era_Diffuse.png')
    save_dds_mips(atlas,out/'RO_Era_Diffuse.dds')
    Image.new('RGBA',(4,4),(128,128,255,255)).save(out/'RO_Era_FlatNormal.dds')
    Image.new('RGBA',(4,4),(0,0,0,255)).save(out/'RO_Era_BlackSpec.dds')
    return atlas


def face_uv(p,n,material):
    """Planar coordinates shared across coplanar triangles, with atlas gutters."""
    axis=int(np.argmax(np.abs(n)))
    axes=([1,2],[0,2],[0,1])[axis]
    # All source coordinates fit a 12-unit square, including vertical masts.
    local=np.stack(((p[:,axes[0]]+5)/12,(p[:,axes[1]]+(0 if axes[1]==2 else 5))/12),axis=1)
    local=np.clip(local,.001,.999)
    index=NAMES.index(material);cell=np.array((index%GRID,index//GRID))
    uv=(cell+GUTTER/CELL+local*(1-2*GUTTER/CELL))/GRID
    # Source/OBJ UVs have the origin at the bottom left; image/glTF at the top.
    uv[:,1]=1-uv[:,1]
    return uv


def attributes(mesh):
    p=np.vstack([p for p,n,mat,part in mesh.faces])
    n=np.vstack([np.tile(n,(3,1)) for p,n,mat,part in mesh.faces])
    uv=np.vstack([face_uv(p,n,mat) for p,n,mat,part in mesh.faces])
    return p,n,uv


def export(mesh,out,atlas):
    folder=out/mesh.name;folder.mkdir(parents=True,exist_ok=True)
    positions,normals,uvs=attributes(mesh)
    diffuse,uvs,bake_info=bake(mesh,atlas)
    diffuse_name=mesh.name+'_diffuse'
    diffuse.save(folder/(diffuse_name+'.png'))
    save_dds_mips(diffuse,folder/(diffuse_name+'.dds'))
    mesh.review_texture=diffuse;mesh.review_uvs=uvs
    lines=['# Original outpost source mesh. Z up. No game-native assets.',f'mtllib {mesh.name}.mtl']
    for p in positions:lines.append('v '+' '.join(f'{x:.7f}' for x in p))
    for t in uvs:lines.append('vt '+' '.join(f'{x:.8f}' for x in t))
    for n in normals:lines.append('vn '+' '.join(f'{x:.8f}' for x in n))
    last=None
    lines.append('usemtl RO_Era_Diffuse')
    for i,(_,_,_,part) in enumerate(mesh.faces):
        if part!=last:lines.append('g '+part);last=part
        lines.append('f '+' '.join(f'{j}/{j}/{j}' for j in range(i*3+1,i*3+4)))
    (folder/(mesh.name+'.obj')).write_text('\n'.join(lines)+'\n')
    (folder/(mesh.name+'.mtl')).write_text('newmtl RO_Era_Diffuse\nKa 0.15 0.15 0.15\nKd 1 1 1\nKs 0 0 0\nNs 1\nd 1\nillum 1\nmap_Kd '+diffuse_name+'.png\n')
    br=['// Original rigid outpost mesh; native conversion not yet validated','skeleton',
        '0 "World" -1 0 0 0 0 0 0 1 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1',
        'meshes:1',f'mesh:"{mesh.name}"','vertices']
    # Tangents follow the actual UV derivatives, not an arbitrary triangle edge.
    for face_index,(p,n,mat,part) in enumerate(mesh.faces):
        uv=uvs[face_index*3:face_index*3+3].copy();uv[:,1]=1-uv[:,1]
        e1,e2=p[1]-p[0],p[2]-p[0];d1,d2=uv[1]-uv[0],uv[2]-uv[0]
        det=d1[0]*d2[1]-d1[1]*d2[0]
        assert abs(det)>1e-12,(mesh.name,part,'degenerate UV')
        tangent=norm((e1*d2[1]-e2*d1[1])/det)
        bitangent=norm((-e1*d2[0]+e2*d1[0])/det)
        # Orthogonalize the bitangent; projected UV axes can be skewed.
        sign=1 if np.dot(np.cross(n,tangent),bitangent)>=0 else -1
        bitangent=norm(np.cross(n,tangent))*sign
        for point,t in zip(p,uv):
            fields=list(point)+list(n)+list(t)+[0,0,0,0,255,0,0,0]+list(tangent)+list(bitangent)
            br.append(' '.join(str(int(v)) if 8<=j<16 else f'{v:.8f}' for j,v in enumerate(fields)))
    br+=['triangles']+[f'{i} {i+1} {i+2}' for i in range(0,len(positions),3)]+['end']
    (folder/(mesh.name+'.br2')).write_text('\n'.join(br)+'\n')
    blob=bytearray();views=[];accessors=[]
    def add(data):
        blob.extend(b'\0'*((-len(blob))%4));offset=len(blob);blob.extend(data)
        views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data)})
        return len(views)-1
    def acc(data,kind):
        data=np.asarray(data,dtype='<f4');view=add(data.tobytes())
        accessors.append({'bufferView':view,'componentType':5126,'count':len(data),'type':kind,
                          'min':data.min(axis=0).tolist(),'max':data.max(axis=0).tolist()})
        return len(accessors)-1
    pi=acc(positions,'VEC3');ni=acc(normals,'VEC3')
    guv=uvs.copy();guv[:,1]=1-guv[:,1];ti=acc(guv,'VEC2')
    image=add((folder/(diffuse_name+'.png')).read_bytes())
    gltf={'asset':{'version':'2.0','generator':'Resource Outposts era mesh builder'},
          'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':accessors,
          'images':[{'bufferView':image,'mimeType':'image/png'}],
          'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],
          'textures':[{'source':0,'sampler':0}],
          'materials':[{'name':'RO_Era_Diffuse','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1}}],
          'meshes':[{'name':mesh.name,'primitives':[{'attributes':{'POSITION':pi,'NORMAL':ni,'TEXCOORD_0':ti},'material':0}]}],
          'nodes':[{'mesh':0,'rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)]}],'scenes':[{'nodes':[0]}],'scene':0}
    encoded=json.dumps(gltf,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
    blob.extend(b'\0'*((-len(blob))%4))
    glb=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(blob))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(blob),0x004e4942)+blob
    (folder/(mesh.name+'.glb')).write_bytes(glb)
    return {'name':mesh.name,'triangles':len(mesh.faces),'vertices':len(positions),
            'bounds_z_up':[positions.min(axis=0).tolist(),positions.max(axis=0).tolist()],
            'parts':sorted(set(part for p,n,mat,part in mesh.faces)),
            'files':[mesh.name+'/'+mesh.name+s for s in ('.obj','.mtl','.br2','.glb')],
            'diffuse':mesh.name+'/'+diffuse_name+'.png',
            'diffuse_dds':mesh.name+'/'+diffuse_name+'.dds',
            'texture_bake':bake_info,
            'native_status':'BR2 import and GR2 conversion not executed'}


def render(mesh,atlas,width=760,height=650,azimuth=0):
    # Actual textured triangles, fixed view and scale across ALL eras/states.
    ss=2;w=width*ss;h=height*ss
    pixels=np.full((h,w,3),(242,240,232),dtype=np.uint8)
    depth=np.full((h,w),-np.inf);tex=np.asarray(mesh.review_texture)
    angle=math.radians(azimuth)
    camera=norm((.7*math.cos(angle)+math.sin(angle),.7*math.sin(angle)-math.cos(angle),.85))
    right=norm(np.cross((0,0,1),camera));up=norm(np.cross(camera,right))
    center=np.array((0,0,2.0));scale=width/12.8*ss;sun=norm((-.5,-.65,1))
    for face_index,(p,n,mat,part) in enumerate(mesh.faces):
        if np.dot(n,camera)<=0:continue
        coords=np.array([(w/2+np.dot(v-center,right)*scale,h*.54-np.dot(v-center,up)*scale) for v in p])
        lo=np.maximum(np.floor(coords.min(axis=0)).astype(int),(0,0));hi=np.minimum(np.ceil(coords.max(axis=0)).astype(int),(w-1,h-1))
        if np.any(hi<lo):continue
        x0,y0=coords[0];x1,y1=coords[1];x2,y2=coords[2]
        den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(den)<1e-10:continue
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];xx=xx+.5;yy=yy+.5
        a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
        b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;c=1-a-b
        zz=p@camera;z=a*zz[0]+b*zz[1]+c*zz[2]
        region=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        visible=(a>=-1e-8)&(b>=-1e-8)&(c>=-1e-8)&(z>region)
        if not np.any(visible):continue
        uv=mesh.review_uvs[face_index*3:face_index*3+3]
        uu=(a*uv[0,0]+b*uv[1,0]+c*uv[2,0])*tex.shape[1]
        vv=(1-(a*uv[0,1]+b*uv[1,1]+c*uv[2,1]))*tex.shape[0]
        # Match the GLB's linear filtering instead of nearest-neighbor texels.
        u=np.clip(uu-.5,0,tex.shape[1]-1);v=np.clip(vv-.5,0,tex.shape[0]-1)
        x=np.floor(u).astype(int);y=np.floor(v).astype(int)
        nx=np.minimum(x+1,tex.shape[1]-1);ny=np.minimum(y+1,tex.shape[0]-1)
        dx=(u-x)[...,None];dy=(v-y)[...,None]
        color=(tex[y,x]*(1-dx)+tex[y,nx]*dx)*(1-dy)+(tex[ny,x]*(1-dx)+tex[ny,nx]*dx)*dy
        light=.58+.42*max(0,np.dot(n,sun))
        color=np.clip(color.astype(float)*light,0,255).astype('uint8')
        region[visible]=z[visible];pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][visible]=color[visible]
    return Image.fromarray(pixels).resize((width,height),Image.Resampling.LANCZOS)


def make_gallery(out,records,approval):
    constructed=[r for r in records if r['state']=='Constructed']
    sheet=Image.new('RGB',(1520,2940),(242,240,232));draw=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',25)
    except OSError:font=ImageFont.load_default()
    for i,r in enumerate(constructed):
        x=i%2*760;y=i//2*735
        draw.text((x+30,y+15),r['era']+' — '+r['design'],font=font,fill='#343d32')
        with Image.open(out/r['preview']) as preview:sheet.paste(preview,(x,y+48))
        draw.text((x+30,y+698),str(r['triangles'])+' triangles · actual source mesh',font=font,fill='#626959')
    sheet.save(out/'approved-era-meshes-preview.png')
    notes={
        'Ancient':'Angled palisade, braced timber tower, tiered thatch roof, open supply shelter and sagging entrance cloth.',
        'Classical':'Projecting gate towers, thick parapets, raised wall walks with stairs, rear tiled barracks and framed openings.',
        'Medieval':'Crenellated walls with angled rear corners, taller gate towers, a true entrance arch, timber gate gallery and open loading bay.',
        'Renaissance':'Tapered enclosure, projecting pentagonal bastions with parapets, a dominant octagonal tower and side lean-to.',
        'Industrial':'Octagonal blockhouses with belt courses and metal roof seams, braced curtain walls, rear store and loading canopy.',
        'Modern':'Splayed perimeter, tapered concrete watchtower, roof parapet, lattice radio mast and barrel-roofed shelter.',
        'Atomic':'Tapered control tower, railed radar platform, concave radar frame, curved equipment shelter and fenced perimeter.',
        'Information':'Flared glazed observation cab, equipment platform, lattice sensor mast, inclined solar panels and draped supply canopy.'}
    art_dir=out/'approved-art';art_dir.mkdir(exist_ok=True)
    rows=[]
    for r in constructed:
        source=Path(__file__).resolve().parents[1]/'shared/art/outpost-era-concepts-v1'/(r['concept']+'.png')
        concept='approved-art/'+source.name;shutil.copyfile(source,out/concept)
        def card(v):
            return '<figure><a href="'+v['preview']+'"><img src="'+v['preview']+'" alt="'+html.escape(v['era']+' '+v['state'])+'"></a><figcaption>'+v['state']+' · '+str(v['triangles'])+' triangles<br><a href="'+v['name']+'/'+v['name']+'.glb">GLB</a> · <a href="'+v['name']+'/'+v['name']+'.obj">OBJ</a> · <a href="'+v['name']+'/'+v['name']+'.br2">BR2</a></figcaption></figure>'
        reference='<figure class="reference"><a href="'+concept+'"><img src="'+concept+'" alt="'+r['era']+' approved artwork"></a><figcaption>Approved artwork · '+r['concept']+'</figcaption></figure>'
        states=''.join(card(v) for v in records if v['era']==r['era'] and v['state']!='Constructed')
        rows.append('<section id="'+r['era'].lower()+'"><h2>'+r['era']+' · '+html.escape(r['design'])+'</h2><p>'+notes[r['era']]+'</p><div class="comparison">'+reference+card(r)+'</div><p><a href="'+r['reverse_preview']+'">Reverse view of the mesh</a></p><details><summary>Construction and pillaged models</summary><div class="states">'+states+'</div></details></section>')
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Approved Outpost Architecture</title>\n<style>body{margin:0;background:#f2f0e8;color:#303a30;font:16px/1.5 system-ui}main{max-width:1400px;padding:36px;margin:auto}h1,h2{font-family:Georgia,serif;font-weight:400}h1{font-size:44px;line-height:1.08}h2{font-size:27px;margin:0}section{padding:34px 0;border-top:1px solid #c9cbbb}.comparison,.states{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}figure{margin:0;border:1px solid #d2d6c8;background:#fbfaf6}.comparison figure>a{height:440px;display:flex;align-items:center;justify-content:center}img{width:100%;display:block}.comparison img{max-height:100%;object-fit:contain}.map-scale figure>a{height:240px}.map-scale img{width:200px;max-width:100%;margin:auto}button{font:inherit;background:#365642;color:white;border:0;padding:9px 16px;margin:5px 8px 5px 0;cursor:pointer;border-radius:3px}figcaption{padding:15px;font-size:14px}a{color:#34634b}p{max-width:950px}summary{cursor:pointer;margin:12px 0}nav{display:flex;gap:8px 16px;flex-wrap:wrap;margin:25px 0}small{color:#606b5b}.tag{text-transform:uppercase;letter-spacing:.12em;font-size:12px;color:#62745a}@media(max-width:750px){main{padding:20px}h1{font-size:35px}.comparison,.states{gap:8px}.comparison figure>a{height:225px}figcaption{padding:9px;font-size:12px}.map-scale figure>a{height:200px}section>p{font-size:14px}}</style><main><p class="tag">Geometry revision 2 · Approved 9 October 2026</p><h1>From approved artwork<br>to outpost geometry</h1><p>The approved concept and the revised source mesh are shown together for each era. The new geometry restores architectural massing, projecting defenses, roof profiles, gatehouses and supporting structures. The concept artwork is unchanged.</p><p><small>Mesh previews render the actual exported triangles and baked textures. Terrain bases and vegetation in the artwork are not part of these meshes. Native GR2 conversion and in-game scale, materials and era switching remain pending.</small></p><div><button onclick="document.body.classList.remove(\'map-scale\')">Close-up</button><button onclick="document.body.classList.add(\'map-scale\')">Small-scale check (~200 px)</button></div><nav>'+''.join('<a href="#'+r['era'].lower()+'">'+r['era']+'</a>' for r in constructed)+'</nav>'+''.join(rows)+'<p><a href="models.json">Mesh manifest</a> · <a href="CONVERSION.txt">Conversion and integration notes</a> · <a href="approved-era-meshes-preview.png">All eight constructed models</a></p><p><small>All garrison centers remain clear. No road or supply connection is required. The playable mod still uses its existing graphics.</small></p></main></html>'
    (out/'index.html').write_text(page)
    (out/'CONVERSION.txt').write_text('''RESOURCE OUTPOSTS — ERA SOURCE MESHES, ARCHITECTURAL REVISION 2

Approved 9 October 2026: Ancient A, Classical B, Medieval B, Renaissance A,
Industrial B, Modern A, Atomic A, Information A. Supersedes the earlier generic
RO_ResourceOutpost source concept; does not change other structures or releases.

Architectural revision 2 restores the distinctive approved compositions:
angled defenses, projecting towers/bastions, thick walls, stairs and walks,
proper gatehouses, layered roof silhouettes and open supply structures.
Approved concept PNGs are included unchanged for direct visual comparison.
The user approved architectural revision 2 on 9 October 2026.
This records design approval; native conversion and game checks remain pending.

24 original source meshes: 8 eras x Constructed/UnderConstruction/Pillaged.
OBJ/MTL: editable geometry, named component groups and atlas UVs.
GLB: textured portable preview with embedded atlas (Y up).
BR2: static geometry with one World bone (Z up), 255/255 rigid weights.
The material library is original generated artwork, guided by locally inspected
stock Fort_MID_DIFF, Fort_MOD_DIFF and Citadel_Anc_DIFF. No game assets are copied.
Each model has a dedicated 1024x1024 UV atlas with repeated material detail and
ray-sampled cavity shading plus ground contact shading baked into its diffuse.
DXT1 DDS exports include every mip level down to 1x1. PNG/GLB are uncompressed
source previews; native DDS compression should be checked during conversion.
Normal/specular DDS inputs are placeholders: stock landmark wrappers use
SREF/decal textures, so inspect the actual template shader slots rather than
assuming a modern PBR material mapping.

Models have no tile-shaped terrain pedestal, road, resource-specific machine,
animation or off-tile wire. Source units are arbitrary; the origin is centered
on the garrison. The visible blue cloth is a material accent, not native dynamic
player-color support. Preserving the open center does not establish actual
unit/model scale or collision behavior in the game.

PENDING NATIVE PRODUCTION
1. Inspect/refine OBJ or GLB in a 3D editor. Calibrate footprint and height using
   a locally owned Civ V improvement reference. Check material detail at map zoom,
   UV seams, roof profiles, terrain transitions and shadow response. Exact Civ V
   style parity has not been established by these source previews.
2. Import BR2 with Nexus Buddy 2 on a compatible Windows setup. Bind materials,
   verify orientation, normals, UVs and root transforms, then produce real GR2.
   BR2 syntax/geometry checks are not a successful Nexus Buddy import test.
3. Create matching FXSXML wrappers for each of the 24 native meshes. Validate
   construction/pillage/repair and every texture in Nexus and a BNW game.
4. Add unique Resource Outposts art definitions inside mods/resource-outposts/src/.
   Do not replace stock Fort art globally or pass OBJ/GLB/BR2 to ArtDefines.
5. Implement and verify model selection by the claiming civilization's era,
   including neutral plots, capture, annexation, load and era advancement.
   Native art Era strings alone have not been proven to cover all eight player
   eras on neutral plots. Do not assume that the player's ledger owner is the
   engine's territorial owner or that every Era string is accepted as an art era.
6. Preserve resources, upkeep, pillage state, garrison and worker progress when
   visuals refresh. No road checks. Optional Realistic Terrain remains shelter
   only; no dependency on its graphics, Lua context or installation.
7. Test against native BNW before registering assets or releasing an updated ZIP.

The build Mac has no Blender/Nexus Buddy/Windows conversion runtime. Mesh
generation and portable export are complete; GR2 conversion and gameplay
integration are outstanding. No native runtime model is claimed in this bundle.

REPRODUCE
python tools/build_outpost_era_models.py    (NumPy and Pillow)
python tools/validate_outpost_era_models.py (NumPy and Pillow)

FORMAT/TOOL REFERENCES
https://github.com/deliverator23/Civilization-Blender-Scripts/blob/master/Blender-2.7-Addons/io_export_br2.py
https://forums.civfanatics.com/threads/nexus-buddy-2-granny-editor-for-civ-5.496855/
''')
