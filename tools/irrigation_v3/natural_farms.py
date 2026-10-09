"""Open hillside benches and gravity-fed branched distribution networks.

Coordinates and shared edges retain the radius-six source contract. Terrain
and channel elevations are authored together; no trough follows a dipped
terrain contour and then climbs to the next farm.
"""
import math
from functools import lru_cache
import numpy as np
from irrigation_mesh_io import Mesh,unit
from refine_geometry import palm,orchard,farmstead,tube,cluster

B=None
N=24
ANGLES=np.linspace(-math.pi,math.pi,N,endpoint=False)

def bind(module):
    global B
    B=module

def front_end(k):return [14,12,13,11,12,11][k]
def front(i,k=0):return 0<=i<front_end(k)
def gully(i,k):return k>0 and i in (4,10) and i<front_end(k)-1

def boundary():
    # Sample exact hex edges, including all six corners, at the polar angles.
    out=[]
    for a in ANGLES:
        d=np.array((math.cos(a),math.sin(a)))
        radius=min(B.A/max(1e-9,np.dot(d,[math.cos(j*math.pi/3),math.sin(j*math.pi/3)])) for j in range(6) if np.dot(d,[math.cos(j*math.pi/3),math.sin(j*math.pi/3)])>0)
        out.append(d*radius)
    return np.array(out)

@lru_cache(None)
def terrace_rings(kind):
    if kind=='Flat':return [(boundary(),0.)]
    steps,H=B.KINDS[kind]
    radii={'GentleHill':[4.40,3.13,1.64], 'SteepHill':[4.48,3.69,2.89,2.07,1.22], 'RockyFoothill':[4.40,3.43,2.42,1.25]}[kind]
    rings=[(boundary(),0.)]
    for k,r in enumerate(radii):
        r*=.95
        points=[]
        for a in ANGLES:
            variation=1+.065*math.sin(3*a+.6)+.037*math.cos(5*a-.5)
            points.append((.32-.055*k+r*.98*variation*math.cos(a),.72+.07*k+r*.83*variation*math.sin(a)))
        # Unequal retaining heights; shelves retain a horizontal water grade.
        h=H*((k+1)/steps)**.93
        rings.append((np.array(points),h))
    return rings

@lru_cache(None)
def terrain_faces(kind):
    rings=terrace_rings(kind);faces=[]
    if kind=='Flat':
        p,z=rings[0]
        for i in range(N):faces.append((np.array([(*p[i],0),(*p[(i+1)%N],0),(0,0,0)]),False,0,i))
        return faces
    for k,((outer,z),(inner,h)) in enumerate(zip(rings,rings[1:])):
        for i in range(N):
            j=(i+1)%N;back=not front(i,k)
            q=np.array([(*outer[i],z),(*outer[j],z),(*inner[j],h if back else z),(*inner[i],h if back else z)])
            if gully(i,k):q[:,2]-=.32
            for ids in [[0,1,2],[0,2,3]]:faces.append((q[ids],back,k,i))
    p,z=rings[-1];c=p.mean(axis=0)
    for i in range(N):
        j=(i+1)%N
        faces.append((np.array([(*p[i],z),(*p[j],z),(*c,z+.22)]),True,len(rings)-1,i))
    return faces

@lru_cache(None)
def terrain_arrays(kind):
    tr=np.array([f[0] for f in terrain_faces(kind)])
    a=tr[:,0,:2];e1=tr[:,1,:2]-a;e2=tr[:,2,:2]-a
    return tr,a,e1,e2,e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0]

def surface_height(kind,x,y):
    tr,a,e1,e2,den=terrain_arrays(kind);p=np.array((x,y))-a
    u=(p[:,0]*e2[:,1]-p[:,1]*e2[:,0])/den
    v=(e1[:,0]*p[:,1]-e1[:,1]*p[:,0])/den
    ids=np.flatnonzero((u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7))
    if not len(ids):return 0.
    return float(max(tr[i,0,2]*(1-u[i]-v[i])+tr[i,1,2]*u[i]+tr[i,2,2]*v[i] for i in ids))

def flat_rotate(point):
    x,y,z=point;a=.19
    return np.array((x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),z))

def inlet(kind):
    return flat_rotate((-2.5,3.6,.14)) if kind=='Flat' else np.array((0,.42,B.KINDS[kind][1]+.65))

