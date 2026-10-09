"""Textured source exports for the revised models. NumPy/Pillow only."""
import json
import math
import struct
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from build_models import norm
from model_surface_v2 import bake
PREVIOUS={
 'stone':(149,146,129),'limestone':(210,195,161),'brick':(151,90,60),
 'timber':(100,70,43),'woodlight':(148,112,70),'thatch':(181,148,80),
 'slate':(68,80,86),'tile':(155,78,50),'copper':(101,132,112),
 'concrete':(168,169,157),'olive':(93,103,70),'steel':(73,80,79),
 'glass':(40,60,66),'blue':(69,102,135),'charcoal':(45,46,41),
 'sandbag':(166,150,110),'roofmetal':(90,101,104),'solar':(40,69,95),
 'rubble':(128,117,99),'plaster':(197,187,157),'gabion':(140,132,108),
 'soil':(137,119,85)}

MATERIALS=dict(PREVIOUS)
MATERIALS.update(sandstone=(172,156,120),ochre_plaster=(157,114,80),water=(54,89,81),
    canvas=(150,137,101),rope=(110,96,70),brass=(138,119,70),paving=(135,128,109),
    dry_soil=(146,130,97),crop=(107,120,64),dry_crop=(144,125,75),
    rubber=(43,43,39),truckpaint=(98,109,94))
MATERIALS.update(limestone=(182,173,143),stone=(128,129,113),brick=(132,96,73),
    tile=(134,90,65),concrete=(139,140,128),glass=(40,58,61),blue=(61,83,93),
    plaster=(172,161,133),soil=(105,99,71),timber=(91,77,55))
# Approved palette, translated into subdued diffuse materials for the map.
# Smooth architectural planes carry the silhouette; masonry is fine/subtle.
MATERIALS.update(sandstone=(187,168,127),limestone=(216,199,162),
    ochre_plaster=(171,111,74),smooth_stone=(208,190,147),
    goldstone=(184,135,70),goldcloth=(187,140,66),banner=(117,40,32),
    patina=(67,88,78),brass=(151,125,64),canvas=(162,148,112))
NAMES=list(MATERIALS);GRID=7;CELL=256;GUTTER=12


