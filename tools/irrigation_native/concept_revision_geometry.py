"""Review revision: long parcel canals, broad benches and shallow aqueducts.

Offline source geometry only. V3's archived geometry and native exports are not
modified. Grades here are design limits in normalized model units, not claims
about a calibrated Civ V terrain surface or historical engineering tolerances.
"""
from contextlib import contextmanager
import math
import numpy as np
from build_concept_models import natural, v3, Mesh, unit, farm_function
from build_overlays import channel

MAX_GRADE = .02
DESIGN_GRADE = .008
MAX_TURN = 15.0
BENCHES = 3
FLAT_CONTROLS = [(.62,3.75),(.62,2.846),(0,2.846),(0,0),(-3.302,0),(-3.302,-2.50)]


def rounded(points, radius=.28, steps=6):
    """Fillet polygon corners while retaining the long straight canal runs."""
    p=np.asarray(points,float);out=[p[0]]
    for a,b,c in zip(p,p[1:],p[2:]):
        d=min(radius,np.linalg.norm(b-a)*.35,np.linalg.norm(c-b)*.35)
        first=b-unit(b-a)*d;last=b+unit(c-b)*d
        out.append(first)
        for t in np.linspace(0,1,steps+1)[1:]:out.append((1-t)**2*first+2*t*(1-t)*b+t*t*last)
    out.append(p[-1]);return np.array(out)


def rings(kind):
    if kind=='Flat':return [(natural.boundary(),0.)]
    H=v3.KINDS[kind][1];out=[(natural.boundary(),0.)]
    # Long, gently bowed fronts, with uncultivated shoulders behind. Three broad
    # shelves replace the old nested rings and frequent dry gully interruptions.
    for k,(w,y,back) in enumerate([(4.25,-2.68,3.75),(3.56,-1.12,3.48),(2.67,.42,3.12)]):
        points=[]
        for i in range(natural.N):
            if i<=12:
                x=-w*math.cos(math.pi*i/12)
                yy=y+(.90+.07*k-y)*(x/w)**6+.025*math.sin(x*.9)*(1-(x/w)**2)
            else:
                a=math.pi*(i-12)/12;x=w*math.cos(a)
                yy=.90+.07*k+(back-.90-.07*k)*math.sin(a)
            points.append((x,yy))
        out.append((np.array(points),H*(k+1)/BENCHES))
    return out


def header(kind,k):
    a,z=rings(kind)[k];b,_=rings(kind)[k+1]
    p=a[:13]*.25+b[:13]*.75
    # Keep route ends off the shoulder wedge, including the full channel width.
    p=p[1:12].copy()
    p[0]=(p[0]+p[1])/2;p[-1]=(p[-1]+p[-2])/2
    return np.c_[p,np.full(len(p),z+.145)]


def inlet(kind):
    if kind=='Flat':return natural.flat_rotate((*FLAT_CONTROLS[0],.145))
    h=header(kind,BENCHES-1)
    # Receive beside the upper field, not on an invented summit reservoir.
    p=h[0]+np.r_[-unit(h[1,:2]-h[0,:2])*.35,0.]
    p[2]=v3.KINDS[kind][1]+.40
    return p


def endcap(m,p,d,width,name):
    q=Mesh('cap');q.box((0,0,-.014),(.055,width+.09,.13),'stone',name+'_closed_end')
    m.append(q,p,math.degrees(math.atan2(d[1],d[0])))


def wall(m,a,b,z,h,k,i):
    # Continuous battered face and narrow coping. Only the supply-chute opening
    # interrupts the first segment; no arbitrary chips or repeating missing bays.
    d=b-a
    kind=next(kind for kind in v3.KINDS if kind in m.name)
    polygon=rings(kind)[k+1][0]
    def corner(j):
        before=unit(polygon[j]-polygon[(j-1)%len(polygon)]);after=unit(polygon[(j+1)%len(polygon)]-polygon[j])
        n0=np.array([-before[1],before[0]]);n1=np.array([-after[1],after[0]])
        side=unit(n0+n1);return side*.055/max(.5,np.dot(side,n1))
    side0,side1=corner(i),corner((i+1)%len(polygon))
    intervals=[(0.,.23),(.77,1.)] if i==1 else [(0.,1.)]
    for t0,t1 in intervals:
        p=a+d*t0;q=a+d*t1
        ps=side0*(1-t0)+side1*t0;qs=side0*(1-t1)+side1*t1
        uv=[(t0*np.linalg.norm(d)/2,0),(t1*np.linalg.norm(d)/2,0),
            (t1*np.linalg.norm(d)/2,(h-z)/.85),(t0*np.linalg.norm(d)/2,(h-z)/.85)]
        m.face([(*(p-ps*.7),z),(*(q-qs*.7),z),(*q,h),(*p,h)],'stone','retaining_wall',uv)
        m.face([(*p,h),(*q,h),(*(q+qs),h),(*(p+ps),h)],'coping','wall_coping')


