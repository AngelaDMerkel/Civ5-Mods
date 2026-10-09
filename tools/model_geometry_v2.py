"""Revised original Civ V source geometry; no native game art is copied.

All coordinates are Z-up. Field models leave a central garrison lane clear.
"""
import math
import numpy as np
from build_models import Mesh as BaseMesh, norm


class Mesh(BaseMesh):
    def prism(self,polygon,z,height,material,part,taper=1):
        center=np.mean(polygon,axis=0)
        low=[(x,y,z) for x,y in polygon]
        high=[(*(center+(np.array((x,y))-center)*taper),z+height) for x,y in polygon]
        self.face(low[::-1],material,part);self.face(high,material,part)
        for i in range(len(low)):
            j=(i+1)%len(low);self.face([low[i],low[j],high[j],high[i]],material,part)

    def cylinder(self,x,y,z,r,h,material,part,n=12,taper=1):
        points=[(x+r*math.cos(2*math.pi*i/n),y+r*math.sin(2*math.pi*i/n)) for i in range(n)]
        self.prism(points,z,h,material,part,taper)

    def wall(self,a,b,width,height,material,part='wall',z=0):
        a,b=np.array(a,dtype=float),np.array(b,dtype=float)
        t=(b-a)/np.linalg.norm(b-a);side=np.array((-t[1],t[0]))*width/2
        self.prism([a-side,b-side,b+side,a+side],z,height,material,part)

    def oriented(self, points, material, part, direction):
        p=np.asarray(points,dtype=float)
        if np.dot(np.cross(p[1]-p[0],p[2]-p[0]),direction)<0:p=p[::-1]
        self.face(p,material,part)

    def box(self,center,size,material,part='structure',bevel=None):
        # Small detail stays cheap; principal volumes have actual bevel geometry.
        h=np.asarray(size,dtype=float)/2;c=np.asarray(center,dtype=float)
        b=min(.045,float(h.min())*.18) if bevel is None else bevel
        if h.min()<.09 or b==0:return super().box(center,size,material,part)
        for axis in range(3):
            others=[i for i in range(3) if i!=axis]
            for s in (-1,1):
                points=[]
                for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    p=np.zeros(3);p[axis]=s*h[axis];p[others]=[u*(h[others[0]]-b),v*(h[others[1]]-b)];points.append(p+c)
                d=np.zeros(3);d[axis]=s;self.oriented(points,material,part,d)
        for along in range(3):
            a,d=[i for i in range(3) if i!=along]
            for sa in (-1,1):
                for sd in (-1,1):
                    points=[]
                    for t,k in [(-1,0),(1,0),(1,1),(-1,1)]:
                        p=np.zeros(3);p[along]=t*(h[along]-b)
                        p[a]=sa*(h[a]-(b if k else 0));p[d]=sd*(h[d]-(0 if k else b));points.append(p+c)
                    direct=np.zeros(3);direct[a]=sa;direct[d]=sd;self.oriented(points,material,part,direct)
        for sx in (-1,1):
            for sy in (-1,1):
                for sz in (-1,1):
                    signs=np.array((sx,sy,sz));points=[]
                    for axis in range(3):
                        p=h-b;p[axis]=h[axis];points.append(c+p*signs)
                    self.oriented(points,material,part,signs)

    def append(self,other,offset=(0,0,0),angle=0,scale=(1,1,1)):
        a=math.radians(angle);r=np.array(((math.cos(a),-math.sin(a),0),(math.sin(a),math.cos(a),0),(0,0,1)))
        for p,n,mat,part in other.faces:self.face((p*np.asarray(scale))@r.T+offset,mat,part)


def cornice(m,x,y,z,w,d,mat='limestone'):
    for dz,extra,thick in [(0,0,.11),(.12,.12,.1),(.22,.2,.09)]:
        m.box((x,y,z+dz),(w+extra,d+extra,thick),mat,'cornice')


