"""R3: shared crop/ditch boundaries and open, straight gentle-hill terraces."""
from contextlib import contextmanager
from collections import deque
from functools import lru_cache
import math
import numpy as np
from build_concept_models import natural, v3, Mesh, unit
import concept_revision_geometry as r2

ANGLE=.19
ROT=np.array([[math.cos(ANGLE),-math.sin(ANGLE)],[math.sin(ANGLE),math.cos(ANGLE)]])
MARGIN=.125
WATER_Z=.145
MINOR_WIDTH=.10
MAIN_WIDTH=.16
# Each line runs left -> right. Deliberately unequal width, skew and spacing;
# the terraces climb one open slope instead of wrapping a radial hill.
LINES=np.array([[[-4.05,-1.85],[4.10,-1.43]],
                [[-3.65,-.18],[3.85,.09]],
                [[-2.95,1.58],[3.26,1.32]],
                [[-1.74,3.47],[2.12,3.20]]])
LEVELS=[.28,.56,.84]


def y_edge(i):return i*2.7+.17*math.sin(i*2.1)
def x_edge(i,row):return i*3.+.62*(row%2)+.31*math.sin(i*1.8)


def clip(poly,normal,limit,inside=True):
    """Clip a convex polygon against any directed half-plane."""
    poly=np.asarray(poly);out=[]
    if len(poly)<3:return []
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        da=np.dot(a,normal)-limit;db=np.dot(b,normal)-limit
        ia=da<=1e-8 if inside else da>=-1e-8;ib=db<=1e-8 if inside else db>=-1e-8
        if ia:out.append(a)
        if ia!=ib:out.append(a+(b-a)*da/(da-db))
    return v3.clean(out)


def subtract(poly,hole):
    """Convex pieces outside a convex hole, without a geometry dependency."""
    current=poly;pieces=[]
    for a,b in zip(hole,np.roll(hole,-1,axis=0)):
        d=b-a;normal=np.array([d[1],-d[0]]);limit=np.dot(a,normal)
        outside=clip(current,normal,limit,False)
        if outside:pieces.append(outside)
        current=clip(current,normal,limit)
        if not current:break
    return pieces


def crop_patches(m,poly,z,origin,state,margin=MARGIN):
    """Same global partition supplies both crop cutouts and ditch centerlines."""
    world=(np.asarray(poly)+origin)@ROT
    for row in range(math.floor(world[:,1].min()/2.7)-1,math.ceil(world[:,1].max()/2.7)+1):
        for col in range(math.floor(world[:,0].min()/3)-2,math.ceil(world[:,0].max()/3)+2):
            bounds=(x_edge(col,row),x_edge(col+1,row),y_edge(row),y_edge(row+1))
            p=world.copy()
            for axis,lim,gt in [(0,bounds[0]+margin,True),(0,bounds[1]-margin,False),(1,bounds[2]+margin,True),(1,bounds[3]-margin,False)]:p=v3.clip(p,axis,lim,gt)
            p=v3.clean(p)
            if not p:continue
            p=np.array(p);mat=['barley','vegetables','legumes','stubble','vegetables','legumes','barley'][(col*3+row*2)%7]
            if state=='Dry':mat='dry_crop'
            if state=='Pillaged':mat='stubble'
            if state=='Construction':continue
            for tx in range(math.floor(p[:,0].min()/2.4),math.floor(p[:,0].max()/2.4)+1):
                for ty in range(math.floor(p[:,1].min()/2.4),math.floor(p[:,1].max()/2.4)+1):
                    sub=p.copy()
                    for axis,lim,gt in [(0,tx*2.4,True),(0,(tx+1)*2.4,False),(1,ty*2.4,True),(1,(ty+1)*2.4,False)]:sub=v3.clip(sub,axis,lim,gt)
                    sub=v3.clean(sub)
                    if not sub:continue
                    sub=np.array(sub);local=sub@ROT.T-origin
                    m.face([(*q,z+.013) for q in local],mat,'crop_surface',(sub-[tx*2.4,ty*2.4])/2.4)