def network(m,kind,wet,openings=None):
    openings= {} if openings is None else openings
    if kind=='Flat':
        # Follow the same rotated/staggered parcel seams as field_patches. One
        # branch and two rounded right-angle turns replace the curved comb.
        main=rounded(FLAT_CONTROLS)
        distances=np.r_[0,np.cumsum(np.linalg.norm(np.diff(main,axis=0),axis=1))]
        points=np.array([natural.flat_rotate((*p,.145-.012*s/distances[-1])) for p,s in zip(main,distances)])
        # Fork at the start of the broad lower turn. Smoothly join the horizontal
        # parcel boundary, without adding a second parallel header.
        idx=np.argmin(np.linalg.norm(main-[0,.28],axis=1));start=points[idx]
        branch_xy=rounded([main[idx],(0,0),(3.65,0)],.25)
        branch=np.array([natural.flat_rotate((*p,start[2]-.005*i/(len(branch_xy)-1))) for i,p in enumerate(branch_xy)])
        channel(m,points,'flat_supply',.28,wet,gaps=[(start,branch[1]-start)],bank_scale=.62,bank_material='stone')
        channel(m,branch,'flat_field_branch',.24,wet,upstream='flat_supply',start_clearance=.24,bank_scale=.62,bank_material='stone')
        for r in m.routes:r['kind']='parcel_canal'
        return
    root=inlet(kind);top=header(kind,2)
    approach=top[0]+np.r_[-unit(top[1,:2]-top[0,:2])*.08,0.]
    approach[2]=root[2]
    natural.trough(m,[root,approach,top[0]],'mountain_receiver_drop',wet,.25,gaps=openings.get('mountain_receiver_drop',[]))
    m.routes[-1]['kind']='lined_drop'
    support(m,[root,approach,top[0]],lambda x,y:natural.surface_height(kind,x,y),'upper_receiver')
    for k in range(2,-1,-1):
        arc=header(kind,k);name=f'bench_{k}_contour';parent='mountain_receiver_drop' if k==2 else f'drop_{k+1}_{k}'
        natural.trough(m,arc,name,wet,.23,parent=parent,gaps=openings.get(name,[]))
        open_end=any(np.linalg.norm(np.array(p)-arc[-1])<1e-6 for p in openings.get(name,[]))
        m.routes[-1].update(kind='terrace_canal',end='open_joint' if open_end else 'closed_field_outlet')
        if not open_end:endcap(m,arc[-1],arc[-1]-arc[-2],.23,name)
        if k:
            lower=header(kind,k-1)[0];edge=(rings(kind)[k][0][1]+rings(kind)[k][0][2])/2
            center=rings(kind)[k][0].mean(0);u=unit(edge-center)
            route=[arc[0],(*(edge-u*.10),arc[0,2]),(*(edge+u*.035),arc[0,2]),(*(edge+u*.15),lower[2]),lower]
            natural.trough(m,route,f'drop_{k}_{k-1}',wet,.25,parent=name)
            m.routes[-1]['kind']='lined_drop'


def support(m,points,ground,name):
    """Masonry under a lined chute, with no unsupported horizontal lip."""
    for a,b in zip(points,points[1:]):
        a,b=np.asarray(a),np.asarray(b);d=b-a;side=unit(np.array([-d[1],d[0],0]))*.18
        za=ground(*a[:2])-.015;zb=ground(*b[:2])-.015
        if min(a[2]-.09-za,b[2]-.09-zb)<.005:continue
        p=[a-side,a+side,b+side,b-side]
        bottom=[np.r_[q[:2],za if i<2 else zb] for i,q in enumerate(p)]
        top=[q-[0,0,.09] for q in p]
        m.face(top[::-1],'stone',name+'_support')
        for i in range(4):
            j=(i+1)%4;m.face([bottom[i],bottom[j],top[j],top[i]],'stone',name+'_support')


