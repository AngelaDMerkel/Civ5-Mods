"""R4: angular farm steps, tier-fitted crop parcels and visible central cascades."""
from contextlib import contextmanager
from functools import lru_cache
import math
import numpy as np
from build_concept_models import natural, v3, Mesh, unit
import concept_revision_geometry as r2
import concept_parcel_geometry as r3

# Straight front/back lines bound each trapezoidal bench, rather than concentric
# rings. All three hill forms have a cultivated top and a distinct stepped rise.
SHAPES={
    'GentleHill':dict(lines=[[[-4.15,-2.00],[4.05,-1.75]],[[-3.65,-.30],[3.70,-.10]],[[-2.85,1.45],[3.05,1.60]],[[-1.85,3.35],[2.10,3.45]]],heights=[.42,.88,1.36]),
    'SteepHill':dict(lines=[[[-4.15,-2.15],[4.15,-1.90]],[[-3.50,-.45],[3.70,-.15]],[[-2.75,1.30],[2.95,1.55]],[[-1.80,3.30],[1.95,3.50]]],heights=[.85,1.80,2.80]),
    'RockyFoothill':dict(lines=[[[-4.25,-2.05],[3.95,-1.80]],[[-3.65,-.35],[3.45,-.05]],[[-2.85,1.35],[2.65,1.65]],[[-1.90,3.25],[1.70,3.60]]],heights=[1.00,2.10,3.25])}
WATER=.145
SPINE_WIDTH=.22
HEADER_WIDTH=.16


def lines(kind):return np.array(SHAPES[kind]['lines'])
def heights(kind):return SHAPES[kind]['heights']


def point(kind,k,u,v):
    a,b=lines(kind)[k];d,c=lines(kind)[k+1]
    return (a*(1-u)+b*u)*(1-v)+(d*(1-u)+c*u)*v


def front(kind,k):return point(kind,k,.5,0)
def down(kind,k):return unit(front(kind,k)-point(kind,k,.5,1))
def spine(kind,k):return np.array([np.r_[point(kind,k,.5,v),heights(kind)[k]+WATER] for v in (.91,.16)])


def inlet(kind):
    p=spine(kind,2)[0].copy();p[:2]-=down(kind,2)*.45;p[2]+=.12;return p


def ground_headers(kind):
    a,b=lines(kind)[0];d=down(kind,0);center=(a+b)/2+d*.48
    # Clear the side shoulders before sending a low connector to a neighbor.
    return [np.c_[[center,a+d*.48+[-.48,0]],np.full(2,WATER)],
            np.c_[[center,b+d*.48+[.48,0]],np.full(2,WATER)]]


def cascade(kind,k):
    start=spine(kind,k)[-1];edge=front(kind,k);direction=down(kind,k)
    end=spine(kind,k-1)[0] if k else ground_headers(kind)[0][0]
    lip=np.r_[edge+direction*.075,start[2]]
    run=end[:2]-lip[:2];rise=start[2]-end[2];count=math.ceil(rise/.18)
    path=[start,lip]
    for j in range(count):
        # Each short level tread precedes a near-vertical face of visible water.
        a=lip.copy();a[:2]+=run*(j+.65)/count;a[2]-=rise*j/count
        b=lip.copy();b[:2]+=run*(j+1)/count;b[2]-=rise*(j+1)/count
        path.extend([a,b])
    return np.array(path)


def hull(points):
    points=sorted(set(map(tuple,points)))
    def half(seq):
        result=[]
        for p in seq:
            while len(result)>1 and np.cross(np.subtract(result[-1],result[-2]),np.subtract(p,result[-1]))<=0:result.pop()
            result.append(p)
        return result
    return np.array(half(points)[:-1]+half(points[::-1])[:-1])