def window(m,x,y,z,w=.38,h=.68):
    # Recess is a real framed opening impression, not a large black stripe.
    m.box((x,y,z),(w,.045,h),'glass','window',0)
    for dx in (-w/2-.055,w/2+.055):m.box((x+dx,y-.02,z),(.08,.11,h+.18),'limestone','window_frame',0)
    m.box((x,y-.045,z-h/2-.06),(w+.22,.19,.09),'limestone','window_sill',0)
    m.box((x,y-.025,z+h/2+.055),(w+.18,.12,.08),'limestone','window_frame',0)
    m.box((x,y-.055,z),(.045,.045,h),'timber','window_mullion',0)


def doorway(m,x,y,z=0,w=.72,h=1.6):
    m.box((x,y,z+h/2),(w,.06,h),'timber','door',0)
    for dx in (-w/2-.09,w/2+.09):m.box((x+dx,y-.035,z+h/2),(.15,.18,h),'limestone','door_frame')
    m.box((x,y-.025,z+h+.06),(w+.38,.22,.15),'limestone','door_lintel')
    for zz in (z+.35,z+h-.32):m.box((x,y-.065,zz),(w,.045,.055),'steel','door_band',0)


def crate(m,x,y,size=.55):
    m.box((x,y,size/2),(size,size,size),'timber','crate')
    for xx in (x-size*.35,x+size*.35):m.box((xx,y-size/2-.014,size/2),(.05,.025,size),'steel','crate_strap',0)


def barrel(m,x,y,z=0):
    m.cylinder(x,y,z,.25,.57,'timber','barrel',12,taper=.95)
    for zz in (z+.09,z+.45):m.ring((x,y,zz),.259,.244,.06,'steel',12,'barrel_hoop')


def well(m,x,y):
    # Approved worker B: pale flat canopy, FOUR pale posts, circular open well.
    m.ring((x,y,0),.49,.35,.55,'smooth_stone',16,'well')
    m.ring((x,y,.53),.56,.34,.12,'limestone',16,'well_coping')
    m.cylinder(x,y,.22,.345,.01,'water','well_water',16)
    for dx in (-.66,.66):
        for dy in (-.55,.55):
            m.box((x+dx,y+dy,1.01),(.105,.105,2.02),'smooth_stone','well_post',0)
            m.box((x+dx,y+dy,.07),(.21,.21,.14),'limestone','well_post_base')
    m.beam((x-.69,y,1.72),(x+.69,y,1.72),.075,'woodlight','well_winch')
    m.beam((x,y,1.7),(x,y,.69),.023,'rope','well_rope')
    m.box((x,y,2.07),(1.72,1.5,.12),'smooth_stone','well_canopy')
    m.box((x,y,2.15),(1.78,1.56,.055),'limestone','well_canopy_trim',0)


def gateway(m):
    # The icon's dominant vertical silhouette: smooth pale portal with a true
    # arch cutout. Filled spandrels avoid the old unsupported cornice/gap.
    y=-3.12;spring=3.05;radius=.96;depth=.77;top=4.58
    m.arch(0,y,spring,radius,.19,depth,'smooth_stone',16)
    for sign in (-1,1):
        m.box((sign*1.5,y,top/2),(.7,depth,top),'smooth_stone','gateway_wing')
        m.box((sign*1.66,y-.46,2.27),(.28,.15,4.54),'limestone','gate_pilaster')
        m.box((sign*1.53,y-.05,.17),(.86,1.01,.34),'limestone','gate_base')
        m.box((sign*1.09,y-.42,3.05),(.28,.15,.13),'goldstone','gate_impost',0)
    outer=radius+.19
    for i in range(16):
        a,b=math.pi*i/16,math.pi*(i+1)/16
        xa,za=outer*math.cos(a),spring+outer*math.sin(a)
        xb,zb=outer*math.cos(b),spring+outer*math.sin(b)
        front=[(xa,y-depth/2,za),(xb,y-depth/2,zb),(xb,y-depth/2,top),(xa,y-depth/2,top)]
        back=[(x,y+depth/2,z) for x,_,z in front]
        m.oriented(front,'smooth_stone','gate_spandrel',(0,-1,0))
        m.oriented(back,'smooth_stone','gate_spandrel',(0,1,0))
        m.oriented([front[2],back[2],back[3],front[3]],'smooth_stone','gate_spandrel',(0,0,1))
    m.box((0,y,4.66),(3.86,.95,.16),'goldstone','gate_frieze')
    m.box((0,y,4.80),(4.07,1.08,.13),'limestone','gate_cornice')
    m.box((0,y,4.91),(4.22,1.14,.095),'goldstone','gate_coping',0)