def curved_bridge(m,points,ground,name,wet=True,lod=0,parent=None):
    """One continuous arcade along a softly turning, shallow graded centerline."""
    points=np.asarray(points);lengths=np.linalg.norm(np.diff(points[:,:2],axis=0),axis=1)
    station=np.r_[0,np.cumsum(lengths)];length=station[-1]
    grades=-np.diff(points[:,2])/lengths
    if np.min(grades)<-1e-7 or np.max(grades)>MAX_GRADE+1e-7:raise ValueError(('bridge grade',name,grades))
    def at(s):
        j=min(len(points)-2,np.searchsorted(station,s,side='right')-1);j=max(0,j)
        t=(s-station[j])/lengths[j];p=points[j]*(1-t)+points[j+1]*t
        d=unit(points[j+1,:2]-points[j,:2]);return p,np.array([-d[1],d[0]])
    def xyz(s,y,z=None):
        p,side=at(s);return [*(p[:2]+side*y),p[2]-.11 if z is None else z]
    count=max(1,round(length/1.55));step=length/count;depth=.43;pier=.22
    for i in range(count+1):
        s=i*step;p,side=at(s);z=ground(*p[:2])-.025;h=p[2]-.11-z
        if h>0:
            q=Mesh('pier');q.box((0,0,z+h/2),(pier,depth,h),'stone',name+'_pier')
            m.append(q,(*p[:2],0),math.degrees(math.atan2(-side[0],side[1])))
    for i in range(count):
        left,right=i*step+pier/2,(i+1)*step-pier/2;mid=(left+right)/2;rad=(right-left)/2
        base=max(ground(*at(s)[0][:2]) for s in np.linspace(left,right,9))
        deck=min(at(left)[0][2],at(right)[0][2])-.11;available=deck-base
        if available<=.01:continue
        rise=min(rad*.88,max(0,available-.12));spring=deck-.12-rise
        xs=np.linspace(left,right,6 if lod else 9)
        for x0,x1 in zip(xs,xs[1:]):
            z0=base if available<.24 else spring+rise*math.sqrt(max(0,1-((x0-mid)/rad)**2))
            z1=base if available<.24 else spring+rise*math.sqrt(max(0,1-((x1-mid)/rad)**2))
            for sign in (-1,1):
                face=[xyz(x0,sign*depth/2,z0),xyz(x1,sign*depth/2,z1),xyz(x1,sign*depth/2),xyz(x0,sign*depth/2)]
                m.face(face if sign<0 else face[::-1],'stone',name+'_spandrel')
            m.face([xyz(x0,-depth/2,z0),xyz(x0,depth/2,z0),xyz(x1,depth/2,z1),xyz(x1,-depth/2,z1)],'stone',name+'_intrados')
            m.face([xyz(x0,-depth/2),xyz(x1,-depth/2),xyz(x1,depth/2),xyz(x0,depth/2)],'stone',name+'_deck')
    natural.trough(m,points,name,wet,.25,parent=parent)
    m.routes[-1].update(kind='aqueduct',max_grade=MAX_GRADE)


def feeder(m,start,end,tangent,ground,name,parent=None):
    """Ease a shallow arcade into a short, separate lined receiving chute."""
    start,end=np.asarray(start,float),np.asarray(end,float);tangent=unit(tangent)
    # The approach shares the destination channel tangent. A short drop then
    # absorbs height differences without tilting the entire bridge like a ramp.
    landing=end[:2]-tangent*.70
    distance=np.linalg.norm(landing-start[:2]);direction=unit(landing-start[:2])
    c0=start[:2];c1=c0+direction*distance*.38;c3=landing;c2=c3-tangent*min(3.8,distance*.50)
    points=[]
    for t in np.linspace(0,1,max(64,math.ceil(distance/.18))):
        points.append((1-t)**3*c0+3*(1-t)**2*t*c1+3*(1-t)*t*t*c2+t**3*c3)
    points=np.array(points);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    fall=min(DESIGN_GRADE*s[-1],start[2]-end[2]);z=start[2]-fall*s/s[-1]
    path=np.c_[points,z];curved_bridge(m,path,ground,name,parent=parent)
    # Tiny horizontal treads distinguish the controlled drop from a steep span.
    a=path[-1];height=a[2]-end[2];count=max(1,math.ceil(height/.24));drop=[a]
    for i in range(count):
        p=a+(end-a)*(i+.30)/count;p[2]=a[2]-height*i/count;drop.append(p)
        p=a+(end-a)*(i+1)/count;drop.append(p)
    natural.trough(m,drop,name+'_receiver',True,.25,parent=name)
    m.routes[-1]['kind']='lined_drop' if height>.025 else 'receiving_channel'
    # Real masonry under the chute, ending at terrain, not a floating water strip.
    for a,b in zip(drop,drop[1:]):
        p=(a+b)/2;z=ground(*p[:2]);h=min(a[2],b[2])-.09-z
        if h>.01:
            q=Mesh('receiver');q.box((0,0,z+h/2),(np.linalg.norm((b-a)[:2])+.01,.36,h),'stone',name+'_receiver_support')
            m.append(q,(*p[:2],0),math.degrees(math.atan2(tangent[1],tangent[0])))
    return name+'_receiver'