def segment_clip(a,b,poly):
    a,b=np.asarray(a),np.asarray(b);lo=0.;hi=1.;d=b-a
    for p,q in zip(poly,np.roll(poly,-1,axis=0)):
        edge=q-p;n=np.array([edge[1],-edge[0]]);numerator=np.dot(p-a,n);denom=np.dot(d,n)
        if abs(denom)<1e-10:
            if numerator<0:return None
        elif denom>0:hi=min(hi,numerator/denom)
        else:lo=max(lo,numerator/denom)
    if hi-lo<1e-5:return None
    return a+d*lo,a+d*hi


def parcel_graph(origin=(0,0),neighbors=(),toward=(0,1)):
    """Clip actual parcel seams; split every T junction before hydraulic routing."""
    origin=np.asarray(origin);poly=v3.HEX.copy()
    # Only shared flat-farm edges stay open. Exposed ends finish inside the tile.
    for edge in range(6):
        n=np.array([math.cos(edge*math.pi/3),math.sin(edge*math.pi/3)])
        poly=clip(poly,n,v3.A-(0 if edge in neighbors else .38))
    world=(np.array(poly)+origin)@ROT;segments=[]
    xmin,xmax=world[:,0].min()-1,world[:,0].max()+1
    for row in range(math.floor(world[:,1].min()/2.7)-1,math.ceil(world[:,1].max()/2.7)+1):
        seg=segment_clip([xmin,y_edge(row)],[xmax,y_edge(row)],world)
        if seg:segments.append((*seg,MAIN_WIDTH,'row',row))
        for col in range(math.floor(xmin/3)-2,math.ceil(xmax/3)+2):
            seg=segment_clip([x_edge(col,row),y_edge(row)],[x_edge(col,row),y_edge(row+1)],world)
            if seg:segments.append((*seg,MINOR_WIDTH,'column',row))
    nodes={};edges=[]
    def node(p):
        for key,index in nodes.items():
            if np.linalg.norm(np.array(key)-p)<1e-6:return index
        key=tuple(np.round(p,8))
        if key not in nodes:nodes[key]=len(nodes)
        return nodes[key]
    for a,b,w,axis,row in segments:
        cuts=[0.,1.];d=b-a
        for c,e,*_ in segments:
            for p in (c,e):
                t=np.dot(p-a,d)/np.dot(d,d)
                if 1e-7<t<1-1e-7 and np.linalg.norm(a+t*d-p)<1e-6:cuts.append(float(t))
        cuts=sorted(set(round(t,9) for t in cuts))
        for t,u in zip(cuts,cuts[1:]):
            if u-t<1e-6:continue
            edges.append(dict(a=node(a+t*d),b=node(a+u*d),width=w,axis=axis,row=row))
    # A clipped corner plot can have a short seam whose junction lies outside
    # this tile. Connect those seams along the field margin, not across crops.
    perimeter=np.r_[0,np.cumsum(np.linalg.norm(np.roll(world,-1,axis=0)-world,axis=1))]
    def station(point):
        best=(1e9,0.)
        for i,(a,b) in enumerate(zip(world,np.roll(world,-1,axis=0))):
            d=b-a;t=np.clip(np.dot(point-a,d)/np.dot(d,d),0,1);distance=np.linalg.norm(point-a-t*d)
            if distance<best[0]:best=(distance,perimeter[i]+t*(perimeter[i+1]-perimeter[i]))
        return best
    while True:
        adjacency={i:[] for i in range(len(nodes))}
        for e in edges:adjacency[e['a']].append(e['b']);adjacency[e['b']].append(e['a'])
        groups=[];seen=set()
        for first in adjacency:
            if first in seen:continue
            pending=[first];component=set()
            while pending:
                i=pending.pop()
                if i in component:continue
                component.add(i);pending.extend(adjacency[i])
            groups.append(component);seen.update(component)
        if len(groups)==1:break
        groups.sort(key=len,reverse=True);coords=np.array(list(nodes));choice=None
        for a in groups[0]:
            da,sa=station(coords[a])
            if da>1e-5:continue
            for group in groups[1:]:
                for b in group:
                    db,sb=station(coords[b])
                    if db>1e-5:continue
                    forward=(sb-sa)%perimeter[-1];backward=perimeter[-1]-forward
                    option=(min(forward,backward),a,b,sa,sb,forward<=backward)
                    if choice is None or option[0]<choice[0]:choice=option
        assert choice is not None,'no field-margin connection'
        _,a,b,sa,sb,forward=choice
        if not forward:a,b,sa,sb=b,a,sb,sa
        if sb<sa:sb+=perimeter[-1]
        route=[a]
        for s,index in sorted((float(s+offset),i) for offset in (0,perimeter[-1]) for i,s in enumerate(perimeter[:-1])):
            if sa+1e-6<s<sb-1e-6:route.append(node(world[index]))
        route.append(b)
        for x,y in zip(route,route[1:]):edges.append(dict(a=x,b=y,width=MINOR_WIDTH,axis='field_margin',row=None))
    coordinates=np.array(list(nodes));local=coordinates@ROT.T-origin;adj={i:[] for i in range(len(local))}
    for i,e in enumerate(edges):adj[e['a']].append(i);adj[e['b']].append(i)
    leaves=[i for i in adj if len(adj[i])==1]
    direction=unit(np.asarray(toward));root=max(leaves,key=lambda i:np.dot(local[i],direction)-.10*abs(np.cross(direction,local[i])))
    open_nodes=set()
    for i in leaves:
        for edge in neighbors:
            n=np.array([math.cos(edge*math.pi/3),math.sin(edge*math.pi/3)])
            if abs(np.dot(local[i],n)-v3.A)<1e-5:open_nodes.add(i)
    return dict(points=local,world=coordinates,edges=edges,adj=adj,root=root,open_nodes=open_nodes)