def caravansary(industrial=False):
    m=Mesh('RT_Caravansary_Industrial' if industrial else 'RT_Caravansary_Ancient')
    wall='brick' if industrial else 'sandstone';roof='roofmetal' if industrial else 'paving'
    # Open perimeter: local foundations only, never a square tile pedestal.
    for x in (-3.34,3.34):
        m.box((x,.05,.17),(1.5,7.45,.34),'stone','footing')
        m.box((x,.05,1.01),(1.4,7.3,1.7),wall,'lodgings')
        if industrial:m.roof(x,.05,1.92,1.67,7.55,.20,roof)
        else:
            m.box((x,.05,1.94),(1.62,7.5,.18),'goldstone','lodge_cornice')
            m.box((x,.05,2.065),(1.5,7.39,.07),'paving','roof',0)
            for side in (-1,1):m.box((x+side*.72,.05,2.13),(.09,7.48,.15),'goldstone','lodge_parapet',0)
        for y in (-2.8,-1.25,.3,1.85,3.05):
            # Interior arcade facing the court, leaving a two-unit garrison lane.
            q=Mesh('arcade');q.arch(0,0,1.14,.39,.12,.25,'limestone',8)
            m.append(q,(x+(-.81 if x>0 else .81),y,0),90)
        for y in (-2.2,0,2.2):
            q=Mesh('window');window(q,0,0,1.37,.26,.47)
            m.append(q,(x+(.716 if x>0 else -.716),y,0),90 if x<0 else -90)
    m.box((0,3.1,1.02),(5.25,1.17,2.04),wall,'store_wall')
    cornice(m,0,3.1,2.05,5.35,1.25,'goldstone')
    for x in (-1.7,0,1.7):doorway(m,x,2.49,w=.62,h=1.55)
    gateway(m)
    for x in (-2.36,2.36):
        m.box((x,-3.12,.81),(1.0,.5,1.62),wall,'gate_return')
        m.box((x,-3.12,1.65),(1.08,.59,.11),'goldstone','gate_return_cap',0)
    well(m,-1.94,.2)
    crate(m,2.0,1.62,size=.58);barrel(m,2.05,.66)
    for x in (1.5,2.2):m.box((x,-1.8,.78),(.07,.07,1.56),'timber','awning_post',0)
    m.face([(1.45,-.9,1.9),(2.62,-.9,1.9),(2.3,-1.88,1.56),(1.43,-1.88,1.56)],'goldcloth','awning')
    m.face([(1.43,-1.88,1.56),(2.3,-1.88,1.56),(2.62,-.9,1.9),(1.45,-.9,1.9)],'goldcloth','awning')
    if industrial:
        m.box((2.09,3.1,2.8),(.39,.39,1.5),'brick','chimney');cornice(m,2.09,3.1,3.5,.4,.4,'stone')
        m.box((0,-3.53,4.42),(.9,.055,.18),'blue','service_sign',0)
        for x in (-1.54,1.54):m.box((x,-3.75,2.35),(.17,.2,.3),'brass','lantern')
    return m