def make_atlas(out):
    atlas=Image.new('RGB',(GRID*CELL,GRID*CELL));rng=np.random.default_rng(61009)
    for index,(name,color) in enumerate(MATERIALS.items()):
        small=Image.fromarray(rng.integers(85,170,(20,20),dtype=np.uint8)).resize((CELL,CELL),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(4))
        broad=np.asarray(small).astype(float)-128
        fine=rng.normal(0,1.3,(CELL,CELL))
        grain=(broad*.28+fine)[:,:,None]
        data=np.clip(np.array(color)[None,None,:]+grain,0,255).astype('uint8')
        tile=Image.fromarray(data);d=ImageDraw.Draw(tile)
        dark=tuple(round(v*.85) for v in color);light=tuple(min(255,round(v*1.075)) for v in color)
        if name in ('stone','sandstone','limestone','brick','rubble','paving'):
            row=4 if name=='brick' else 6;block=12 if name=='brick' else 17
            dark=tuple(round(v*(.86 if name in ('brick','rubble') else .95)) for v in color)
            light=tuple(min(255,round(v*1.025)) for v in color)
            for y in range(0,CELL,row):
                d.line((0,y,CELL,y),fill=dark)
                for x in range(-(y//row%2)*block//2,CELL,block):
                    d.line((x,y,x,y+row),fill=dark)
                    if row>5:d.line((x+2,y+1,x+block-3,y+1),fill=light)
        elif name in ('timber','woodlight','thatch'):
            step=11 if name!='thatch' else 3
            for x in range(0,CELL,step):
                d.line((x,0,x,CELL),fill=dark)
                for y in range(0,CELL,24):
                    dx=int(rng.integers(1,6));d.line((x+dx,y,x+dx-1,y+int(rng.integers(8,22))),fill=light)
        elif name in ('tile','slate'):
            for y in range(0,CELL,7):
                d.line((0,y,CELL,y),fill=dark)
                for x in range(-(y//7%2)*5,CELL,10):d.line((x,y,x,y+7),fill=dark)
        elif name in ('roofmetal','olive','patina'):
            for x in range(0,CELL,11):
                d.line((x,0,x,CELL),fill=dark);d.line((x+2,0,x+2,CELL),fill=light)
        elif name=='water':
            for y in range(1,CELL,5):
                pts=[(x,y+math.sin(x*.14+y)*1.1) for x in range(0,CELL,3)]
                d.line(pts,fill=(64,99,90),width=1)
        elif name=='solar':
            for x in range(0,CELL,22):d.line((x,0,x,CELL),fill=(96,116,128))
            for y in range(0,CELL,25):d.line((0,y,CELL,y),fill=(96,116,128))
        elif name=='gabion':
            for x in range(0,CELL,8):d.line((x,0,x,CELL),fill=dark)
            for y in range(0,CELL,8):d.line((0,y,CELL,y),fill=dark)
        elif name in ('canvas','rope','goldcloth','banner'):
            for x in range(0,CELL,3):d.line((x,0,x,CELL),fill=tuple(int(c*.98) for c in color))
            for y in range(0,CELL,5):d.line((0,y,CELL,y),fill=tuple(int(c*1.02) for c in color))
        elif name=='rubber':
            for y in range(0,CELL,7):d.line((0,y,CELL,y),fill=(32,33,30),width=2)
        # Light stains are in the diffuse texture, not pasted over the render.
        stain=np.asarray(tile).astype(float)
        if name not in ('glass','water','solar','rubber'):
            stain*=np.clip(1+broad[:,:,None]*.0015,.92,1.06)
        tile=Image.fromarray(np.uint8(np.clip(stain,0,255)))
        # Replicate edge pixels as filtering gutters.
        inner=tile.crop((GUTTER,GUTTER,CELL-GUTTER,CELL-GUTTER))
        tile.paste(inner,(GUTTER,GUTTER))
        tile.paste(inner.crop((0,0,1,inner.height)).resize((GUTTER,inner.height)),(0,GUTTER))
        tile.paste(inner.crop((inner.width-1,0,inner.width,inner.height)).resize((GUTTER,inner.height)),(CELL-GUTTER,GUTTER))
        tile.paste(tile.crop((0,GUTTER,CELL,GUTTER+1)).resize((CELL,GUTTER)),(0,0))
        tile.paste(tile.crop((0,CELL-GUTTER-1,CELL,CELL-GUTTER)).resize((CELL,GUTTER)),(0,CELL-GUTTER))
        atlas.paste(tile,((index%GRID)*CELL,(index//GRID)*CELL))
    atlas=atlas.resize((2048,2048),Image.Resampling.BICUBIC)
    atlas.save(out/'RT_Surface.png');atlas.convert('RGBA').save(out/'RT_Surface.dds')
    luminance=np.asarray(atlas.convert('L')).astype(float)/255
    dy,dx=np.gradient(luminance);normal=np.stack((-dx*2.4,dy*2.4,np.ones_like(dx)),axis=2)
    normal/=np.linalg.norm(normal,axis=2)[:,:,None]
    normal=Image.fromarray(np.uint8(np.clip((normal*.5+.5)*255,0,255)))
    normal.save(out/'RT_Surface_Normal.png');normal.convert('RGBA').save(out/'RT_Surface_Normal.dds')
    spec=Image.new('RGB',atlas.size,(12,12,12));d=ImageDraw.Draw(spec)
    for i,name in enumerate(NAMES):
        value=65 if name in ('water','glass','brass','steel') else (30 if name in ('truckpaint','roofmetal') else 12)
        x=(i%GRID)*2048/GRID;y=(i//GRID)*2048/GRID;d.rectangle((x,y,x+2048/GRID,y+2048/GRID),fill=(value,)*3)
    spec.save(out/'RT_Surface_Specular.png');spec.convert('RGBA').save(out/'RT_Surface_Specular.dds')
    return atlas


def face_uv(p,n,material):
    axis=int(np.argmax(np.abs(n)));axes=([1,2],[0,2],[0,1])[axis]
    local=np.stack(((p[:,axes[0]]+5)/12,(p[:,axes[1]]+(0 if axes[1]==2 else 5))/12),axis=1)
    assert local.min()>=0 and local.max()<1,(material,local)
    index=NAMES.index(material);cell=np.array((index%GRID,index//GRID))
    uv=(cell+GUTTER/CELL+local*(1-2*GUTTER/CELL))/GRID;uv[:,1]=1-uv[:,1]
    return uv


def attributes(mesh):
    p=np.vstack([p for p,n,mat,part in mesh.faces])
    n=np.vstack([np.tile(n,(3,1)) for p,n,mat,part in mesh.faces])
    uv=getattr(mesh,'baked_uv',None)
    if uv is None:uv=np.vstack([face_uv(p,n,mat) for p,n,mat,part in mesh.faces])
    return p,n,uv


def save_dds_mips(image,path,compression='DXT1'):
    level=image.convert('RGB');payload=[];header=None
    while True:
        stream=io.BytesIO();level.save(stream,format='DDS',pixel_format=compression)
        raw=stream.getvalue()
        if header is None:header=bytearray(raw[:128])
        payload.append(raw[128:])
        if level.size==(1,1):break
        level=level.resize((max(1,level.width//2),max(1,level.height//2)),Image.Resampling.LANCZOS)
    struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,20,len(payload[0]));struct.pack_into('<I',header,28,len(payload))
    struct.pack_into('<I',header,108,0x1000|0x8|0x400000)
    path.write_bytes(header+b''.join(payload))


def export(mesh,out,atlas):
    folder=out/mesh.name;folder.mkdir(parents=True,exist_ok=True)
    diffuse,normal,spec,mesh.baked_uv,bake_info=bake(mesh,atlas,NAMES,GRID)
    mesh.baked_diffuse=diffuse
    for name,img in [('Diffuse',diffuse),('Normal',normal),('Specular',spec)]:
        img.save(folder/(mesh.name+'_'+name+'.png'))
        # Native normal swizzling is still a conversion-time concern. Keep its
        # PNG/uncompressed DDS vector data intact; color maps use BC1 mipmaps.
        if name=='Normal':img.convert('RGBA').save(folder/(mesh.name+'_'+name+'.dds'))
        else:save_dds_mips(img,folder/(mesh.name+'_'+name+'.dds'))
    positions,normals,uvs=attributes(mesh)
    lines=['# Original revised source mesh. Z up. No game-native assets.',f'mtllib {mesh.name}.mtl']
    for p in positions:lines.append('v '+' '.join(f'{x:.7f}' for x in p))
    for t in uvs:lines.append('vt '+' '.join(f'{x:.8f}' for x in t))
    for n in normals:lines.append('vn '+' '.join(f'{x:.8f}' for x in n))
    last=None
    lines.append('usemtl RT_Surface')
    for i,(_,_,_,part) in enumerate(mesh.faces):
        if part!=last:lines.append('g '+part);last=part
        lines.append('f '+' '.join(f'{j}/{j}/{j}' for j in range(i*3+1,i*3+4)))
    (folder/(mesh.name+'.obj')).write_text('\n'.join(lines)+'\n')
    (folder/(mesh.name+'.mtl')).write_text('newmtl RT_Surface\nKa 0.15 0.15 0.15\nKd 1 1 1\nKs 0 0 0\nNs 1\nd 1\nillum 1\nmap_Kd '+mesh.name+'_Diffuse.png\n')
    br=['// Original revised rigid mesh; native conversion not yet validated','skeleton',
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
    image=add((folder/(mesh.name+'_Diffuse.png')).read_bytes())
    gltf={'asset':{'version':'2.0','generator':'Realistic Terrain revised mesh builder'},
          'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':accessors,
          'images':[{'bufferView':image,'mimeType':'image/png'}],
          'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],
          'textures':[{'source':0,'sampler':0}],
          'materials':[{'name':'RT_Surface','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1}}],
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
            'textures':[mesh.name+'/'+mesh.name+'_'+kind+ext for kind in ('Diffuse','Normal','Specular') for ext in ('.png','.dds')],
            'surface_bake':bake_info,
            'native_status':'BR2 import and GR2 conversion not executed'}



def _project(p,right,up,center,scale,w,h):
    return np.stack((w/2+(p-center)@right*scale,h*.55-(p-center)@up*scale),axis=1)


def _pixels(coords,w,h):
    lo=np.maximum(np.floor(coords.min(axis=0)).astype(int),(0,0));hi=np.minimum(np.ceil(coords.max(axis=0)).astype(int),(w-1,h-1))
    if np.any(hi<lo):return None
    (x0,y0),(x1,y1),(x2,y2)=coords
    den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    if abs(den)<1e-10:return None
    yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];xx=xx+.5;yy=yy+.5
    a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
    b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;c=1-a-b
    return (slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1)),a,b,c,(a>=-1e-8)&(b>=-1e-8)&(c>=-1e-8)


def render(mesh,atlas,width=960,height=760,azimuth=-57,terrain=False,elevation=32):
    """Rasterize the exported triangles/UVs, with shadow maps and contact shading.

    The neutral review ground is presentation only and is never exported.
    """
    ss=1.5;w=int(width*ss);h=int(height*ss)
    pixels=np.full((h,w,3),(225,220,205),dtype=float);depth=np.full((h,w),-np.inf)
    world=np.zeros((h,w,3),dtype=np.float32);normalbuf=np.zeros_like(world)
    allp=np.vstack([p for p,_,_,_ in mesh.faces]);middle=(allp.max(axis=0)+allp.min(axis=0))/2
    center=np.array((middle[0],middle[1],middle[2]*.78))
    a=math.radians(azimuth);e=math.radians(elevation)
    camera=norm((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))
    right=norm(np.cross((0,0,1),camera));up=norm(np.cross(camera,right))
    projected=np.stack(((allp-center)@right,(allp-center)@up),axis=1)
    span=np.ptp(projected,axis=0);scale=min((w-100)/span[0],(h-110)/span[1])*.94
    sun=norm((-.55,-.72,1.2));sr=norm(np.cross((0,0,1),sun));su=norm(np.cross(sun,sr))
    sw=1200;sh=1200;sc=sw/15;shadow=np.full((sh,sw),-np.inf,dtype=np.float32)
    for p,n,mat,part in mesh.faces:
        out=_pixels(_project(p,sr,su,center,sc,sw,sh),sw,sh)
        if out is None:continue
        region,a,b,c,inside=out;zz=p@sun;z=a*zz[0]+b*zz[1]+c*zz[2]
        visible=inside&(z>shadow[region]);shadow[region][visible]=z[visible]
    tex=np.asarray(getattr(mesh,'baked_diffuse',atlas))
    ground=[]
    for tri in [((-30,-30,-.025),(30,-30,-.025),(30,30,-.025)),((-30,-30,-.025),(30,30,-.025),(-30,30,-.025))]:
        ground.append((np.array(tri),np.array((0,0,1)),None,'review_ground'))
    for face_index,(p,n,mat,part) in enumerate(ground+mesh.faces):
        if n@camera<=0:continue
        out=_pixels(_project(p,right,up,center,scale,w,h),w,h)
        if out is None:continue
        region,a,b,c,inside=out;zz=p@camera;z=a*zz[0]+b*zz[1]+c*zz[2]
        visible=inside&(z>depth[region])
        if not visible.any():continue
        pos=a[:,:,None]*p[0]+b[:,:,None]*p[1]+c[:,:,None]*p[2]
        coords=_project(pos.reshape(-1,3),sr,su,center,sc,sw,sh).reshape(*a.shape,2)
        sx=np.clip(coords[:,:,0].astype(int),1,sw-2);sy=np.clip(coords[:,:,1].astype(int),1,sh-2)
        sz=pos@sun;shade=np.zeros(a.shape)
        for dx,dy in [(0,0),(-1,0),(1,0),(0,1),(0,-1)]:shade+=(sz+.028>=shadow[sy+dy,sx+dx])/5
        if mat:
            uv=mesh.baked_uv[(face_index-2)*3:(face_index-1)*3] if hasattr(mesh,'baked_uv') else face_uv(p,n,mat)
            uu=a*uv[0,0]+b*uv[1,0]+c*uv[2,0];vv=1-(a*uv[0,1]+b*uv[1,1]+c*uv[2,1])
            color=tex[np.clip((vv*tex.shape[0]).astype(int),0,tex.shape[0]-1),np.clip((uu*tex.shape[1]).astype(int),0,tex.shape[1]-1)].astype(float)
            # Subtle near-ground dirt wash is review lighting, not an extra texture.
            light=.54+.46*max(0,n@sun)*(.35+.65*shade)
        else:
            noise=np.sin(pos[:,:,0]*7.3+pos[:,:,1]*2.1)*.7+np.sin(pos[:,:,0]*17.1-pos[:,:,1]*8)*.35
            base=(131,135,103) if terrain else (225,220,205)
            color=np.array(base)[None,None,:]+noise[:,:,None]
            light=.83+.17*shade
        depth[region][visible]=z[visible];world[region][visible]=pos[visible];normalbuf[region][visible]=n
        pixels[region][visible]=(color*light[:,:,None])[visible]
    # Short-radius directional contact occlusion derived from mesh depth.
    occ=np.zeros((h,w),dtype=np.float32)
    for radius in (6,14,27):
        for dx,dy in ((radius,0),(-radius,0),(0,radius),(0,-radius),(radius,radius),(-radius,-radius)):
            neighbor=np.roll(world,(dy,dx),(0,1));delta=neighbor-world
            dist=np.linalg.norm(delta,axis=2)
            lifted=np.sum(delta*normalbuf,axis=2)
            occ+=((lifted>.045)&(dist>.055)&(dist<.7))*(1-np.clip(dist/.7,0,1))
    pixels*=np.clip(1-occ*.055,.69,1)[:,:,None]
    return Image.fromarray(np.uint8(np.clip(pixels,0,255))).resize((width,height),Image.Resampling.LANCZOS)
