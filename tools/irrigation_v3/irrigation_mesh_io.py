"""Independent UV mesh/export/review utilities for the irrigation tile kit.

Only NumPy/Pillow are required. Previews rasterize the actual exported GLB data;
no generated concept pixels or extracted game textures enter these assets.
"""
from pathlib import Path
import io
import json
import math
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MATERIALS = {
    'stone': (139, 133, 111), 'coping': (173, 162, 132),
    'soil': (120, 103, 72), 'rock': (119, 115, 104),
    'barley': (155, 145, 81), 'vegetables': (62, 89, 44),
    'legumes': (91, 110, 54), 'stubble': (146, 125, 83),
    'leaves': (65, 83, 43), 'leaf_light': (85, 103, 54),
    'wood': (103, 86, 58), 'water': (49, 78, 69),
    'plaster': (172, 158, 124), 'shadow': (49, 47, 38),
    'dry_crop': (136, 120, 79), 'earth': (142, 122, 87),
}
NAMES = list(MATERIALS)
CELL, GRID, GUTTER = 512, 4, 16


def unit(v):
    v = np.asarray(v, dtype=float)
    length = np.linalg.norm(v)
    if length < 1e-12:
        raise ValueError('Zero vector')
    return v / length


def atlas_uv(uv, material):
    i = NAMES.index(material)
    uv = np.asarray(uv, dtype=float)
    # Source UVs and OBJ use bottom-left origin; PNG/glTF use top-left.
    result = (np.array((i % GRID, i // GRID)) + GUTTER / CELL
              + uv * (1 - 2 * GUTTER / CELL)) / GRID
    result[:, 1] = 1 - result[:, 1]
    return result


class Mesh:
    def __init__(self, name):
        self.name, self.faces, self.routes = name, [], []
        self.meta = {}

    def face(self, vertices, material, part, uv=None):
        p = np.asarray(vertices, dtype=float)
        if uv is None:
            n = unit(np.cross(p[1]-p[0], p[2]-p[0]))
            axes = ([1, 2], [0, 2], [0, 1])[np.argmax(np.abs(n))]
            projected = p[:, axes]
            extent = np.ptp(projected, axis=0)
            uv = (projected - projected.min(axis=0)) / np.maximum(extent, 1e-9)
            if material in ('stone','coping'):
                # Physical masonry scale instead of a whole wall atlas per face.
                uv = (projected-projected.min(axis=0))/np.maximum(extent,[4.5,2.4])
        uv = atlas_uv(uv, material)
        for j in range(1, len(p)-1):
            ids = [0, j, j+1]
            tri = p[ids]
            n = unit(np.cross(tri[1]-tri[0], tri[2]-tri[0]))
            self.faces.append((tri, n, uv[ids], material, part))

    def box(self, center, size, material, part):
        c, s = np.asarray(center), np.asarray(size) / 2
        if (s <= 0).any():
            return
        p = c + np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                          (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]) * s
        for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.face(p[list(ids)], material, part)

    def append(self, mesh, offset=(0,0,0), angle=0, prefix=''):
        a = math.radians(angle)
        r = np.array(((math.cos(a),-math.sin(a),0),
                      (math.sin(a),math.cos(a),0),(0,0,1)))
        for p,n,uv,mat,part in mesh.faces:
            self.faces.append((p @ r.T + offset, n @ r.T, uv.copy(), mat, prefix+part))
        for route in mesh.routes:
            self.routes.append(dict(route, name=prefix+route['name'],
                upstream=prefix+route['upstream'] if route.get('upstream') else None,
                points=(np.array(route['points']) @ r.T + offset).tolist()))

    def arrays(self):
        p=np.concatenate([f[0] for f in self.faces])
        normals=np.repeat(np.array([f[1] for f in self.faces]),3,axis=0)
        shared={}
        for j,(tri,n,uv,mat,part) in enumerate(self.faces):
            if not part.endswith('terrain_surface'):continue
            weight=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))
            for v in tri:
                key=tuple(np.round(v,7));shared[key]=shared.get(key,np.zeros(3))+n*weight
        for j,(tri,n,uv,mat,part) in enumerate(self.faces):
            if part.endswith('terrain_surface'):
                for k,v in enumerate(tri):normals[j*3+k]=unit(shared[tuple(np.round(v,7))])
        return p,normals,np.concatenate([f[2] for f in self.faces])