def scene():
    m=Mesh('RT_IF_ConceptR2_ConnectedDistrict')
    layout=[(-1,1,'RockyFoothill'),(0,1,'SteepHill'),(0,0,'GentleHill'),(-1,0,'Flat'),(1,0,'Flat'),(0,-1,'Flat')]
    samples=[]
    for q,r,kind in layout:
        xy=v3.axial(q,r);samples.append(dict(q=q,r=r,kind=kind,center=xy.tolist(),inlet=(inlet(kind)+[*xy,0]).tolist()))
    source=np.array(samples[0]['inlet'])+[-8,-.15,.10];links=[];openings={}
    for parent,child in [(-1,0),(0,1),(1,2),(0,3),(2,4),(2,5)]:
        end=np.array(samples[child]['inlet']);upstream=None
        if parent<0:start=source
        else:
            owner=samples[parent]
            if samples[child]['kind']=='Flat':
                options=header(owner['kind'],0);name='bench_0_contour'
                index=np.argmin(np.linalg.norm((options+[*owner['center'],0])[:,:2]-end[:2],axis=1))
                local=options[index];start=local+[*owner['center'],0]
                openings.setdefault(owner['kind'],{}).setdefault(name,[]).append(local)
            else:
                start=np.array(owner['inlet']);name='mountain_receiver_drop'
                openings.setdefault(owner['kind'],{}).setdefault(name,[]).append(inlet(owner['kind']))
            upstream=f'tile_{owner["q"]}_{owner["r"]}_'+name
        links.append((parent,child,start,end,upstream))
    base_network=natural.network
    try:
        for sample in samples:
            kind=sample['kind'];natural.network=lambda mesh,k,wet:network(mesh,k,wet,openings.get(k,{}))
            part=natural.tile(kind,origin=sample['center']);prefix=f'tile_{sample["q"]}_{sample["r"]}_'
            m.append(part,(*sample['center'],0),prefix=prefix)
    finally:natural.network=base_network
    def ground(x,y):
        for e in samples:
            xy=np.array((x,y))-e['center']
            if v3.in_poly(xy,v3.HEX):return natural.surface_height(e['kind'],*xy)
        return 0.
    graph=[]
    for parent,child,start,end,upstream in links:
        dest=samples[child];root=f'tile_{dest["q"]}_{dest["r"]}_'+('flat_supply' if dest['kind']=='Flat' else 'mountain_receiver_drop')
        route=next(r for r in m.routes if r['name']==root);tangent=(np.array(route['points'])[1]-end)[:2]
        name=f'feeder_{parent}_{child}';receiver=feeder(m,start,end,tangent,ground,name,upstream);route['upstream']=receiver
        graph.append(dict(parent=parent,child=child,start=start.tolist(),end=end.tolist(),span=name,receiver=receiver))
    m.box((source[0]-.12,source[1],source[2]-.20),(.42,.50,.50),'stone','source_socket')
    m.meta=dict(category='assembly',tiles=samples,source=source.tolist(),feeder_graph=graph,
                water_network=dict(root='feeder_-1_0',routes=len(m.routes)),native_status='offline review only')
    return m


@contextmanager
def geometry(regular):
    replacements=dict(terrace_rings=rings,header=header,inlet=inlet,wall=wall,network=network,
                      front_end=lambda k:12,gully=lambda i,k:False,farmstead=farm_function(regular))
    old={key:getattr(natural,key) for key in replacements}
    old_fields=natural.field_patches;old_palm=natural.palm
    def palm(lod=0):
        m=old_palm(lod);m.faces=[(p*.65,n,uv,mat,part) for p,n,uv,mat,part in m.faces];return m
    natural.palm=palm
    natural.field_patches=lambda *a,**kw:old_fields(*a,**kw,texture_repeat=2.4,parcel_margin=.018)
    for key,value in replacements.items():setattr(natural,key,value)
    natural.terrain_faces.cache_clear();natural.terrain_arrays.cache_clear()
    try:yield
    finally:
        for key,value in old.items():setattr(natural,key,value)
        natural.field_patches=old_fields;natural.palm=old_palm
        natural.terrain_faces.cache_clear();natural.terrain_arrays.cache_clear()