def parcel_network(m,graph,wet):
    pts=graph['points'];adj=graph['adj'];edges=graph['edges'];root=graph['root']
    queue=deque([root]);incoming={root:None};used=set();ordered=[]
    while queue:
        a=queue.popleft()
        for index in adj[a]:
            if index in used:continue
            used.add(index);e=edges[index];b=e['b'] if e['a']==a else e['a']
            name='flat_supply' if not ordered else f'plot_seam_{index}'
            ordered.append((a,b,name,incoming[a],e))
            if b not in incoming:incoming[b]=name;queue.append(b)
    assert len(used)==len(edges),'disconnected parcel seam graph'
    for a,b,name,parent,e in ordered:
        start=np.r_[pts[a],WATER_Z];end=np.r_[pts[b],WATER_Z]
        joints=[p for i,p in [(a,start),(b,end)] if len(adj[i])>1]
        natural.trough(m,[start,end],name,wet,e['width'],gaps=joints,parent=parent)
        terminal=len(adj[b])==1 and b not in graph['open_nodes']
        m.routes[-1].update(kind='parcel_canal',end='closed_field_outlet' if terminal else 'open_joint',
                           parcel_axis=e['axis'],parcel_row=e['row'])
        if terminal:r2.endcap(m,end,end-start,e['width'],name)
    return np.r_[pts[root],WATER_Z]



def clear_prop_position(desired,routes,radius):
    """Move existing props off the newly shared parcel ditches and tile edge."""
    starts=[];ends=[];widths=[]
    for r in routes:
        for a,b in zip(r['points'],r['points'][1:]):
            starts.append(a[:2]);ends.append(b[:2]);widths.append(r['width'])
    a=np.array(starts);d=np.array(ends)-a;widths=np.array(widths)
    normals=np.array([[math.cos(i*math.pi/3),math.sin(i*math.pi/3)] for i in range(6)])
    offsets=sorted(((x*.15,y*.15) for x in range(-16,17) for y in range(-16,17)),key=lambda p:p[0]**2+p[1]**2)
    for delta in offsets:
        p=np.array(desired)+delta
        if (normals@p>v3.A-radius).any():continue
        t=np.clip(np.sum((p-a)*d,axis=1)/np.sum(d*d,axis=1),0,1)
        if np.all(np.linalg.norm(p-a-t[:,None]*d,axis=1)>radius+widths/2+.065):return p
    raise ValueError('no clear parcel position for prop')