def slit_window(m,x,y,z,h=.68):
    m.box((x,y,z),(.27,.035,h),'glass','slit_window',0)
    m.box((x,y-.025,z-h/2-.035),(.34,.10,.055),'goldstone','slit_sill',0)


def banner(m,x,y,top=3.91,bottom=1.18,width=.36):
    # Two-sided folded cloth. Red pennants are taken from wonder painting A.
    pts=[(x-width/2,y,top),(x,y-.045,top),(x+width/2,y,top),
         (x-width/2,y+.015,bottom+.15),(x,y-.025,bottom),(x+width/2,y+.015,bottom+.15)]
    for ids in ((0,3,4,1),(1,4,5,2)):
        f=[pts[i] for i in ids];m.oriented(f,'banner','treasury_banner',(0,-1,0))
        m.oriented(f,'banner','treasury_banner_back',(0,1,0))
    m.box((x,y-.025,top+.06),(width+.10,.09,.075),'brass','banner_rail',0)
    # A small gold branch reinforces the painting motif without lettering.
    m.beam((x,y-.058,bottom+.31),(x,y-.058,bottom+.85),.018,'brass','banner_branch')
    for side in (-1,1):
        for i in range(3):
            z=bottom+.4+i*.13
            m.oriented([(x,y-.066,z),(x+side*.09,y-.066,z+.12),(x+side*.045,y-.066,z+.02)],'brass','banner_leaf',(0,-1,0))


def treasury_seal(m,x,y,z):
    q=Mesh('seal');q.cylinder(0,0,0,.36,.045,'patina','coin_seal',20)
    q.ring((0,0,.042),.365,.326,.026,'brass',20,'seal_rim')
    for p,n,mat,part in q.faces:
        v=p.copy();v[:,0]+=x;v[:,1]=y-p[:,2];v[:,2]=z+p[:,1];m.face(v,mat,part)
    m.beam((x-.06,y-.08,z-.23),(x+.06,y-.08,z+.24),.022,'brass','seal_branch')
    for side in (-1,1):
        for i in range(3):
            zz=z-.16+i*.13;xx=x+(zz-z)*.24
            points=[(xx,y-.095,zz),(xx+side*.14,y-.095,zz+.035),
                    (xx+side*.16,y-.095,zz+.14),(xx+side*.045,y-.095,zz+.085)]
            m.oriented(points,'brass','seal_leaf',(0,-1,0))


