"""Bake the material library and static occlusion into each 3D mesh's UV atlas.

This is a source-mesh texture bake, not a repaint of the approved concept images.
No stock game texture is sampled. Diffuse materials come from the original
procedural material library. Preview renders use the same baked export texture.
"""
from collections import defaultdict
from pathlib import Path
import math
import numpy as np
from PIL import Image

# RT owns this copy: the independently edited outpost toolchain is not imported.
REPEAT={'stone':(7,6),'limestone':(8,7),'sandstone':(8,7),'brick':(6,6),
        'timber':(4,5),'woodlight':(4,5),'tile':(5,5),'roofmetal':(6,6),
        'water':(8,8),'rubber':(5,5),'paving':(7,7)}
SIZE=2048;PAD=5


def charts_for(mesh):
    charts={}
    for i,(p,n,material,part) in enumerate(mesh.faces):
        normal=tuple(np.round(n,5));plane=round(float(np.dot(n,p[0])),5)
        key=(normal,plane,material,part)
        if key not in charts:
            dominant=int(np.argmax(np.abs(n)))
            axes=([1,2],[0,2],[0,1])[dominant]
            charts[key]={'normal':n,'plane':plane,'axes':axes,'dominant':dominant,
                         'material':material,'part':part,'faces':[]}
        charts[key]['faces'].append(i)
    for chart in charts.values():
        points=np.vstack([mesh.faces[i][0] for i in chart['faces']])
        projected=points[:,chart['axes']]
        chart.update(low=projected.min(axis=0),high=projected.max(axis=0),origin=points.mean(axis=0))
    return list(charts.values())


def pack(charts):
    for density in (82,72,62,52,44,36,28,20,14):
        for c in charts:
            c['extent']=np.maximum(c['high']-c['low'],.015)
            priority=1.4 if c['part'] in ('roof','treasury_facade','gateway_wing','counting_house','left_office') else 1
            c['pixels']=np.maximum(2,np.ceil(c['extent']*density*priority).astype(int))
        shelves=[];bottom=0;ok=True
        for c in sorted(charts,key=lambda c:(-c['pixels'][1],-c['pixels'][0])):
            w,h=c['pixels']+PAD*2
            if w>SIZE or h>SIZE:ok=False;break
            candidates=[s for s in shelves if h<=s['height'] and s['x']+w<=SIZE]
            if candidates:
                shelf=min(candidates,key=lambda s:s['height']-h)
            else:
                if bottom+h>SIZE:ok=False;break
                shelf={'x':0,'y':bottom,'height':h};shelves.append(shelf);bottom+=h
            c['pixel_origin']=np.array((shelf['x']+PAD,shelf['y']+PAD))
            shelf['x']+=w
        if ok:return density
    raise ValueError('UV atlas packing failed')


class Occlusion:
    def __init__(self,mesh):
        triangles=np.array([p for p,n,mat,part in mesh.faces])
        self.p0=triangles[:,0];self.e1=triangles[:,1]-triangles[:,0];self.e2=triangles[:,2]-triangles[:,0]
        self.cache={}

    def sample(self,point,normal):
        key=tuple(np.round(normal,5))
        if key not in self.cache:
            seed=np.array((0.,0.,1.)) if abs(normal[2])<.9 else np.array((1.,0.,0.))
            tangent=np.cross(seed,normal);tangent/=np.linalg.norm(tangent)
            bitangent=np.cross(normal,tangent)
            directions=[]
            for i in range(8):
                angle=2*math.pi*(i+.5)/8;z=.42 if i%2 else .78;r=math.sqrt(1-z*z)
                directions.append(normal*z+tangent*(r*math.cos(angle))+bitangent*(r*math.sin(angle)))
            directions=np.array(directions)
            h=np.cross(directions[:,None,:],self.e2[None,:,:])
            det=np.einsum('tj,rtj->rt',self.e1,h)
            inv=np.divide(1.,det,out=np.zeros_like(det),where=np.abs(det)>1e-8)
            self.cache[key]=(directions,h,inv,np.abs(det)>1e-8)
        directions,h,inv,valid=self.cache[key]
        s=point+normal*.025-self.p0
        u=np.einsum('tj,rtj->rt',s,h)*inv
        q=np.cross(s,self.e1)
        v=np.einsum('rj,tj->rt',directions,q)*inv
        t=np.einsum('tj,tj->t',self.e2,q)[None,:]*inv
        hits=valid&(u>=0)&(v>=0)&(u+v<=1)&(t>.025)&(t<1.8)
        proximity=np.where(hits,1-t/1.8,0).max(axis=1)
        return 1-.42*float(proximity.mean())