def trough(m,points,part='channel',wet=True,width=None,gaps=(),parent=None,spans=()):
    width=B.WATER_WIDTH if width is None else width
    points=np.asarray(points,dtype=float)
    if len(points)<2 or (np.diff(points[:,2])>1e-7).any():raise ValueError(('uphill route',part,points))
    sides=[]
    for i,p in enumerate(points):
        before=unit(points[i]-points[i-1]) if i else unit(points[1]-p)
        after=unit(points[i+1]-p) if i+1<len(points) else before
        s0=unit((-before[1],before[0],0));s1=unit((-after[1],after[0],0))
        side=unit(s0+s1);sides.append(side/max(.50,np.dot(side,s1)))
    rim=min(B.WALL_WIDTH,width*.28);depth=B.WATER_DEPTH
    for index,(a,b) in enumerate(zip(points,points[1:])):
        if index in spans:continue
        s0,s1=sides[index:index+2];delta=b-a;length=np.linalg.norm(delta[:2]);u=delta[:2]/length
        cut=[]
        for g in gaps:
            g=np.asarray(g);along=np.dot(g[:2]-a[:2],u);distance=abs(np.cross(u,g[:2]-a[:2]))
            if distance<width+rim and abs(g[2]-a[2])<.02:
                cut.append((max(0.,(along-width*.7)/length),min(1.,(along+width*.7)/length)))
        for lo,hi,z0,z1,mat,label in [(-width/2,width/2,-depth-.035,-depth,'stone','bed'),(-width/2-rim,-width/2,-depth-.035,.055,'stone','left_rim'),(width/2,width/2+rim,-depth-.035,.055,'stone','right_rim')]:
            intervals=[(0.,1.)]
            if label!='bed':
                for start,end in cut:
                    updated=[]
                    for l,r in intervals:
                        if end<=l or start>=r:updated.append((l,r));continue
                        if start>l:updated.append((l,start))
                        if end<r:updated.append((end,r))
                    intervals=updated
            for t0,t1 in intervals:
                if t1-t0<1e-6:continue
                va,vb=a+delta*t0,a+delta*t1;sa,sb=s0+(s1-s0)*t0,s0+(s1-s0)*t1
                p=[v+side*s+[0,0,z] for v,side in [(va,sa),(vb,sb)] for s,z in [(lo,z0),(hi,z0),(hi,z1),(lo,z1)]]
                faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
                if getattr(m,'lod',0):
                    faces=[] if label=='bed' and wet else [(3,7,6,2),(0,4,7,3),(1,2,6,5)]
                for ids in faces:m.face([p[i] for i in ids],mat,part+'_'+label)
        if wet:m.face([a-s0*width/2,b-s1*width/2,b+s1*width/2,a+s0*width/2],'water',part+'_water',[(0,0),(1,0),(1,1),(0,1)])
    m.routes.append({'name':part,'points':points.tolist(),'width':width,'wet':wet,'upstream':parent})

def header(kind,k):
    rings=terrace_rings(kind);outer,z=rings[k];inner,_=rings[k+1]
    # A narrow supply ditch midway along the planted contour bench.
    end=front_end(k)+1
    result=np.c_[outer[:end]*.38+inner[:end]*.62,np.full(end,z+.14)]
    result[0,:2]=(result[0,:2]+result[1,:2])/2
    result[-1,:2]=result[-1,:2]*.2+result[-2,:2]*.8
    return result

def wall(m,a,b,z,h,k,i):
    # Slightly battered masonry, interrupted by the descending supply ditch.
    d=b-a;length=np.linalg.norm(d)
    for j in range(max(1,math.ceil(length/.40))):
        count=max(1,math.ceil(length/.40));t0=j/count;t1=(j+1)/count
        if i==0 and abs((t0+t1)/2-.5)<.21:continue
        if i==N-1 and t1>.74:continue
        p=a+d*t0;q=a+d*t1
        inward=unit(np.array((-(q-p)[1],(q-p)[0])))*.045
        # Common elevation at joints; tiny cap chips alter the silhouette only.
        top0=h+(.012 if (j+i)%3 else -.009);top1=h+(.012 if (j+i+1)%3 else -.009)
        uv=np.array([(t0*length,0),(t1*length,0),(t1*length,(h-z)/.85),(t0*length,(h-z)/.85)])
        m.face([(*(p-inward*.8),z),(*(q-inward*.8),z),(*q,top1),(*p,top0)],'stone','retaining_wall',uv)
        m.face([(*p,top0),(*q,top1),(*(q+inward),top1),(*(p+inward),top0)],'stone','wall_coping')