def flat_props(m,state,lod):
    if state not in ('Wet','Dry'):return
    rng=np.random.default_rng(719)
    spots=[(-3.65,2.3),(-2.7,3.95),(-1.2,3.5),(.4,3.55),(2.6,2.9),(3.7,1.1),(-3.9,-.7)]
    for i,spot in enumerate(spots):
        x,y=clear_prop_position(spot,m.routes,.24)
        tree=natural.palm(lod) if i in (0,2,4) else natural.orchard(lod,seed=123+i)
        scale=rng.uniform(.72,1.08)
        tree.faces=[(p*scale,n,uv,mat,part) for p,n,uv,mat,part in tree.faces]
        m.append(tree,(x,y,.02),angle=rng.uniform(0,360))
    x,y=clear_prop_position((2.5,-2.5),m.routes,.82)
    natural.farmstead(m,x,y,.02,state)


def flat_tile(state='Wet',lod=0,origin=(0,0),neighbors=(),toward=(0,1)):
    m=Mesh('RT_IF_Flat_'+state+('_LOD1' if lod else ''));m.lod=lod
    for i in range(6):m.face([(*v3.HEX[i],0),(*v3.HEX[(i+1)%6],0),(0,0,0)],'earth','terrain_surface')
    crop_patches(m,v3.HEX,0,np.array(origin),state)
    graph=parcel_graph(origin,neighbors,toward);root=parcel_network(m,graph,state=='Wet')
    trim_crops(m,[r for r in m.routes if r['parcel_axis']=='field_margin'])
    flat_props(m,state,lod)
    m.meta=dict(category='tile',terrain='Flat',state=state,lod=lod,tile_radius=v3.R,inlet=root.tolist(),
                parcel_origin=list(origin),parcel_channels=True,parcel_margin=MARGIN,
                water_network=dict(root='flat_supply',routes=len(m.routes)),
                edge_ports=[dict(node=i,xy=graph['points'][i].tolist()) for i in sorted(graph['open_nodes'])])
    return m


def gentle_header(k):
    if k==0:
        a,b=LINES[0];p=np.linspace(a,b,9);p[:,1]-=.34
        p[-1,:]+=unit(b-a)*.65
        return np.c_[p,np.full(9,WATER_Z)]
    # Along the upslope edge of each planted bench; a real corridor is reserved
    # in the crop polygons, rather than laying a gutter over the crop pixels.
    lower,upper=LINES[k-1],LINES[k];p=np.linspace(upper[0]*.84+lower[0]*.16,upper[1]*.84+lower[1]*.16,9)
    return np.c_[p,np.full(9,LEVELS[k-1]+WATER_Z)]


def gentle_inlet():
    p=gentle_header(3)[0].copy();p[:2]+=[-.45,-.05];p[2]=1.30;return p


def wall(m,a,b,low,high,name):
    d=b-a;side=unit(np.array([-d[1],d[0]]))*.05
    m.face([(*a,low),(*b,low),(*(b+side),high),(*(a+side),high)],'stone',name)
    m.face([(*(a+side),high),(*(b+side),high),(*(b+side*1.9),high),(*(a+side*1.9),high)],'coping',name+'_coping')