def bake(mesh,library,names,grid):
    charts=charts_for(mesh);density=pack(charts)
    image=np.full((SIZE,SIZE,3),96,dtype=np.uint8)
    normal_image=np.full_like(image,(128,128,255));spec_image=np.full_like(image,8)
    uv=np.empty((len(mesh.faces)*3,2),dtype=float)
    source=np.asarray(library.convert('RGB'));occ=Occlusion(mesh)
    for chart in charts:
        start=chart['pixel_origin'];width,height=chart['pixels'];a,b=chart['axes']
        xx,yy=np.meshgrid(np.arange(-PAD,width+PAD),np.arange(-PAD,height+PAD))
        fx=np.clip((xx+.5)/width,0,1);fy=np.clip((yy+.5)/height,0,1)
        ua=chart['low'][0]+fx*chart['extent'][0]
        ub=chart['low'][1]+fy*chart['extent'][1]
        material=chart['material'];idx=names.index(material)
        repeat=REPEAT.get(material,(9,9))
        su=(idx%grid+.06+np.mod(ua/repeat[0],1)*.88)/grid
        sv=(idx//grid+.06+np.mod(-ub/repeat[1],1)*.88)/grid
        color=source[np.clip((sv*source.shape[0]).astype(int),0,source.shape[0]-1),
                     np.clip((su*source.shape[1]).astype(int),0,source.shape[1]-1)].astype(float)
        n=chart['normal'];other=chart['dominant']
        if b==2:z=ub
        elif a==2:z=ua
        else:z=(chart['plane']-n[a]*ua-n[b]*ub)/n[other]
        ground=.86+.14*np.clip(z/.7,0,1)
        # Sample along the chart's long direction; this bakes broad, soft cavity
        # changes instead of one flat darkness value across a whole wall.
        samples=[]
        axis=a if chart['extent'][0]>=chart['extent'][1] else b
        for t in (.12,.5,.88):
            p=chart['origin'].copy();k=0 if axis==a else 1
            p[axis]=chart['low'][k]+t*chart['extent'][k]
            p[other]=(chart['plane']-n[a]*p[a]-n[b]*p[b])/n[other]
            samples.append(occ.sample(p,n))
        f=fx if axis==a else fy
        ao=np.interp(f,[.12,.5,.88],samples)
        if material in ('glass','solar'):ao=np.maximum(.82,ao)
        # Derive modest micro-relief from the unlit original material, never AO.
        lum=color.mean(axis=2)/255
        dv,du=np.gradient(lum)
        normal=np.stack((-du*1.9,dv*1.9,np.ones_like(lum)),axis=2)
        normal/=np.linalg.norm(normal,axis=2)[...,None]
        normal=np.uint8(np.clip((normal*.5+.5)*255,0,255))
        spec=55 if material in ('brass','steel','water','glass') else (23 if material in ('truckpaint','patina','roofmetal') else 8)
        color*= (ground*ao)[...,None]
        # Small desaturation makes colored roofs and cloth sit in the terrain.
        grey=color.mean(axis=2,keepdims=True);color=color*.96+grey*.04
        region=np.clip(color,0,255).astype('uint8')
        x,y=start-PAD;image[y:y+region.shape[0],x:x+region.shape[1]]=region
        normal_image[y:y+region.shape[0],x:x+region.shape[1]]=normal
        spec_image[y:y+region.shape[0],x:x+region.shape[1]]=spec
        for index in chart['faces']:
            p=mesh.faces[index][0]
            local=(p[:,chart['axes']]-chart['low'])/chart['extent']
            pixels=start+local*chart['pixels']
            uv[index*3:index*3+3]=pixels/SIZE
    uv[:,1]=1-uv[:,1]
    return Image.fromarray(image),Image.fromarray(normal_image),Image.fromarray(spec_image),uv,{'charts':len(charts),'texels_per_source_unit':density,
                                    'density_priority':'principal volumes 1.4x; detail 1x',
                                    'resolution':SIZE,'occlusion':'8 hemisphere rays at 3 samples per planar chart, plus ground contact gradient'}