def field_patches(m,poly,z,origin,state):
    # Unequal, staggered parcels in a common rotated world frame. Adjacent farm
    # meshes therefore still meet with identical field species and UV phase.
    a=.19;rotation=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
    origin=np.asarray(origin);world=(np.asarray(poly)+origin)@rotation
    sx,sy=3.,2.7
    for iy in range(math.floor(world[:,1].min()/sy)-1,math.ceil(world[:,1].max()/sy)+1):
        y0=iy*sy+.17*math.sin(iy*2.1);y1=(iy+1)*sy+.17*math.sin((iy+1)*2.1)
        offset=.62*(iy%2)
        for ix in range(math.floor(world[:,0].min()/sx)-1,math.ceil(world[:,0].max()/sx)+1):
            x0=ix*sx+offset+.31*math.sin(ix*1.8);x1=(ix+1)*sx+offset+.31*math.sin((ix+1)*1.8)
            mat=['barley','vegetables','legumes','stubble','vegetables','legumes','barley'][(ix*3+iy*2)%7]
            if state=='Dry':mat='dry_crop'
            if state=='Construction':continue
            if state=='Pillaged':mat='stubble'
            pp=world.copy();margin=.06+.016*((ix+iy)%3)
            for axis,lim,gt in [(0,x0+margin,True),(0,x1-margin,False),(1,y0+margin,True),(1,y1-margin,False)]:pp=B.clip(pp,axis,lim,gt)
            pp=B.clean(pp)
            if not pp:continue
            pp=np.array(pp)
            # Fine painted crop detail repeats at agricultural scale within
            # the larger irregular parcel. Whole barley stalks are not tile-sized.
            repeat=.72
            for tx in range(math.floor(pp[:,0].min()/repeat),math.floor(pp[:,0].max()/repeat)+1):
                for ty in range(math.floor(pp[:,1].min()/repeat),math.floor(pp[:,1].max()/repeat)+1):
                    sub=pp.copy()
                    for axis,limit,gt in [(0,tx*repeat,True),(0,(tx+1)*repeat,False),(1,ty*repeat,True),(1,(ty+1)*repeat,False)]:sub=B.clip(sub,axis,limit,gt)
                    sub=B.clean(sub)
                    if not sub:continue
                    sub=np.array(sub);uv=(sub-[tx*repeat,ty*repeat])/repeat
                    local=sub@rotation.T-origin
                    m.face([(*v,z+.013) for v in local],mat,'crop_surface',uv)

