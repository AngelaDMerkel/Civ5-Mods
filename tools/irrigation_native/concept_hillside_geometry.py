"""R5: unequal angular benches, embedded channels and staggered parcel drops."""
from contextlib import contextmanager
from functools import lru_cache
import math
import sys
import numpy as np
from build_concept_models import natural, v3, Mesh, unit
import concept_revision_geometry as r2
import concept_parcel_geometry as r3
import concept_cascade_geometry as r4

SHAPES={
 'GentleHill':dict(rows=[[[-4.15,-1.75],[-.65,-2.2],[4.2,-1.30]],[[-3.75,.15],[-.9,-.45],[3.6,.20]],[[-3.35,1.55],[-1.15,1.0],[2.75,1.75]],[[-2.25,3.25],[-.45,2.9],[1.8,3.65]]],heights=[.24,.57,.96]),
 'SteepHill':dict(rows=[[[-4.1,-1.8],[-1.,-2.3],[4.15,-1.45]],[[-3.4,.20],[-.55,-.35],[3.75,-.05]],[[-2.85,1.70],[-.25,1.2],[3.,1.9]],[[-1.5,3.3],[.35,3.0],[2.15,3.65]]],heights=[.38,.88,1.46]),
 'RockyFoothill':dict(rows=[[[-4.15,-1.8],[-1.2,-2.25],[4.1,-1.45]],[[-3.5,.15],[-.85,-.4],[3.55,.15]],[[-3.2,1.6],[-1.1,1.1],[2.65,1.85]],[[-2.,3.2],[-.25,2.8],[1.85,3.55]]],heights=[.45,1.05,1.70])}
# Unequal plots and different active drop locations break the axial staircase.
DIVISIONS=[(.34,.72),(.42,),(.61,)]
OUTLET=[.72,.42,.61]
WATER=.095
GROUND_WATER=.145
WIDTH=.15


def rows(kind):return np.array(SHAPES[kind]['rows'])
def heights(kind):return SHAPES[kind]['heights']
def line_at(row,u):
    i=0 if u<=.5 else 1;t=u*2-i
    return row[i]*(1-t)+row[i+1]*t


def point(kind,k,u,v):
    rs=rows(kind);return line_at(rs[k],u)*(1-v)+line_at(rs[k+1],u)*v


def direction(kind,k,u):return unit(point(kind,k,u,0)-point(kind,k,u,1))
def divider(kind,k,u):return np.array([np.r_[point(kind,k,u,v),heights(kind)[k]+WATER] for v in (.91,.12)])
def incoming_u(k):return OUTLET[k+1] if k<2 else .12

def inlet(kind):
    p=np.r_[point(kind,2,incoming_u(2),.91),heights(kind)[2]+WATER]
    p[:2]-=direction(kind,2,incoming_u(2))*.40;p[2]+=.10;return p


def ground_headers(kind):
    a=rows(kind)[0,0];b=rows(kind)[0,-1];u=OUTLET[0];d=direction(kind,0,u)
    center=point(kind,0,u,0)+d*.64
    # Keep both low outgoing ends beyond the earth shoulders.
    return [np.c_[[center,a+[-.46,-.53]],np.full(2,GROUND_WATER)],np.c_[[center,b+[.46,-.53]],np.full(2,GROUND_WATER)]]


def cascade(kind,k):
    u=OUTLET[k];start=divider(kind,k,u)[-1];edge=point(kind,k,u,0)
    end=np.r_[point(kind,k-1,u,.91),heights(kind)[k-1]+WATER] if k else ground_headers(kind)[0][0]
    lip=np.r_[edge+direction(kind,k,u)*.075,start[2]];run=end[:2]-lip[:2];rise=start[2]-end[2]
    path=[start,lip];count=max(2,math.ceil(rise/.18))
    for j in range(count):
        a=lip.copy();a[:2]+=run*(j+.65)/count;a[2]-=rise*j/count
        b=lip.copy();b[:2]+=run*(j+1)/count;b[2]-=rise*(j+1)/count
        path.extend([a,b])
    return np.array(path)


@lru_cache(None)
def terrain(kind):
    result=[];rs=rows(kind)
    for i in range(6):result.append(np.array([(*v3.HEX[i],0),(*v3.HEX[(i+1)%6],0),(0,0,0)]))
    for k,z in enumerate(heights(kind)):
        for j in range(2):
            a,b=rs[k,j:j+2];d,c=rs[k+1,j:j+2];quad=np.array([(*a,z),(*b,z),(*c,z),(*d,z)])
            result.extend([quad[[0,1,2]],quad[[0,2,3]]])
        for p,q,offset in [(rs[k,0],rs[k+1,0],[-.42,0]),(rs[k+1,-1],rs[k,-1],[.42,0])]:
            f=np.array([(*p,z),(*q,z),(*(q+offset),0),(*(p+offset),0)])
            for ids in ([0,1,2],[0,2,3]):
                tri=f[ids]
                if np.cross(tri[1]-tri[0],tri[2]-tri[0])[2]<0:tri=tri[::-1]
                result.append(tri)
    for j in range(2):
        a,b=rs[-1,j:j+2];z=heights(kind)[-1]
        f=np.array([(*a,z),(*b,z),(*(b+[0,.42]),0),(*(a+[0,.42]),0)])
        result.extend([f[[0,1,2]],f[[0,2,3]]])
    return result