def ministry():
    m=Mesh('RT_MinistryOfCoin')
    # Portrait B governs the asymmetric massing. Painting A supplies only the
    # treasury entrance treatment: pale pilasters, steps, banners and seal.
    m.box((.87,.73,2.93),(4.22,3.94,5.56),'ochre_plaster','counting_house')
    m.box((.87,.73,.13),(4.42,4.14,.26),'stone','main_footing')
    cornice(m,.87,.73,5.68,4.34,4.06,'limestone')
    m.box((.87,.73,5.95),(4.17,3.89,.075),'paving','roof_terrace',0)
    for x in (-1.20,2.94):m.box((x,.73,6.00),(.12,4.04,.18),'limestone','upper_parapet',0)
    for y in (-1.25,2.72):m.box((.87,y,6.00),(4.25,.12,.18),'limestone','upper_parapet',0)
    # Lower LEFT wing is a separate volume, not a symmetric tier underneath.
    m.box((-2.30,-.02,1.98),(2.45,3.32,3.66),'ochre_plaster','left_office')
    m.box((-2.30,-.02,.14),(2.67,3.52,.28),'stone','office_footing')
    cornice(m,-2.30,-.02,3.79,2.59,3.44,'limestone')
    m.box((-2.30,-.02,4.06),(2.37,3.24,.07),'paving','office_terrace',0)
    for x in (-3.48,-1.12):m.box((x,-.02,4.12),(.11,3.36,.17),'limestone','office_parapet',0)
    for y in (-1.65,1.61):m.box((-2.30,y,4.12),(2.45,.11,.17),'limestone','office_parapet',0)
    # Broad clean wall planes, narrow dark openings, restrained trim.
    m.box((.87,-1.252,4.22),(4.25,.095,.14),'limestone','storey_band',0)
    for x in (-.69,.45,1.61,2.57):slit_window(m,x,-1.268,4.99,.68)
    for x in (-2.99,-2.14,-1.41):slit_window(m,x,-1.70,3.19,.54)
    for y in (-.70,.55,1.77):
        for z in (2.96,4.98):
            q=Mesh('slit');slit_window(q,0,0,z);m.append(q,(2.995,y,0),90)
    for x in (-.68,.5,1.67,2.51):
        for z in (2.96,4.98):
            q=Mesh('rear_slit');slit_window(q,0,0,z);m.append(q,(x,2.715,0),180)
    for y in (-.7,.58):
        q=Mesh('office_slit');slit_window(q,0,0,3.19,.54);m.append(q,(-3.542,y,0),-90)
    for x in (-2.95,-1.67):
        q=Mesh('office_rear');slit_window(q,0,0,3.19,.54);m.append(q,(x,1.655,0),180)
    q=Mesh('service');doorway(q,0,0,.2,.77,1.8);m.append(q,(.84,2.74,0),180)
    m.box((.84,2.99,.15),(1.24,.45,.23),'limestone','service_step')
    # The treasury sits forward and to the RIGHT, as in the chosen icon.
    cx=1.28;front=-2.01
    m.box((cx,-1.52,2.34),(3.40,1.00,3.96),'smooth_stone','treasury_facade')
    m.box((cx,front-.047,1.69),(1.08,.06,2.54),'glass','treasury_recess',0)
    m.box((cx,front-.084,1.59),(.85,.045,2.28),'timber','treasury_door',0)
    for side in (-1,1):
        for dx in (.75,1.54):
            xx=cx+side*dx
            m.box((xx,front-.17,2.35),(.29,.42,4.04),'limestone','treasury_pilaster')
            m.box((xx,front-.18,.46),(.41,.49,.26),'smooth_stone','treasury_base')
            m.box((xx,front-.18,4.22),(.40,.5,.20),'limestone','treasury_capital')
        banner(m,cx+side*1.125,front-.17)
    m.box((cx,front-.165,3.06),(1.54,.18,.12),'brass','door_entablature',0)
    cornice(m,cx,-1.53,4.35,3.6,1.32,'limestone')
    # Painting A's muted green shallow roof belongs to the entry canopy only;
    # the main counting house retains the approved portrait's flat silhouette.
    m.roof(cx,-1.53,4.64,3.77,1.44,.18,'patina')
    treasury_seal(m,cx,front-.23,3.63)
    for i in range(5):
        m.box((cx,-2.42-i*.235,.095+(4-i)*.073),(3.42+i*.09,.31,.16),'limestone','treasury_step')
    # Portrait B's gold awning and open counting counter on the low left wing.
    for x in (-3.34,-1.24):m.box((x,-2.37,1.18),(.12,.12,2.14),'smooth_stone','awning_post',0)
    m.face([(-3.56,-1.70,2.63),(-1.00,-1.70,2.63),(-1.00,-2.52,2.19),(-3.56,-2.52,2.19)],'goldcloth','awning')
    m.face([(-3.56,-2.52,2.19),(-1.00,-2.52,2.19),(-1.00,-1.70,2.63),(-3.56,-1.70,2.63)],'goldcloth','awning_back')
    m.box((-2.3,-1.715,1.14),(1.76,.05,1.7),'glass','counting_recess',0)
    m.box((-2.3,-2.04,.7),(1.91,.57,.91),'timber','counting_counter')
    return m