@lru_cache(None)
def gentle_surfaces():
    surfaces=[]
    for i in range(6):surfaces.append(np.array([(*v3.HEX[i],0),(*v3.HEX[(i+1)%6],0),(0,0,0)]))
    for k,z in enumerate(LEVELS):
        a,b=LINES[k];d,c=LINES[k+1];quad=np.c_[[a,b,c,d],np.full(4,z)]
        surfaces.extend([quad[[0,1,2]],quad[[0,2,3]]])
        for p,q,sign in [(a,d,-1),(c,b,1)]:
            # Earth shoulders taper into the surrounding land, not a circular
            # stone enclosure around a miniature hill.
            step=np.array([sign*.48,0]);f=np.array([(*p,z),(*q,z),(*(q+step),0),(*(p+step),0)])
            for ids in ([0,1,2],[0,2,3]):
                tri=f[ids]
                if np.cross(tri[1]-tri[0],tri[2]-tri[0])[2]<0:tri=tri[::-1]
                surfaces.append(tri)
    a,b=LINES[-1];q=np.array([(*a,LEVELS[-1]),(*b,LEVELS[-1]),(*(b+[0,.48]),0),(*(a+[0,.48]),0)])
    surfaces.extend([q[[0,1,2]],q[[0,2,3]]]);return surfaces


def gentle_height(x,y):
    best=0.
    for tri in gentle_surfaces()[6:]:
        a=tri[1,:2]-tri[0,:2];b=tri[2,:2]-tri[0,:2];d=np.array([x,y])-tri[0,:2]
        den=np.cross(a,b)
        if abs(den)<1e-10:continue
        u=np.cross(d,b)/den;v=np.cross(a,d)/den
        if u>=-1e-7 and v>=-1e-7 and u+v<=1+1e-7:best=max(best,float(tri[0,2]*(1-u-v)+tri[1,2]*u+tri[2,2]*v))
    return best


def gentle_network(m,wet,openings=None):
    openings=openings or {};root=gentle_inlet();head=gentle_header(3)
    approach=np.r_[head[0,:2]+[-.08,0],root[2]]
    natural.trough(m,[root,approach,head[0]],'mountain_receiver_drop',wet,.20,gaps=openings.get('mountain_receiver_drop',[]))
    m.routes[-1]['kind']='lined_drop';r2.support(m,[root,approach,head[0]],gentle_height,'upper_receiver')
    for k in range(3,-1,-1):
        h=gentle_header(k);name=f'bench_{k}_contour';parent='mountain_receiver_drop' if k==3 else f'drop_{k+1}_{k}'
        natural.trough(m,h,name,wet,.17,parent=parent,gaps=openings.get(name,[]))
        end_open=any(np.linalg.norm(np.array(p)-h[-1])<1e-6 for p in openings.get(name,[]))
        m.routes[-1].update(kind='terrace_canal',end='open_joint' if end_open else 'closed_field_outlet')
        if not end_open:r2.endcap(m,h[-1],h[-1]-h[-2],.17,name)
        if k:
            lower=gentle_header(k-1)[0];edge=LINES[k-1][0]
            # Descend in the open left-hand shoulder, clear of the retaining wall.
            route=[h[0],np.r_[edge+[-.22,.08],h[0,2]],np.r_[edge+[-.24,-.16],lower[2]],lower]
            natural.trough(m,route,f'drop_{k}_{k-1}',wet,.18,parent=name)
            m.routes[-1]['kind']='lined_drop';r2.support(m,route,gentle_height,f'drop_{k}_{k-1}')


def corridor(a,b,width):
    d=b-a;side=unit(np.array([-d[1],d[0]]))*width
    return np.array([a-side,b-side,b+side,a+side])


def trim_crops(m,routes):
    """Reserve earth/canal corridors: exported crop triangles cannot cover water."""
    faces=m.faces;m.faces=[]
    holes=[]
    for r in routes:
        for a,b in zip(np.array(r['points']),np.array(r['points'])[1:]):
            holes.append((a,b,corridor(a[:2],b[:2],r['width']/2+.065)))
    for p,n,uv,mat,part in faces:
        if not part.endswith('crop_surface'):m.faces.append((p,n,uv,mat,part));continue
        fragments=[p[:,:2]];z=p[0,2]
        for a,b,hole in holes:
            if max(a[2],b[2])-z>.26 or min(a[2],b[2])<z+.03:continue
            lo=hole.min(0);hi=hole.max(0)
            if (p[:,:2].max(0)<lo).any() or (p[:,:2].min(0)>hi).any():continue
            fragments=[q for poly in fragments for q in subtract(poly,hole)]
        basis=np.array([p[1,:2]-p[0,:2],p[2,:2]-p[0,:2]]).T
        for poly in fragments:
            poly=np.asarray(poly);bary=np.linalg.solve(basis,(poly-p[0,:2]).T).T
            tex=uv[0]+bary[:,0,None]*(uv[1]-uv[0])+bary[:,1,None]*(uv[2]-uv[0])
            for i in range(1,len(poly)-1):
                ids=[0,i,i+1];tri=np.c_[poly[ids],np.full(3,z)]
                if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))>1e-6:m.faces.append((tri,n,tex[ids],mat,part))