def network(m,kind,wet):
    root=inlet(kind)
    if kind=='Flat':
        ys=[3.6,2.4,1.2,0,-1.2,-2.4,-3.6]
        spine=np.array([(-2.5,y,.14) for y in ys])
        branches=[]
        for j,p in enumerate(spine[1:-1]):
            endx=3.6 if abs(p[1])<2 else 2.8
            end=np.array((endx,p[1],.14))
            branches.append((p,end,f'flat_header_{j}'))
        rot=lambda points:np.array([flat_rotate(p) for p in points])
        trough(m,rot(spine),'flat_supply',wet,.18,gaps=rot([a for a,_,_ in branches]))
        for a,b,name in branches:
            points=np.linspace(a,b,5);tines=[]
            for index,p in enumerate(points[1:-1]):
                for sign in (-1,1):tines.append((p,p+[0,sign*.88,-.012],f'{name}_bed_{index}_{sign}'))
            trough(m,rot(points),name,wet,.10,gaps=rot([p for p,_,_ in tines]),parent='flat_supply')
            for p,q,n in tines:trough(m,rot([p,q]),n,wet,.055,parent=name)
        return
    rings=terrace_rings(kind);top=len(rings)-2
    h=header(kind,top);feed=[root,(*h[0,:2],root[2]),h[0]]
    # Avoid a zero-horizontal-length vertical segment: a short lined stair chute.
    feed[1]=np.array(feed[1])+[.10,0,0]
    trough(m,feed,'mountain_receiver_drop',wet,.18)
    for k in range(top,-1,-1):
        arc=header(kind,k);tines=[]
        outer,z=rings[k]
        for i in (2,4,6,8,10,12):
            if i>=len(arc)-1 or gully(i,k) or gully(i-1,k):continue
            p=arc[i];target=outer[i]*.78+arc[i,:2]*.22
            q=np.array((*target,z+.127))
            tines.append((p,q,f'bench_{k}_field_{i}'))
        parent='mountain_receiver_drop' if k==top else f'drop_{k+1}_{k}'
        spans=[i for i in range(len(arc)-1) if gully(i,k)]
        trough(m,arc,f'bench_{k}_contour',wet,.105,gaps=[p for p,_,_ in tines],parent=parent,spans=spans)
        for i in spans:
            B.bridge(m,arc[i],arc[i+1],ground=lambda x,y:z-.32,wet=wet,lod=m.lod,part=f'bench_{k}_aqueduct_{i}')
            m.routes[-1]['upstream']=f'bench_{k}_contour'
        for p,q,n in tines:trough(m,[p,q],n,wet,.055,parent=f'bench_{k}_contour')
        if k:
            lower=header(kind,k-1)[0];edge=(rings[k][0][0]+rings[k][0][1])/2;center=rings[k][0].mean(axis=0);u=unit(edge-center)
            # Keep the high grade until past the upper retaining edge; only
            # then descend into the lined cut on the lower bench.
            drop=[arc[0],(*(edge-u*.10),arc[0,2]),(*(edge+u*.035),arc[0,2]),(*(edge+u*.12),lower[2]),lower]
            trough(m,drop,f'drop_{k}_{k-1}',wet,.18,parent=f'bench_{k}_contour')

def planted_trees(m,kind,state,lod):
    if state not in ('Wet','Dry'):return
    rng=np.random.default_rng(719)
    if kind=='Flat':spots=[(-3.65,2.3),(-2.7,3.95),(-1.2,3.5),(.4,3.55),(2.6,2.9),(3.7,1.1),(-3.9,-.7)]
    else:
        spots=[]
        rings=terrace_rings(kind)
        for k in range(len(rings)-1):
            outer,z=rings[k];inner,h=rings[k+1]
            for i in (1,12):spots.append(tuple(outer[i]*.64+inner[i]*.36))
        spots+=[(1.8,2.8),(-1.5,2.8)]
    for i,(x,y) in enumerate(spots):
        z=surface_height(kind,x,y)
        if any(abs(surface_height(kind,x+dx,y+dy)-z)>.18 for dx,dy in [(.12,0),(-.12,0),(0,.12),(0,-.12)]):continue
        tree=palm(lod) if kind=='Flat' and i in (0,2,4) else orchard(lod,seed=123+i)
        scale=rng.uniform(.72,1.08)
        tree.faces=[(p*scale,n,uv,mat,part) for p,n,uv,mat,part in tree.faces]
        m.append(tree,(x,y,z+.02),angle=rng.uniform(0,360))