def irrigation():
    m=Mesh('RT_IrrigationWorks')
    # A gravity-fed civic waterworks, with an open cistern, aqueduct and gate.
    for a,b in [((-2.3,-2.8),(2.3,-2.8)),((2.3,-2.8),(2.3,.85)),((2.3,.85),(-2.3,.85)),((-2.3,.85),(-2.3,-2.8))]:
        m.wall(a,b,.27,.91,'stone','basin_wall');m.wall(a,b,.36,.11,'limestone','basin_coping',.91)
    m.box((0,-.98,.57),(4.27,3.3,.025),'water','reservoir',0)
    for y in (1.55,2.85):
        q=Mesh('arch');q.arch(0,0,.8,.43,.19,.47,'limestone',10);m.append(q,(0,y,0))
    for x in (-.65,.65):m.box((x,2.03,1.67),(.19,3.0,.51),'limestone','feeder_wall')
    m.box((0,2.03,1.47),(1.12,3.0,.075),'water','feeder_water',0)
    for x in (-.78,.78):m.box((x,.62,1.18),(.14,.18,2.36),'timber','sluice_frame',0)
    m.box((0,.62,2.44),(1.85,.25,.18),'woodlight','sluice_header')
    m.box((0,.62,1.03),(1.35,.14,1.35),'timber','sluice_gate')
    m.cylinder(0,.62,1.4,.055,1.5,'steel','sluice_screw',8)
    m.ring((0,.62,2.7),.31,.25,.06,'steel',12,'handwheel')
    for x in (-.3,.3):m.box((x,-3.25,.28),(.15,1.08,.46),'stone','outlet')
    m.box((0,-3.25,.16),(.42,1.08,.02),'water','outlet_water',0)
    m.box((-3.0,1.8,1.07),(1.65,2.57,2.14),'plaster','keeper_house')
    m.roof(-3,1.8,2.17,1.95,2.85,.43,'tile');doorway(m,-3,.48,w=.67,h=1.45)
    window(m,-3.02,.464,1.81,.35,.3)
    # Spillway stairs double as a maintenance walkway.
    for i in range(5):m.box((2.7,-.1+i*.36,.08+i*.12),(.61,.4,.16),'limestone','maintenance_step')
    barrel(m,-2.88,-.35)
    return m