@lru_cache(None)
def terrain(kind):
    result=[];ls=lines(kind)
    for i in range(6):result.append(np.array([(*v3.HEX[i],0),(*v3.HEX[(i+1)%6],0),(0,0,0)]))
    for k,z in enumerate(heights(kind)):
        a,b=ls[k];d,c=ls[k+1];quad=np.array([(*a,z),(*b,z),(*c,z),(*d,z)])
        result.extend([quad[[0,1,2]],quad[[0,2,3]]])
        # Planar earth/rock shoulders meet straight masonry returns. No radial
        # subdivisions or smooth crown surface are introduced.
        for p,q,offset in [(a,d,[-.32,0]),(c,b,[.32,0])]:
            face=np.array([(*p,z),(*q,z),(*(q+offset),0),(*(p+offset),0)])
            for ids in ([0,1,2],[0,2,3]):
                tri=face[ids]
                if np.cross(tri[1]-tri[0],tri[2]-tri[0])[2]<0:tri=tri[::-1]
                result.append(tri)
    a,b=ls[-1];z=heights(kind)[-1];f=np.array([(*a,z),(*b,z),(*(b+[0,.35]),0),(*(a+[0,.35]),0)])
    result.extend([f[[0,1,2]],f[[0,2,3]]]);return result


def height(kind,x,y):
    best=0.
    for tri in terrain(kind)[6:]:
        a=tri[1,:2]-tri[0,:2];b=tri[2,:2]-tri[0,:2];q=np.array([x,y])-tri[0,:2];den=np.cross(a,b)
        if abs(den)<1e-10:continue
        u=np.cross(q,b)/den;v=np.cross(a,q)/den
        if u>=-1e-7 and v>=-1e-7 and u+v<=1+1e-7:best=max(best,float(tri[:,2]@[1-u-v,u,v]))
    return best


def retaining_front(m,kind,k):
    a,b=lines(kind)[k];z=heights(kind)[k];low=heights(kind)[k-1] if k else 0.
    gap=(SPINE_WIDTH/2+.09)/np.linalg.norm(b-a)
    # Actual opening through both the wall and coping for the cascade, not a
    # water ribbon laid across an intact parapet.
    for u,v in [(0,.5-gap),(.5+gap,1)]:
        p=a*(1-u)+b*u;q=a*(1-v)+b*v
        r3.wall(m,p,q,low,z,f'tier_{k}_retaining_front')
    # Angular short masonry returns keep the stepped footprint legible at a
    # shallow viewing angle, while the outside shoulders remain faceted terrain.
    d,c=lines(kind)[k+1]
    for p,q in [(d,a),(b,c)]:
        direction=unit(q-p)*.055
        m.face([(*p,z-.16),(*q,z-.16),(*(q+direction),z),(*(p+direction),z)],'stone',f'tier_{k}_side_return')


def tier_crops(m,kind,k,state):
    z=heights(kind)[k];records=[]
    # Plot outlines follow the actual terrace. Texture repeat subdivisions stay
    # within each parcel; no world-grid crop strip continues over a riser.
    for side,(u0,u1) in enumerate([(.055,.465),(.535,.945)]):
        v0,v1=.265,.93
        polygon=np.array([point(kind,k,u,v) for u,v in [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]])
        material=['vegetables','barley','legumes','vegetables','barley','stubble'][k*2+side]
        if state=='Dry':material='dry_crop'
        part=f'tier_{k}_plot_{side}_crop_surface'
        width=(np.linalg.norm(polygon[1]-polygon[0])+np.linalg.norm(polygon[2]-polygon[3]))/2
        depth=(np.linalg.norm(polygon[3]-polygon[0])+np.linalg.norm(polygon[2]-polygon[1]))/2
        # Texture rows align with the long straight front of this tier.
        nx=max(1,math.ceil(width/2.4));ny=max(1,math.ceil(depth/2.4))
        for i in range(nx):
            for j in range(ny):
                us=[u0+(u1-u0)*i/nx,u0+(u1-u0)*(i+1)/nx];vs=[v0+(v1-v0)*j/ny,v0+(v1-v0)*(j+1)/ny]
                m.face([(*point(kind,k,u,v),z+.013) for u,v in [(us[0],vs[0]),(us[1],vs[0]),(us[1],vs[1]),(us[0],vs[1])]],material,part,[(0,0),(width/nx/2.4,0),(width/nx/2.4,depth/ny/2.4),(0,depth/ny/2.4)])
        records.append(dict(group=part,tier=k,polygon=polygon.tolist(),elevation=z,material=material))
    return records