def tile(kind,state='Wet',lod=0,origin=(0,0),name=None):
    m=Mesh(name or f'RT_IF_{kind}_{state}'+('_LOD1' if lod else ''));m.lod=lod
    rings=terrace_rings(kind)
    for tri,back,k,i in terrain_faces(kind):
        m.face(tri,'rock' if back and k>1 else 'earth','terrain_surface')
    if kind=='Flat':field_patches(m,B.HEX,0,origin,state)
    else:
        for k,((outer,z),(inner,h)) in enumerate(zip(rings,rings[1:])):
            for i in range(N):
                j=(i+1)%N
                if front(i,k) and not gully(i,k):
                    field_patches(m,[outer[i],outer[j],inner[j],inner[i]],z,origin,state)
                    wall(m,inner[i],inner[j],z,h,k,i)
                elif gully(i,k):
                    # Exposed eroded banks beneath the little contour aqueduct.
                    for a,b in [(outer[i],inner[i]),(inner[j],outer[j])]:
                        q=[(*a,z-.32),(*b,z-.32),(*b,z),(*a,z)]
                        m.face(q,'rock','gully_bank');m.face(q[::-1],'rock','gully_bank')
                    upper=h-(.32 if k+1<len(rings)-1 and gully(i,k+1) else 0)
                    q=[(*inner[i],z-.32),(*inner[j],z-.32),(*inner[j],upper),(*inner[i],upper)]
                    m.face(q,'rock','gully_headwall');m.face(q[::-1],'rock','gully_headwall')
            # Close the exposed wedges where a cultivated bench ends against
            # the rising unworked shoulder. These are earth banks, not walls.
            for i in (0,front_end(k)):
                q=[(*outer[i],z),(*inner[i],z),(*inner[i],h)]
                m.face(q,'earth','bench_end_bank');m.face(q[::-1],'earth','bench_end_bank')
        # Small rock breaks interrupt the unworked shoulder silhouette.
        rng=np.random.default_rng(111)
        for x,y,r in [(1.2,2.4,.28),(-.6,2.85,.22),(2.0,2.0,.18),(.65,1.35,.24)]:
            z=surface_height(kind,x,y);cluster(m,(x,y,z+.08),(r,r*.74,r*.9),'rock','shoulder_stones',rng,7,2)
    network(m,kind,state=='Wet')
    planted_trees(m,kind,state,lod)
    x,y=(2.5,-2.5) if kind=='Flat' else (-2.4,-3.65)
    farmstead(m,x,y,surface_height(kind,x,y)+.02,state)
    m.meta={'category':'tile','terrain':kind,'state':state,'lod':lod,'tile_radius':B.R,'inlet':inlet(kind).tolist(),
            'surface_policy':'partial cultivated benches with unworked sloping shoulders; normalized source terrain',
            'water_network':{'root':'flat_supply' if kind=='Flat' else 'mountain_receiver_drop','routes':len(m.routes),'gravity':'every route level or falling'},
            'edge_ports':[{'edge':i,'xy':[B.A*math.cos(i*math.pi/3),B.A*math.sin(i*math.pi/3)]} for i in range(6)]}
    return m

def scene():
    m=Mesh('RT_IF_ConnectedDistrict')
    layout=[(-1,1,'RockyFoothill'),(0,1,'SteepHill'),(0,0,'GentleHill'),(-1,0,'Flat'),(1,0,'Flat'),(0,-1,'Flat')]
    samples=[]
    for q,r,kind in layout:
        xy=B.axial(q,r);part=tile(kind,origin=xy);m.append(part,(*xy,0),prefix=f'tile_{q}_{r}_')
        samples.append({'q':q,'r':r,'kind':kind,'center':xy.tolist(),'inlet':(inlet(kind)+[*xy,0]).tolist()})
    def ground(x,y):
        for e in samples:
            xy=np.array((x,y))-e['center']
            if B.in_poly(xy,B.HEX):return surface_height(e['kind'],*xy)
        return 0.
    source=np.array((-16.2,13.6,inlet('RockyFoothill')[2]+.12));graph=[]
    for parent,child in [(-1,0),(0,1),(1,2),(0,3),(2,4),(2,5)]:
        end=np.array(samples[child]['inlet'])
        if parent==-1:start=source
        elif samples[child]['kind']=='Flat':
            e=samples[parent];options=header(e['kind'],0)+[*e['center'],0]
            start=options[np.argmin(np.linalg.norm(options[:,:2]-end[:2],axis=1))].copy()
        else:start=np.array(samples[parent]['inlet'])
        B.bridge(m,start,end,ground=ground,part=f'feeder_{parent}_{child}')
        if parent>=0:
            owner=samples[parent];prefix=f'tile_{owner["q"]}_{owner["r"]}_'
            m.routes[-1]['upstream']=prefix+('bench_0_contour' if samples[child]['kind']=='Flat' else 'mountain_receiver_drop')
        dest=samples[child];root=f'tile_{dest["q"]}_{dest["r"]}_'+('flat_supply' if dest['kind']=='Flat' else 'mountain_receiver_drop')
        next(r for r in m.routes if r['name']==root)['upstream']=f'feeder_{parent}_{child}'
        graph.append({'parent':parent,'child':child,'start':start.tolist(),'end':end.tolist()})
    # Source socket only; native mountains belong to the game and are not
    # represented by the rejected generic cone in this model review.
    m.box((source[0]-.12,source[1],source[2]-.2),(.42,.50,.50),'stone','source_socket')
    m.meta={'category':'assembly','tiles':samples,'source':source.tolist(),'feeder_graph':graph,
            'water_network':{'root':'feeder_-1_0','routes':len(m.routes)},'native_status':'source assembly; native integration pending'}
    return m