def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def height(kind,x,y):
    best=0.
    for tri in terrain(kind)[6:]:
        a=tri[1,:2]-tri[0,:2];b=tri[2,:2]-tri[0,:2];q=np.array([x,y])-tri[0,:2];den=cross2(a,b)
        if abs(den)<1e-10:continue
        u=cross2(q,b)/den;v=cross2(a,q)/den
        if u>=-1e-7 and v>=-1e-7 and u+v<=1+1e-7:best=max(best,float(tri[:,2]@[1-u-v,u,v]))
    return best


def masonry(m,a,b,low,high,part,phase=0):
    """Repeat native masonry at a fixed physical scale instead of stretching it."""
    d=b-a;length=np.linalg.norm(d);inward=unit(np.array([-d[1],d[0]]))*.045
    cuts=np.linspace(0,1,max(1,math.ceil(length/1.35))+1)
    for i,(s,t) in enumerate(zip(cuts,cuts[1:])):
        p=a+d*s;q=a+d*t;span=(t-s)*length
        # Subtle joint variation, no rubble silhouette or multiplied tiny props.
        chip=.006*math.sin((i+phase)*2.4)
        uv=[(0,0),(span/1.35,0),(span/1.35,(high-low)/.85),(0,(high-low)/.85)]
        m.face([(*(p-inward*.7),low),(*(q-inward*.7),low),(*q,high),(*p,high)],'stone',part,uv)
        m.face([(*p,high),(*q,high),(*(q+inward),high+chip),(*(p+inward),high+chip)],'coping',part+'_coping',[(0,0),(span/1.35,0),(span/1.35,.65),(0,.65)])


def walls(m,kind,k):
    rs=rows(kind);z=heights(kind)[k];low=heights(kind)[k-1] if k else 0.
    u=OUTLET[k];segment=0 if u<.5 else 1;notch=line_at(rs[k],u);records=[]
    for j in range(2):
        a,b=rs[k,j:j+2];part=f'tier_{k}_retaining_front_{j}'
        if j==segment:
            tangent=unit(b-a);half=WIDTH/2+.09
            masonry(m,a,notch-tangent*half,low,z,part,j+k)
            masonry(m,notch+tangent*half,b,low,z,part,j+k+3)
            records.append(dict(group=part,center=notch.tolist(),tangent=tangent.tolist(),half_width=half,tier=k))
        else:masonry(m,a,b,low,z,part,j+k)
    return records


def crops(m,kind,k,state):
    z=heights(kind)[k];bounds=[0.,*DIVISIONS[k],1.];records=[]
    material_set=['barley','vegetables','stubble','legumes','barley','vegetables','legumes']
    for j,(left,right) in enumerate(zip(bounds,bounds[1:])):
        # Physical setback from each seam keeps narrow plots legible and water
        # out of their triangles. The outer boundaries follow the angled bench.
        margin=.13/np.linalg.norm(point(kind,k,1,.5)-point(kind,k,0,.5))
        u0=left+margin;u1=right-margin;v0=.075;v1=.83
        material='dry_crop' if state=='Dry' else material_set[(k*3+j)%len(material_set)]
        part=f'tier_{k}_plot_{j}_crop_surface';cuts=sorted(set([u0,u1,*([.5] if u0<.5<u1 else [])]))
        for ua,ub in zip(cuts,cuts[1:]):
            width=np.linalg.norm(point(kind,k,ub,.5)-point(kind,k,ua,.5));depth=np.linalg.norm(point(kind,k,(ua+ub)/2,v1)-point(kind,k,(ua+ub)/2,v0))
            nx=max(1,math.ceil(width/2.4))
            for i in range(nx):
                a=ua+(ub-ua)*i/nx;b=ua+(ub-ua)*(i+1)/nx
                m.face([(*point(kind,k,u,v),z+.013) for u,v in [(a,v0),(b,v0),(b,v1),(a,v1)]],material,part,[(0,0),(width/nx/2.4,0),(width/nx/2.4,depth/2.4),(0,depth/2.4)])
        records.append(dict(group=part,tier=k,elevation=z,material=material,u_bounds=[u0,u1]))
    return records