def network(m,kind,wet,openings=None):
    openings=openings or {};top=spine(kind,2)[0];root=inlet(kind)
    natural.trough(m,[root,np.r_[top[:2]-down(kind,2)*.06,root[2]],top],'mountain_receiver_drop',wet,SPINE_WIDTH,gaps=openings.get('mountain_receiver_drop',[]))
    m.routes[-1]['kind']='lined_drop';r2.support(m,[root,top],lambda x,y:height(kind,x,y),'upper_receiver')
    for k in range(2,-1,-1):
        path=spine(kind,k);name=f'tier_{k}_spine';parent='mountain_receiver_drop' if k==2 else f'cascade_{k+1}_{k}'
        natural.trough(m,path,name,wet,SPINE_WIDTH,parent=parent,gaps=[path[-1]])
        m.routes[-1].update(kind='tier_divider',tier=k)
        for side,u in [('left',.055),('right',.945)]:
            end=np.r_[point(kind,k,u,.16),path[-1,2]];part=f'tier_{k}_{side}_header'
            natural.trough(m,[path[-1],end],part,wet,HEADER_WIDTH,parent=name,gaps=[path[-1]])
            m.routes[-1].update(kind='terrace_canal',tier=k,end='closed_field_outlet');r2.endcap(m,end,end-path[-1],HEADER_WIDTH,part)
        drop=cascade(kind,k);name=f'cascade_{k}_{k-1}' if k else 'cascade_0_ground'
        natural.trough(m,drop,name,wet,SPINE_WIDTH,parent=f'tier_{k}_spine',gaps=[drop[0]])
        m.routes[-1].update(kind='stepped_cascade',from_tier=k,to_tier=k-1,tread_count=math.ceil((drop[0,2]-drop[-1,2])/.18))
        r2.support(m,drop,lambda x,y:height(kind,x,y),name)
    for side,path in zip(('left','right'),ground_headers(kind)):
        name=f'ground_{side}';gap=openings.get(name,[])
        natural.trough(m,path,name,wet,HEADER_WIDTH,parent='cascade_0_ground',gaps=[path[0],*gap])
        is_open=any(np.linalg.norm(np.array(p)-path[-1])<1e-6 for p in gap)
        m.routes[-1].update(kind='terrace_canal',end='open_joint' if is_open else 'closed_field_outlet')
        if not is_open:r2.endcap(m,path[-1],path[-1]-path[0],HEADER_WIDTH,name)


def tile(kind,state='Wet',lod=0,origin=(0,0),openings=None):
    m=Mesh('RT_IF_'+kind+'_'+state+('_LOD1' if lod else ''));m.lod=lod
    for i,tri in enumerate(terrain(kind)):
        material='rock' if kind=='RockyFoothill' and i>=6 and np.ptp(tri[:,2])>.1 else 'earth'
        m.face(tri,material,'terrain_surface')
    ls=lines(kind);footprint=hull([p+offset for line in ls for p in line for offset in [(-.36,-.05),(.36,.4)]])
    for poly in r3.subtract(v3.HEX,footprint):r3.crop_patches(m,poly,0,np.array(origin),state)
    plots=[]
    for k in range(3):retaining_front(m,kind,k);plots.extend(tier_crops(m,kind,k,state))
    network(m,kind,state=='Wet',openings);r3.trim_crops(m,m.routes)
    natural.farmstead(m,2.35,-3.45,.02,state)
    if state in ('Wet','Dry'):
        for i,(x,y) in enumerate([(-4.65,.7),(4.55,.5),(-2.6,3.8)]):
            tree=natural.orchard(lod,seed=190+i);tree.faces=[(p*.65,n,uv,mat,part) for p,n,uv,mat,part in tree.faces];m.append(tree,(x,y,height(kind,x,y)+.02))
    m.meta=dict(category='tile',terrain=kind,state=state,lod=lod,tile_radius=v3.R,inlet=inlet(kind).tolist(),
                parcel_origin=list(origin),tier_lines=ls.tolist(),tier_heights=heights(kind),tier_plots=plots,
                water_network=dict(root='mountain_receiver_drop',routes=len(m.routes)),hill_shape='angular trapezoidal tiers; central cascades through open retaining notches')
    return m


@contextmanager
def geometry(regular):
    with r2.geometry(regular):
        old_tile=natural.tile;old_height=natural.surface_height
        natural.tile=lambda kind,state='Wet',lod=0,origin=(0,0),name=None:r3.flat_tile(state,lod,origin) if kind=='Flat' else tile(kind,state,lod,origin)
        natural.surface_height=lambda kind,x,y:0. if kind=='Flat' else height(kind,x,y)
        try:yield
        finally:natural.tile=old_tile;natural.surface_height=old_height


