"""Small-scale plant silhouettes and working-farm props for the second art pass."""
import math
import numpy as np
from irrigation_mesh_io import Mesh, unit


def tube(m, points, radii, mat, part, sides=6):
    rings=[]
    for p,r in zip(points,radii):
        rings.append([np.asarray(p)+[r*math.cos(i*math.tau/sides),r*math.sin(i*math.tau/sides),0] for i in range(sides)])
    m.face(rings[0][::-1],mat,part);m.face(rings[-1],mat,part)
    for low,high in zip(rings,rings[1:]):
        for i in range(sides):j=(i+1)%sides;m.face([low[i],low[j],high[j],high[i]],mat,part)


def leaf(m, a, b, width, mat, part, double=True):
    a,b=np.asarray(a),np.asarray(b);d=b-a
    side=unit((-d[1],d[0],.02))*width
    mid=a+d*.48+[0,0,width*.22]
    p=[a,mid-side,b,mid+side]
    m.face(p,mat,part)
    if double:m.face(p[::-1],mat,part)


def palm(lod=0):
    m=Mesh('RT_IF_DatePalm'+('_LOD1' if lod else ''));rng=np.random.default_rng(99)
    tube(m,[(0,0,0),(.025,0,.6),(.09,-.015,1.2),(.15,-.02,1.76)],
         [.125,.112,.089,.07],'wood','palm_trunk',5 if lod else 7)
    count=8 if lod else 13
    for i in range(count):
        angle=i*math.tau/count+rng.uniform(-.08,.08);d=np.array((math.cos(angle),math.sin(angle),0));s=np.array((-d[1],d[0],0))
        length=rng.uniform(.83,1.19)
        def center(t):return np.array((.15,-.02,1.78))+d*length*t+[0,0,.36*math.sin(t*math.pi)-.32*t]
        if lod:
            for a,b in zip([0,.4,.75],[.4,.75,1]):leaf(m,center(a),center(b),.12*(1-a),'vegetables','palm_fronds')
        else:
            for a,b in zip([0,.33,.66],[.33,.66,1]):leaf(m,center(a),center(b),.018,'wood','palm_rachis')
            for t in np.linspace(.16,.88,7):
                width=.29*math.sin(math.pi*(t*.8+.06))
                for sign in (-1,1):
                    a=center(t);b=center(min(1,t+.18))+s*width*sign+[0,0,-.045]
                    leaf(m,a,b,.055*(1-t*.55),'legumes' if (i+int(t*10))%4==0 else 'vegetables','palm_leaflets')
    if not lod:
        for x in (-.06,.20):cluster(m,(x,-.04,1.50),(.08,.09,.16),'wood','date_bunch',rng,5,2)
    return m


def cluster(m,center,scale,mat,part,rng,sides=7,bands=3):
    c=np.asarray(center);s=np.asarray(scale);rings=[]
    phase=rng.uniform(0,.5)
    for j in range(1,bands+1):
        lat=-math.pi/2+math.pi*j/(bands+1)
        ring=[]
        for i in range(sides):
            a=i*math.tau/sides+phase
            v=np.array((math.cos(a)*math.cos(lat),math.sin(a)*math.cos(lat),math.sin(lat)))
            ring.append(c+v*s*rng.uniform(.89,1.10))
        rings.append(ring)
    for i in range(sides):
        j=(i+1)%sides
        m.face([c-[0,0,s[2]],rings[0][j],rings[0][i]],mat,part)
        m.face([rings[-1][i],rings[-1][j],c+[0,0,s[2]]],mat,part)
    for low,high in zip(rings,rings[1:]):
        for i in range(sides):j=(i+1)%sides;m.face([low[i],low[j],high[j],high[i]],mat,part)


def orchard(lod=0,seed=610):
    m=Mesh('RT_IF_FruitTree'+('_LOD1' if lod else ''));rng=np.random.default_rng(seed)
    tube(m,[(0,0,0),(.025,0,.27),(-.01,.025,.54)],[.055,.044,.020],'wood','fruit_trunk',5)
    # Intersecting, tilted leafy sprays leave real holes and broken silhouettes.
    # Their diffuse/alpha comes from original painted branch textures.
    count=4 if lod else 10
    for i in range(count):
        angle=i*2.39996+rng.uniform(-.2,.2);r=rng.uniform(.10,.27)
        center=np.array((r*math.cos(angle),r*math.sin(angle),rng.uniform(.56,.92)))
        if not lod:tube(m,[(0,0,.28),tuple(center-[0,0,.11])],[.023,.009],'wood','fruit_branch',4)
        right=np.array((math.cos(angle),math.sin(angle),rng.uniform(-.3,.3)))
        up=unit(np.cross(right,[math.sin(angle)*.75,-math.cos(angle)*.75,1]))
        size=rng.uniform(.30,.44);right=unit(right)*size;up=up*size
        p=[center-right-up,center+right-up,center+right+up,center-right+up]
        mat='leaves' if i%3 else 'leaf_light';uv=[(0,0),(1,0),(1,1),(0,1)]
        m.face(p,mat,'fruit_foliage',uv);m.face(p[::-1],mat,'fruit_foliage',uv[::-1])
    return m