from refine_materials import make_atlas


def export(mesh, folder):
    folder = folder / mesh.name; folder.mkdir(parents=True, exist_ok=True)
    # Opaque parts may be reordered: keep the offline viewer's draw-call count
    # proportional to component types rather than individual plant leaves.
    mesh.faces.sort(key=lambda face: face[4])
    p,n,uv = mesh.arrays()
    groups=[]
    for i,f in enumerate(mesh.faces):
        if groups and groups[-1]['name']==f[4]:groups[-1]['count']+=3
        else:groups.append({'name':f[4],'first':i*3,'count':3})
    lines = [f'# Original irrigation source mesh. Z up. Normalized units, not engine-calibrated.',
             f'mtllib {mesh.name}.mtl']
    for a,tag in ((p,'v'),(uv,'vt'),(n,'vn')):
        lines.extend(tag+' '+' '.join(f'{v:.8f}' for v in row) for row in a)
    lines.append('usemtl RT_IF_Diffuse'); previous = None
    for j,f in enumerate(mesh.faces):
        if f[4] != previous:
            lines.append('g '+f[4]); previous = f[4]
        lines.append('f '+' '.join(f'{i}/{i}/{i}' for i in range(j*3+1,j*3+4)))
    (folder/(mesh.name+'.obj')).write_text('\n'.join(lines)+'\n')
    (folder/(mesh.name+'.mtl')).write_text('newmtl RT_IF_Diffuse\nKd 1 1 1\nKa 0.15 0.15 0.15\nKs 0 0 0\nNs 1\nillum 1\nmap_Kd ../RT_IF_Diffuse.png\nmap_d ../RT_IF_Diffuse.png\n')
    br=['// Original rigid source geometry; GR2 conversion remains unverified','skeleton',
        '0 "World" -1 0 0 0 0 0 0 1 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1',
        'meshes:1',f'mesh:"{mesh.name}"','vertices']
    for face_index,(tri,normal,tex,mat,part) in enumerate(mesh.faces):
        tex=tex.copy();tex[:,1]=1-tex[:,1]
        e1,e2=tri[1]-tri[0],tri[2]-tri[0];d1,d2=tex[1]-tex[0],tex[2]-tex[0]
        det=d1[0]*d2[1]-d1[1]*d2[0]
        if abs(det)<1e-12: raise ValueError((mesh.name,part,'degenerate UV'))
        tangent=unit((e1*d2[1]-e2*d1[1])/det)
        b=unit((-e1*d2[0]+e2*d1[0])/det)
        bitangent=unit(np.cross(normal,tangent))*(1 if np.dot(np.cross(normal,tangent),b)>=0 else -1)
        for vertex_index,(v,t) in enumerate(zip(tri,tex)):
            vertex_normal=n[face_index*3+vertex_index]
            vertex_tangent=unit(tangent-vertex_normal*np.dot(vertex_normal,tangent))
            vertex_bitangent=unit(np.cross(vertex_normal,vertex_tangent))*(1 if np.dot(np.cross(vertex_normal,vertex_tangent),bitangent)>=0 else -1)
            row=list(v)+list(vertex_normal)+list(t)+[0,0,0,0,255,0,0,0]+list(vertex_tangent)+list(vertex_bitangent)
            br.append(' '.join(str(int(v)) if 8<=k<16 else f'{v:.8f}' for k,v in enumerate(row)))
    br+=['triangles']+[f'{i} {i+1} {i+2}' for i in range(0,len(p),3)]+['end']
    (folder/(mesh.name+'.br2')).write_text('\n'.join(br)+'\n')
    blob=bytearray();views=[];accessors=[]
    def add(data):
        blob.extend(b'\0'*((-len(blob))%4));off=len(blob);blob.extend(data)
        views.append({'buffer':0,'byteOffset':off,'byteLength':len(data)})
        return len(views)-1
    def acc(data,kind):
        data=np.asarray(data,dtype='<f4');v=add(data.tobytes())
        accessors.append({'bufferView':v,'componentType':5126,'count':len(data),'type':kind,
                          'min':data.min(axis=0).tolist(),'max':data.max(axis=0).tolist()})
        return len(accessors)-1
    gp=acc(p,'VEC3');gn=acc(n,'VEC3');t=uv.copy();t[:,1]=1-t[:,1];gt=acc(t,'VEC2')
    im=add((folder.parent/'RT_IF_Diffuse.png').read_bytes())
    g={'asset':{'version':'2.0','generator':'Realistic Terrain irrigation mesh kit'},
       'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':accessors,
       'images':[{'bufferView':im,'mimeType':'image/png'}],
       'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],
       'textures':[{'source':0,'sampler':0}],
       'materials':[{'name':'RT_IF_Diffuse','alphaMode':'MASK','alphaCutoff':0.5,'pbrMetallicRoughness':{
           'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1}}],
       'meshes':[{'name':mesh.name,'extras':{'groups':groups},'primitives':[{'attributes':{'POSITION':gp,'NORMAL':gn,'TEXCOORD_0':gt},'material':0}]}],
       'nodes':[{'mesh':0,'rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)]}],
       'scenes':[{'nodes':[0]}],'scene':0}
    js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    blob.extend(b'\0'*((-len(blob))%4))
    data=struct.pack('<III',0x46546c67,2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob
    (folder/(mesh.name+'.glb')).write_bytes(data)
    record={'name':mesh.name,'triangles':len(mesh.faces),'vertices':len(p),
            'bounds_z_up':[p.min(axis=0).tolist(),p.max(axis=0).tolist()],
            'parts':sorted(set(f[4] for f in mesh.faces)), 'groups':groups, 'routes':mesh.routes, **mesh.meta}
    (folder/(mesh.name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    return record


def read_glb(path):
    raw=Path(path).read_bytes();length,kind=struct.unpack_from('<II',raw,12)
    assert kind==0x4e4f534a
    g=json.loads(raw[20:20+length]);blob=raw[28+length:]
    arrays=[]
    for a in g['accessors']:
        v=g['bufferViews'][a['bufferView']];dim={'VEC2':2,'VEC3':3}[a['type']]
        arrays.append(np.frombuffer(blob,dtype='<f4',count=a['count']*dim,offset=v['byteOffset']).reshape(-1,dim).copy())
    return g, arrays, blob


def pixels(coords,w,h):
    lo=np.maximum(np.floor(coords.min(axis=0)).astype(int),(0,0))
    hi=np.minimum(np.ceil(coords.max(axis=0)).astype(int),(w-1,h-1))
    if (hi<lo).any():return None
    (x0,y0),(x1,y1),(x2,y2)=coords
    den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    if abs(den)<1e-10:return None
    yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];xx=xx+.5;yy=yy+.5
    a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
    b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;c=1-a-b
    return (slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1)),a,b,c,(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)


def render_glb(path, width=1200, height=900, azimuth=-72, elevation=42, wire=False, shadow_bias=.035):
    """Orthographic textured raster and shadow map made from the exported GLB."""
    g,(p,n,uv),blob=read_glb(path)
    v=g['bufferViews'][g['images'][0]['bufferView']]
    tex=np.asarray(Image.open(io.BytesIO(blob[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGBA'))
    ss=1.25;w,h=int(width*ss),int(height*ss)
    a,e=math.radians(azimuth),math.radians(elevation)
    camera=unit((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))
    right=unit(np.cross((0,0,1),camera));up=unit(np.cross(camera,right))
    center=(p.min(axis=0)+p.max(axis=0))/2
    pp=np.stack(((p-center)@right,(p-center)@up),axis=1)
    span=np.ptp(pp,axis=0);scale=min((w-80)/span[0],(h-90)/span[1])*.94
    def proj(data,r,u,c,s,ww,hh):
        return np.stack((ww/2+(data-c)@r*s,hh/2-(data-c)@u*s),axis=-1)
    sun=unit((-.5,-.8,1.7));sr=unit(np.cross((0,0,1),sun));su=unit(np.cross(sun,sr))
    sw=1200;spp=np.stack(((p-center)@sr,(p-center)@su),axis=1)
    sc=(sw-60)/max(np.ptp(spp,axis=0));shadow=np.full((sw,sw),-np.inf)
    for tri,t in zip(p.reshape(-1,3,3),uv.reshape(-1,3,2)):
        r=pixels(proj(tri,sr,su,center,sc,sw,sw),sw,sw)
        if r is None:continue
        reg,a,b,c,inside=r;zv=tri@sun;z=a*zv[0]+b*zv[1]+c*zv[2]
        u=a*t[0,0]+b*t[1,0]+c*t[2,0];v=a*t[0,1]+b*t[1,1]+c*t[2,1]
        alpha=tex[np.clip((v*tex.shape[0]).astype(int),0,tex.shape[0]-1),np.clip((u*tex.shape[1]).astype(int),0,tex.shape[1]-1),3]
        vis=inside&(alpha>=128)&(z>shadow[reg]);shadow[reg][vis]=z[vis]
    colors=np.full((h,w,3),(218,210,188),dtype=float);depth=np.full((h,w),-np.inf)
    triangles=p.reshape(-1,3,3);normals=n.reshape(-1,3,3);uvs=uv.reshape(-1,3,2)
    for tri,normal,t in zip(triangles,normals,uvs):
        if np.mean(normal,axis=0)@camera<=0:continue
        coords=proj(tri,right,up,center,scale,w,h);r=pixels(coords,w,h)
        if r is None:continue
        reg,a,b,c,inside=r;zv=tri@camera;z=a*zv[0]+b*zv[1]+c*zv[2]
        vis=inside&(z>depth[reg])
        if not vis.any():continue
        u=a*t[0,0]+b*t[1,0]+c*t[2,0];v=a*t[0,1]+b*t[1,1]+c*t[2,1]
        sample=tex[np.clip((v*tex.shape[0]).astype(int),0,tex.shape[0]-1),np.clip((u*tex.shape[1]).astype(int),0,tex.shape[1]-1)].astype(float)
        col=sample[:,:,:3];vis&=sample[:,:,3]>=128
        if not vis.any():continue
        pos=a[:,:,None]*tri[0]+b[:,:,None]*tri[1]+c[:,:,None]*tri[2]
        xy=proj(pos,sr,su,center,sc,sw,sw)
        sx=np.clip(xy[:,:,0].astype(int),0,sw-1);sy=np.clip(xy[:,:,1].astype(int),0,sw-1)
        lit=(pos@sun+shadow_bias>=shadow[sy,sx]).astype(float)
        nn=a[:,:,None]*normal[0]+b[:,:,None]*normal[1]+c[:,:,None]*normal[2]
        diffuse=np.maximum(0,(nn@sun)/np.maximum(1e-8,np.linalg.norm(nn,axis=2)))
        lighting=.52+.48*diffuse*(.23+.77*lit)
        col*=lighting[:,:,None]
        if wire:
            edge=np.minimum(np.minimum(a,b),c)<.025
            col[edge]*=.25
        colors[reg][vis]=col[vis];depth[reg][vis]=z[vis]
    return Image.fromarray(np.uint8(np.clip(colors,0,255))).resize((width,height),Image.Resampling.LANCZOS)