def gentle_tile(state='Wet',lod=0,origin=(0,0),openings=None):
    m=Mesh('RT_IF_GentleHill_'+state+('_LOD1' if lod else ''));m.lod=lod
    for tri in gentle_surfaces():m.face(tri,'earth','terrain_surface')
    footprint=np.array([LINES[0,0]+[-.52,-.05],LINES[0,1]+[.52,-.05],LINES[-1,1]+[.52,.52],LINES[-1,0]+[-.52,.52]])
    for poly in subtract(v3.HEX,footprint):crop_patches(m,poly,0,np.array(origin),state)
    for k,z in enumerate(LEVELS):
        a,b=LINES[k];d,c=LINES[k+1];crop_patches(m,[a,b,c,d],z,np.array(origin),state)
        wall(m,a,b,0 if k==0 else LEVELS[k-1],z,'retaining_wall')
    gentle_network(m,state=='Wet',openings)
    trim_crops(m,m.routes)
    natural.farmstead(m,-2.8,-3.25,.02,state)
    # A few trees at the dry field margins; no dome or rocky summit cap.
    if state in ('Wet','Dry'):
        for i,(x,y) in enumerate([(-4.6,.8),(4.55,.6),(-2.25,3.95)]):
            tree=natural.orchard(lod,seed=170+i);tree.faces=[(p*.72,n,uv,mat,part) for p,n,uv,mat,part in tree.faces];m.append(tree,(x,y,gentle_height(x,y)))
    m.meta=dict(category='tile',terrain='GentleHill',state=state,lod=lod,tile_radius=v3.R,inlet=gentle_inlet().tolist(),
                parcel_origin=list(origin),gentle_shape='three staggered straight benches; cultivated upper bench; no radial crown',
                water_network=dict(root='mountain_receiver_drop',routes=len(m.routes)))
    return m


@contextmanager
def geometry(regular):
    with r2.geometry(regular):
        old_tile=natural.tile;old_height=natural.surface_height
        def tile(kind,state='Wet',lod=0,origin=(0,0),name=None):
            if kind=='Flat':return flat_tile(state,lod,origin)
            if kind=='GentleHill':return gentle_tile(state,lod,origin)
            return old_tile(kind,state,lod,origin,name)
        natural.tile=tile
        natural.surface_height=lambda kind,x,y:gentle_height(x,y) if kind=='GentleHill' else old_height(kind,x,y)
        try:yield
        finally:natural.tile=old_tile;natural.surface_height=old_height