def farmstead(m,x,y,z,state):
    """A small mudbrick store, reed shade, pots and harvested sheaves."""
    if state=='Construction':return
    q=Mesh('farmstead');height=.50 if state!='Pillaged' else .18
    q.box((0,0,height/2),(.78,.62,height),'plaster','farm_store')
    q.box((0,0,height+.024),(.82,.66,.048),'earth','flat_roof')
    for xx in (-.385,.385):q.box((xx,0,height+.085),(.06,.68,.13),'plaster','roof_parapet')
    q.box((0,.30,height+.08),(.80,.055,.12),'plaster','roof_parapet')
    if state!='Pillaged':
        q.box((-.07,-.316,.19),(.20,.014,.38),'shadow','store_door')
        q.box((.265,-.316,.355),(.095,.015,.105),'shadow','store_vent')
        q.box((.01,-.67,.42),(.90,.50,.035),'stubble','reed_awning')
        for xx in (-.39,.39):q.box((xx,-.89,.20),(.028,.028,.40),'wood','awning_post')
    rng=np.random.default_rng(58)
    for xx,yy in [(.65,-.05),(.69,.2),(-.60,.12)]:
        cluster(q,(xx,yy,.12),(.11,.11,.13),'earth','storage_jar',rng,6,3)
        q.face([(xx-.048,yy-.048,.24),(xx+.048,yy-.048,.24),(xx+.048,yy+.048,.24),(xx-.048,yy+.048,.24)],'shadow','jar_mouth')
    if state=='Wet':
        for xx,yy in [(-.67,-.40),(-.54,-.61)]:cluster(q,(xx,yy,.10),(.16,.10,.10),'barley','harvest_sheaves',rng,6,2)
    m.append(q,(x,y,z))


def vegetation(m,kind,state,lod,surface_height,in_poly,hexpoly):
    if state in ('Construction','Pillaged'):return
    # Deliberate orchard strip; central route and field-front remain readable.
    locations=[(-3.8,.7),(-3.1,2.2),(-1.6,3.6),(.2,3.85),(1.9,3.1),(3.15,1.4),(3.8,-.1),(-3.8,-1.15),(-1.2,.8)]
    placed=[]
    for index,(tx,ty) in enumerate(locations):
        # Slide a planting site onto the nearest usable bench instead of
        # deleting most of the orchard when the terrain gets steeper.
        candidates=[(tx,ty)]
        for radius in (.25,.50,.75):
            candidates += [(tx+radius*math.cos(a),ty+radius*math.sin(a)) for a in np.linspace(0,math.tau,8,endpoint=False)]
        chosen=None
        for x,y in candidates:
            if abs(x)<.52 and y<.7:continue
            if any((x-a)**2+(y-b)**2<.72**2 for a,b in placed):continue
            z=surface_height(kind,x,y)
            footprint=[(x+dx,y+dy) for dx,dy in [(.25,0),(-.25,0),(0,.25),(0,-.25)]]
            if not all(in_poly(p,hexpoly) and abs(surface_height(kind,*p)-z)<.05 for p in footprint):continue
            chosen=(x,y,z);break
        if chosen is None:continue
        x,y,z=chosen;placed.append((x,y))
        if kind=='Flat' and index in (0,2,4):p=palm(lod)
        else:p=orchard(lod)
        m.append(p,(x,y,z+.023),angle=(index*79)%360)


def planted_relief(m,poly,z,ix,iy,origin,mat,lod,inside):
    """Low plant clusters, complementary to diffuse rows; no alpha-sorted cards."""
    if lod or mat not in ('barley','vegetables','legumes'):return
    from build_irrigation_meshes import CROP_GRID
    sx,sy=CROP_GRID;o=np.asarray(origin)+[.37,.61]
    rng=np.random.default_rng((ix*73856093 ^ iy*19349663)&0xffffffff)
    n=13 if mat=='barley' else 10
    for row in range(n):
        # Match diffuse row positions after the texture gutter crop.
        u=(32+row*(512-64)/n-16)/(512-32)
        x=ix*sx+u*sx-o[0]
        for j in range(7):
            y=iy*sy+(.14+j*.112+rng.uniform(-.014,.014))*sy-o[1]
            if abs(x)<.29 and y<.45:continue
            if not inside((x,y),np.asarray(poly)):continue
            r=.055 if mat=='barley' else .073;h=.10 if mat=='barley' else .065
            if not all(inside((x+dx,y+dy),np.asarray(poly)) for dx,dy in [(r,0),(-r,0),(0,r),(0,-r)]):continue
            # Open-bottom low crowns provide small real shadows at close zoom.
            p=[(x-r,y,z+.004),(x,y-r,z+.004),(x+r,y,z+.004),(x,y+r,z+.004)]
            for k in range(4):m.face([p[k],p[(k+1)%4],(x+r*.18,y,h+z)],mat,'crop_relief')