def scene(api=None):
    get_inlet=inlet if api is None else api.inlet
    get_headers=ground_headers if api is None else api.ground_headers
    make_tile=tile if api is None else api.tile
    ground_height=height if api is None else api.height

    m=Mesh('RT_IF_ConnectedDistrict')
    layout=[(-1,1,'RockyFoothill'),(0,1,'SteepHill'),(0,0,'GentleHill'),(-1,0,'Flat'),(1,0,'Flat'),(0,-1,'Flat')]
    parents={0:-1,1:0,2:1,3:0,4:2,5:2};samples=[]
    for i,(q,r,kind) in enumerate(layout):
        xy=v3.axial(q,r);neighbors=[];toward=(0,1)
        if kind=='Flat':
            toward=v3.axial(*layout[parents[i]][:2])-xy
            for oq,orr,other in layout:
                delta=v3.axial(oq,orr)-xy
                if other=='Flat' and abs(np.linalg.norm(delta)-2*v3.A)<1e-6:neighbors.append(round(math.atan2(delta[1],delta[0])/(math.pi/3))%6)
            graph=r3.parcel_graph(xy,neighbors,toward);root=np.r_[graph['points'][graph['root']],WATER]
        else:root=get_inlet(kind)
        samples.append(dict(q=q,r=r,kind=kind,center=xy.tolist(),inlet=(root+[*xy,0]).tolist(),neighbors=neighbors,toward=list(toward)))
    source=np.array(samples[0]['inlet'])+[-8,-.15,.10];links=[];openings={}
    for child,parent in parents.items():
        end=np.array(samples[child]['inlet']);upstream=None
        if parent<0:start=source
        else:
            owner=samples[parent]
            if samples[child]['kind']=='Flat':
                candidates=[(name,p) for name,path in zip(('ground_left','ground_right'),get_headers(owner['kind'])) for p in path]
                name,local=min(candidates,key=lambda item:np.linalg.norm((item[1]+[*owner['center'],0])[:2]-end[:2]))
                start=local+[*owner['center'],0]
            else:start=np.array(owner['inlet']);local=start-[*owner['center'],0];name='mountain_receiver_drop'
            openings.setdefault(owner['kind'],{}).setdefault(name,[]).append(local);upstream=f'tile_{owner["q"]}_{owner["r"]}_'+name
        links.append((parent,child,start,end,upstream))
    for e in samples:
        part=r3.flat_tile(origin=e['center'],neighbors=e['neighbors'],toward=e['toward']) if e['kind']=='Flat' else make_tile(e['kind'],origin=e['center'],openings=openings.get(e['kind'],{}))
        m.append(part,(*e['center'],0),prefix=f'tile_{e["q"]}_{e["r"]}_')
    def ground(x,y):
        for e in samples:
            xy=np.array([x,y])-e['center']
            if v3.in_poly(xy,v3.HEX):return 0. if e['kind']=='Flat' else ground_height(e['kind'],*xy)
        return 0.
    graph=[];feeders=[]
    for parent,child,start,end,upstream in links:
        dest=samples[child];name=f'feeder_{parent}_{child}';key=f'tile_{dest["q"]}_{dest["r"]}_'+('flat_supply' if dest['kind']=='Flat' else 'mountain_receiver_drop')
        route=next(r for r in m.routes if r['name']==key);tangent=(np.array(route['points'])[1]-end)[:2];before=len(m.routes)
        receiver=r2.feeder(m,start,end,tangent,ground,name,upstream);route['upstream']=receiver
        feeders.extend(m.routes[before:]);graph.append(dict(parent=parent,child=child,start=start.tolist(),end=end.tolist(),span=name,receiver=receiver))
    r3.trim_crops(m,feeders)
    m.box((source[0]-.12,source[1],source[2]-.2),(.42,.50,.50),'stone','source_socket')
    m.meta=dict(category='assembly',tiles=samples,source=source.tolist(),feeder_graph=graph,water_network=dict(root='feeder_-1_0',routes=len(m.routes)),native_status='offline review only')
    return m