def scene():
    m=Mesh('RT_IF_ConnectedDistrict')
    layout=[(-1,1,'RockyFoothill'),(0,1,'SteepHill'),(0,0,'GentleHill'),(-1,0,'Flat'),(1,0,'Flat'),(0,-1,'Flat')]
    parents={0:-1,1:0,2:1,3:0,4:2,5:2};samples=[]
    for i,(q,r,kind) in enumerate(layout):
        xy=v3.axial(q,r);neighbors=[];toward=(0,1)
        if kind=='Flat':
            toward=v3.axial(*layout[parents[i]][:2])-xy
            for oq,orr,other in layout:
                delta=v3.axial(oq,orr)-xy
                if other=='Flat' and abs(np.linalg.norm(delta)-2*v3.A)<1e-6:
                    neighbors.append(round(math.atan2(delta[1],delta[0])/(math.pi/3))%6)
            graph=parcel_graph(xy,neighbors,toward);root=np.r_[graph['points'][graph['root']],WATER_Z]
        else:root=gentle_inlet() if kind=='GentleHill' else r2.inlet(kind)
        samples.append(dict(q=q,r=r,kind=kind,center=xy.tolist(),inlet=(root+[*xy,0]).tolist(),neighbors=neighbors,toward=list(toward)))
    source=np.array(samples[0]['inlet'])+[-8,-.15,.1];links=[];openings={}
    for child,parent in parents.items():
        end=np.array(samples[child]['inlet']);upstream=None
        if parent<0:start=source
        else:
            owner=samples[parent]
            if samples[child]['kind']=='Flat':
                options=gentle_header(0) if owner['kind']=='GentleHill' else r2.header(owner['kind'],0)
                index=np.argmin(np.linalg.norm((options+[*owner['center'],0])[:,:2]-end[:2],axis=1))
                local=options[index];start=local+[*owner['center'],0];name='bench_0_contour'
            else:
                start=np.array(owner['inlet']);local=start-[*owner['center'],0];name='mountain_receiver_drop'
            openings.setdefault(owner['kind'],{}).setdefault(name,[]).append(local)
            upstream=f'tile_{owner["q"]}_{owner["r"]}_'+name
        links.append((parent,child,start,end,upstream))
    previous=natural.network
    try:
        for e in samples:
            kind=e['kind']
            if kind=='Flat':part=flat_tile(origin=e['center'],neighbors=e['neighbors'],toward=e['toward'])
            elif kind=='GentleHill':part=gentle_tile(origin=e['center'],openings=openings.get(kind,{}))
            else:
                natural.network=lambda mesh,k,wet:r2.network(mesh,k,wet,openings.get(k,{}))
                part=natural.tile(kind,origin=e['center'])
            m.append(part,(*e['center'],0),prefix=f'tile_{e["q"]}_{e["r"]}_')
    finally:natural.network=previous
    def ground(x,y):
        for e in samples:
            xy=np.array([x,y])-e['center']
            if v3.in_poly(xy,v3.HEX):return natural.surface_height(e['kind'],*xy)
        return 0.
    graph=[];feeders=[]
    for parent,child,start,end,upstream in links:
        dest=samples[child];name=f'feeder_{parent}_{child}'
        key=f'tile_{dest["q"]}_{dest["r"]}_'+('flat_supply' if dest['kind']=='Flat' else 'mountain_receiver_drop')
        route=next(r for r in m.routes if r['name']==key);tangent=(np.array(route['points'])[1]-end)[:2]
        before=len(m.routes)
        if parent==2 and child==4:
            # Keep this low connector outside the newly widened gentle terrace.
            # It is a ground-level carrier, not an inclined aqueduct ramp.
            tangent=unit(tangent);receiver_start=end-np.r_[tangent*.30,0.]
            approach=end[:2]-tangent*.90
            xy=r2.rounded([start[:2],approach,receiver_start[:2]],radius=.24,steps=10)
            natural.trough(m,np.c_[xy,np.full(len(xy),WATER_Z)],name,True,.16,parent=upstream)
            m.routes[-1]['kind']='field_margin_connector'
            receiver=name+'_receiver';natural.trough(m,[receiver_start,end],receiver,True,.16,parent=name)
            m.routes[-1]['kind']='receiving_channel'
        else:receiver=r2.feeder(m,start,end,tangent,ground,name,upstream)
        route['upstream']=receiver
        feeders.extend(m.routes[before:]);graph.append(dict(parent=parent,child=child,start=start.tolist(),end=end.tolist(),span=name,receiver=receiver))
    # Incoming connectors also reserve actual soil space in the field geometry.
    trim_crops(m,feeders)
    m.box((source[0]-.12,source[1],source[2]-.2),(.42,.50,.50),'stone','source_socket')
    m.meta=dict(category='assembly',tiles=samples,source=source.tolist(),feeder_graph=graph,
                water_network=dict(root='feeder_-1_0',routes=len(m.routes)),native_status='offline review only')
    return m