def truck():
    m=Mesh('RT_MotorizedCaravan')
    # Early combustion-era civilian 6x4 cargo lorry; no weapons or army markings.
    m.box((0,.18,.7),(1.9,5.15,.27),'steel','chassis')
    m.box((0,1.04,1.13),(2.03,3.27,.28),'timber','cargo_deck')
    for x in (-.99,.99):
        m.box((x,1.05,1.52),(.12,3.25,.58),'woodlight','cargo_side')
        for y in (-.38,.52,1.45,2.47):m.box((x,y,1.73),(.11,.1,1.12),'steel','cargo_stanchion',0)
    m.box((0,2.63,1.52),(2.06,.11,.58),'woodlight','tailgate')
    # Curved canvas canopy, subdivided so the profile isn't a cuboid.
    for i in range(12):
        a,b=math.pi*i/12,math.pi*(i+1)/12
        m.face([(1.04*math.cos(a),-.5,1.91+.59*math.sin(a)),(1.04*math.cos(a),2.64,1.91+.59*math.sin(a)),(1.04*math.cos(b),2.64,1.91+.59*math.sin(b)),(1.04*math.cos(b),-.5,1.91+.59*math.sin(b))],'canvas','cargo_canopy')
    # Close the canvas ends with shaped front/rear panels and modest tie ropes.
    for y,flip in [(-.5,False),(2.64,True)]:
        pts=[(1.04*math.cos(math.pi*i/12),y,1.91+.59*math.sin(math.pi*i/12)) for i in range(13)]
        m.face(pts[::-1] if flip else pts,'canvas','cargo_end')
    for x in (-1.06,1.06):
        for y in (-.38,.52,1.45,2.47):m.beam((x,y,2.06),(x,y,1.27),.018,'rope','canopy_tie')
    m.box((0,-1.23,1.53),(1.85,1.39,1.36),'truckpaint','cab')
    m.box((0,-1.23,2.27),(1.98,1.55,.17),'truckpaint','cab_roof')
    m.box((0,-2.31,1.31),(1.32,.79,.57),'truckpaint','hood')
    m.box((0,-2.73,1.22),(1.28,.06,.71),'steel','radiator')
    for x in np.linspace(-.49,.49,10):m.box((x,-2.772,1.23),(.035,.025,.57),'charcoal','grille',0)
    m.box((0,-1.949,1.98),(1.55,.032,.48),'glass','windscreen',0)
    m.box((0,-1.976,1.98),(.045,.035,.5),'steel','windscreen_divider',0)
    for x in (-.94,.94):
        m.box((x,-1.28,1.97),(.04,.88,.46),'glass','cab_side_glass',0)
        m.box((x*1.06,-1.19,1.58),(.045,.18,.04),'steel','door_handle',0)
        m.box((x*1.14,-1.57,.76),(.41,1.87,.13),'truckpaint','running_board')
        q=Mesh('headlamp');q.cylinder(0,0,0,.13,.13,'steel','headlamp_case',12)
        q.cylinder(0,0,.129,.105,.02,'brass','headlamp',12)
        for p,n,mat,part in q.faces:
            v=p.copy();v[:,0]=p[:,0]+x*.98;v[:,1]=-p[:,2]-2.45;v[:,2]=p[:,1]+1.11;m.face(v,mat,part)
        m.box((x*1.25,-1.91,1.91),(.14,.14,.23),'steel','mirror')
        m.beam((x,-1.83,1.94),(x*1.25,-1.91,1.94),.032,'steel','mirror_arm')
    m.box((0,-2.94,.79),(2.1,.14,.16),'steel','front_bumper')
    m.box((0,2.84,.82),(2.12,.15,.16),'steel','rear_bumper')
    for y in (-1.96,1.08,2.28):
        m.beam((-1.17,y,.55),(1.17,y,.55),.16,'steel','axle')
        for sign in (-1,1):
            label=('L' if sign<0 else 'R')+str(y)
            w=Mesh('wheel');w.cylinder(0,0,-.15,.55,.3,'rubber','wheel_'+label,16)
            w.cylinder(0,0,-.17,.28,.34,'truckpaint','wheel_'+label,12)
            w.cylinder(0,0,-.2,.11,.4,'steel','wheel_'+label,10)
            for p,n,mat,part in w.faces:
                q=p.copy();q[:,0]=p[:,2]+sign*1.08;q[:,1]=p[:,1]+y;q[:,2]=-p[:,0]+.55;m.face(q,mat,part)
    for sign in (-1,1):
        for i in range(12):
            a=math.pi*i/12;b=math.pi*(i+1)/12
            def point(x,r,t):return (x*sign,-1.96+r*math.cos(t),.55+r*math.sin(t))
            m.oriented([point(.76,.66,a),point(1.43,.66,a),point(1.43,.66,b),point(.76,.66,b)],'truckpaint','front_fender',(0,math.cos((a+b)/2),math.sin((a+b)/2)))
            m.oriented([point(1.43,.66,a),point(1.43,.61,a),point(1.43,.61,b),point(1.43,.66,b)],'truckpaint','fender_rim',(sign,0,0))
        m.box((sign*.87,2.905,1.04),(.16,.08,.1),'brass','tail_lamp',0)
    # Visible independent suspension and ribs supply useful normal/highlight cues.
    for x in (-.7,.7):m.box((x,1.66,.56),(.11,1.75,.08),'steel','leaf_spring',0)
    m.cylinder(.81,2.6,.8,.04,1.0,'steel','exhaust',8)
    return m