def network(m,kind,wet,openings=None):
    openings=openings or {};top=np.r_[point(kind,2,incoming_u(2),.91),heights(kind)[2]+WATER];root=inlet(kind)
    natural.trough(m,[root,np.r_[top[:2]-direction(kind,2,incoming_u(2))*.06,root[2]],top],'mountain_receiver_drop',wet,WIDTH,gaps=openings.get('mountain_receiver_drop',[]))
    m.routes[-1]['kind']='lined_drop';r2.support(m,[root,top],lambda x,y:height(kind,x,y),'upper_receiver')
    for k in range(2,-1,-1):
        origin=incoming_u(k);z=heights(kind)[k]+WATER;parent='mountain_receiver_drop' if k==2 else f'cascade_{k+1}_{k}'
        for side,end in [('left',.035),('right',.965)]:
            stops=sorted(set([origin,end,*[u for u in (*DIVISIONS[k],.5) if min(origin,end)<u<max(origin,end)]]),reverse=end<origin)
            path=np.array([np.r_[point(kind,k,u,.91),z] for u in stops]);name=f'tier_{k}_{side}_header'
            joints=[np.r_[point(kind,k,u,.91),z] for u in DIVISIONS[k]]
            natural.trough(m,path,name,wet,WIDTH,parent=parent,gaps=[path[0],*joints])
            m.routes[-1].update(kind='terrace_canal',tier=k,end='closed_field_outlet');r2.endcap(m,path[-1],path[-1]-path[-2],WIDTH,name)
        for j,u in enumerate(DIVISIONS[k]):
            path=divider(kind,k,u);name=f'tier_{k}_divider_{j}';active=u==OUTLET[k]
            natural.trough(m,path,name,wet,.15 if active else .10,parent=f'tier_{k}_'+('left' if u<origin else 'right')+'_header',gaps=[path[0]])
            m.routes[-1].update(kind='tier_divider',tier=k,end='open_joint' if active else 'closed_field_outlet')
            if not active:r2.endcap(m,path[-1],path[-1]-path[-2],.10,name)
            else:
                drop=cascade(kind,k);label=f'cascade_{k}_{k-1}' if k else 'cascade_0_ground'
                natural.trough(m,drop,label,wet,WIDTH,parent=name)
                m.routes[-1].update(kind='stepped_cascade',from_tier=k,to_tier=k-1,drop_u=u,tread_count=max(2,math.ceil((drop[0,2]-drop[-1,2])/.18)))
                r2.support(m,drop,lambda x,y:height(kind,x,y),label)
    for side,path in zip(('left','right'),ground_headers(kind)):
        name=f'ground_{side}';gap=openings.get(name,[])
        natural.trough(m,path,name,wet,.16,parent='cascade_0_ground',gaps=[path[0],*gap])
        is_open=any(np.linalg.norm(np.array(p)-path[-1])<1e-6 for p in gap)
        m.routes[-1].update(kind='terrace_canal',end='open_joint' if is_open else 'closed_field_outlet')
        if not is_open:r2.endcap(m,path[-1],path[-1]-path[0],.16,name)


def tile(kind,state='Wet',lod=0,origin=(0,0),openings=None):
    m=Mesh('RT_IF_'+kind+'_'+state+('_LOD1' if lod else ''));m.lod=lod
    for i,tri in enumerate(terrain(kind)):
        material='rock' if kind=='RockyFoothill' and i>=6 and np.ptp(tri[:,2])>.1 else 'earth'
        m.face(tri,material,'terrain_surface')
    rs=rows(kind);footprint=r4.hull([p+offset for row in rs for p in row for offset in [(-.46,-.05),(.46,.46)]])
    for poly in r3.subtract(v3.HEX,footprint):r3.crop_patches(m,poly,0,np.array(origin),state)
    plots=[];notches=[]
    for k in range(3):notches.extend(walls(m,kind,k));plots.extend(crops(m,kind,k,state))
    network(m,kind,state=='Wet',openings);r3.trim_crops(m,m.routes)
    natural.farmstead(m,2.35,-3.45,.02,state)
    if state in ('Wet','Dry'):
        for i,(x,y,scale) in enumerate([(-4.65,.75,.64),(4.6,.3,.58),(-2.7,3.8,.72)]):
            tree=natural.orchard(lod,seed=221+i);tree.faces=[(p*scale,n,uv,mat,part) for p,n,uv,mat,part in tree.faces];m.append(tree,(x,y,height(kind,x,y)+.02))
    m.meta=dict(category='tile',terrain=kind,state=state,lod=lod,tile_radius=v3.R,inlet=inlet(kind).tolist(),parcel_origin=list(origin),
                tier_rows=rs.tolist(),tier_heights=heights(kind),tier_plots=plots,retaining_notches=notches,
                tier_water_heights=[z+WATER for z in heights(kind)],ground_water_height=GROUND_WATER,
                water_network=dict(root='mountain_receiver_drop',routes=len(m.routes)),hill_shape='unequal angular benches with staggered parcel drops and fine native masonry')
    return m


@contextmanager
def geometry(regular):
    with r2.geometry(regular):
        old_tile=natural.tile;old_height=natural.surface_height
        natural.tile=lambda kind,state='Wet',lod=0,origin=(0,0),name=None:r3.flat_tile(state,lod,origin) if kind=='Flat' else tile(kind,state,lod,origin)
        natural.surface_height=lambda kind,x,y:0. if kind=='Flat' else height(kind,x,y)
        try:yield
        finally:natural.tile=old_tile;natural.surface_height=old_height


def scene():return r4.scene(api=sys.modules[__name__])
