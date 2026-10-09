#!/usr/bin/env python3
"""Original editable outpost meshes from the eight approved era concepts.

Source geometry only: OBJ/GLB/BR2, never a substitute for converted GR2 assets.
Run with NumPy and Pillow. Does not modify either playable mod or the older
shared map-model source set. Coordinates: Z up, entrance south, garrison at 0,0.
"""
from pathlib import Path
import json
import math
import zipfile
import numpy as np
from build_models import Mesh as BaseMesh, norm
from outpost_mesh_io import export, make_atlas, render, make_gallery, MATERIALS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/models/outpost-eras-v1'
APPROVAL = ROOT / 'docs/art/outpost-era-concepts-v1/approved.json'


class Mesh(BaseMesh):
    def oriented(self,points,material,part,direction):
        p=np.asarray(points,dtype=float)
        if np.dot(np.cross(p[1]-p[0],p[2]-p[0]),direction)<0:p=p[::-1]
        self.face(p,material,part)

    def box(self,center,size,material,part='structure'):
        # Tiny bevels give principal volumes restrained edge highlights without
        # spending triangles on every crate, railing, log or sandbag.
        h=np.asarray(size,dtype=float)/2;c=np.asarray(center,dtype=float)
        principal={'tower_wall','tower_upper','tower_deck','store_wall','gate_pier',
                   'gate_gallery','crenel','gabion'}
        if part not in principal or h.min()<.10:return super().box(center,size,material,part)
        b=min(.04,float(h.min())*.15)
        for axis in range(3):
            other=[i for i in range(3) if i!=axis]
            for s in (-1,1):
                points=[]
                for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    p=np.zeros(3);p[axis]=s*h[axis]
                    p[other]=[u*(h[other[0]]-b),v*(h[other[1]]-b)];points.append(p+c)
                direction=np.zeros(3);direction[axis]=s;self.oriented(points,material,part,direction)
        for along in range(3):
            a,d=[i for i in range(3) if i!=along]
            for sa in (-1,1):
                for sd in (-1,1):
                    points=[]
                    for t,k in [(-1,0),(1,0),(1,1),(-1,1)]:
                        p=np.zeros(3);p[along]=t*(h[along]-b)
                        p[a]=sa*(h[a]-(b if k else 0));p[d]=sd*(h[d]-(0 if k else b));points.append(p+c)
                    direction=np.zeros(3);direction[a]=sa;direction[d]=sd
                    self.oriented(points,material,part,direction)
        for sx in (-1,1):
            for sy in (-1,1):
                for sz in (-1,1):
                    signs=np.array((sx,sy,sz));points=[]
                    for axis in range(3):
                        p=h-b;p[axis]=h[axis];points.append(c+p*signs)
                    self.oriented(points,material,part,signs)

    def prism(self, polygon, z, height, material, part, taper=1):
        """Convex CCW footprint with an optional smaller top."""
        center=np.mean(polygon,axis=0)
        low=[(x,y,z) for x,y in polygon]
        high=[(*(center+(np.array((x,y))-center)*taper),z+height) for x,y in polygon]
        self.face(low[::-1],material,part)
        self.face(high,material,part)
        for i in range(len(low)):
            j=(i+1)%len(low)
            self.face([low[i],low[j],high[j],high[i]],material,part)

    def cylinder(self,x,y,z,r,h,material,part,n=8,taper=1):
        points=[(x+r*math.cos(2*math.pi*i/n),y+r*math.sin(2*math.pi*i/n)) for i in range(n)]
        self.prism(points,z,h,material,part,taper)

    def hip(self,x,y,z,w,d,rise,material,part='roof'):
        p=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z)]
        self.face(p[::-1],material,part)
        for i in range(4): self.face([p[i],p[(i+1)%4],(x,y,z+rise)],material,part)

    def cone(self,x,y,z,r,rise,material,part='roof',n=8):
        p=[(x+r*math.cos(2*math.pi*i/n),y+r*math.sin(2*math.pi*i/n),z) for i in range(n)]
        self.face(p[::-1],material,part)
        for i in range(n): self.face([p[i],p[(i+1)%n],(x,y,z+rise)],material,part)

    def wall(self,a,b,width,height,material,part='wall',z=0):
        a,b=np.array(a,dtype=float),np.array(b,dtype=float)
        t=(b-a)/np.linalg.norm(b-a); side=np.array((-t[1],t[0]))*width/2
        self.prism([a-side,b-side,b+side,a+side],z,height,material,part)

    def arch_hut(self,x,y,width,depth,height):
        # Curved opaque corrugated shell and end walls. A dark door sits proud.
        for i in range(10):
            a,b=math.pi*i/10,math.pi*(i+1)/10
            p=[(x+width/2*math.cos(t),yy,.15+height*math.sin(t))
               for yy,t in [(y-depth/2,a),(y-depth/2,b),(y+depth/2,b),(y+depth/2,a)]]
            self.face(p[::-1],'olive','hut_roof')
        ring=[(x+width/2*math.cos(math.pi*i/10),.15+height*math.sin(math.pi*i/10)) for i in range(11)]
        self.face([(xx,y-depth/2,zz) for xx,zz in ring],'olive','store_wall')
        self.face([(xx,y+depth/2,zz) for xx,zz in ring[::-1]],'olive','store_wall')
        self.box((x,y-depth/2-.025,.72),(.72,.055,1.24),'charcoal','door')
        for i in range(1,7):
            yy=y-depth/2+depth*i/7
            for k in range(10):
                a,b=math.pi*k/10,math.pi*(k+1)/10
                self.beam((x+(width/2+.018)*math.cos(a),yy,.15+(height+.018)*math.sin(a)),
                          (x+(width/2+.018)*math.cos(b),yy,.15+(height+.018)*math.sin(b)),.035,'steel','hut_roof_rib')


def crate(m,x,y,z=0,size=.55):
    m.box((x,y,z+size/2),(size,size,size),'timber','crate')
    for xx in (x-size*.36,x+size*.36):
        m.box((xx,y-size/2-.012,z+size/2),(.055,.027,size),'woodlight','crate_strap')
    m.beam((x-size*.4,y-size/2-.027,z+.07),(x+size*.4,y-size/2-.027,z+size-.07),.05,'woodlight','crate_strap')


# Each era follows its approved composition. These helpers describe architecture,
# not a shared square footprint: outlines and massing are authored per era.
def regular(x,y,r,n=8,angle=0):
    return [(x+r*math.cos(angle+2*math.pi*i/n),y+r*math.sin(angle+2*math.pi*i/n)) for i in range(n)]


def turned_box(m,center,size,angle,material,part):
    temp=Mesh('component');temp.box((0,0,0),size,material,part)
    c,s=math.cos(angle),math.sin(angle);rotation=np.array(((c,-s,0),(s,c,0),(0,0,1)))
    for p,n,mat,label in temp.faces:m.face(p@rotation.T+center,mat,label)


def band(m,polygon,z,height,width,material,part='coping'):
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):m.wall(a,b,width,height,material,part,z)


def curtain(m,path,height,material='stone',width=.48,crenels=False,walk=False):
    # Path is open across the entrance, CCW from the right gate pier.
    for a,b in zip(path[:-1],path[1:]):
        a,b=np.array(a,dtype=float),np.array(b,dtype=float)
        tangent=(b-a)/np.linalg.norm(b-a);inside=np.array((-tangent[1],tangent[0]))
        m.wall(a,b,width,height,material,'wall')
        m.wall(a,b,width+.09,.14,'limestone' if material!='concrete' else material,'coping',height)
        if walk:
            aa=a+inside*.49;bb=b+inside*.49
            m.wall(aa,bb,.67,.14,'timber','wall_walk',height-.48)
            for point in (a,b):
                m.box((*point,height+.18),(.5,.5,.5),material,'parapet_pier')
            m.beam((*aa,height+.3),(*bb,height+.3),.10,'timber','walk_rail')
        if crenels:
            count=max(1,round(np.linalg.norm(b-a)/.78))
            for i in range(count):
                q=a+(b-a)*(i+.5)/count
                turned_box(m,(*q,height+.37),(.40,width+.05,.60),math.atan2(tangent[1],tangent[0]),material,'crenel')


def slit(m,x,y,z,w=.25,h=.44,material='limestone',side='front'):
    # Raised reveals catch light around a dark recessed opening at map scale.
    temp=Mesh('reveal')
    temp.box((0,-.008,0),(w,.035,h),'charcoal','window')
    for sx in (-1,1):temp.box((sx*(w/2+.055),-.035,0),(.11,.075,h+.12),material,'window_reveal')
    for sz in (-1,1):temp.box((0,-.048,sz*(h/2+.05)),(w+.22,.10,.10),material,'window_reveal')
    angle={'front':0,'right':math.pi/2,'back':math.pi,'left':-math.pi/2}[side]
    c,s=math.cos(angle),math.sin(angle);rot=np.array(((c,-s,0),(s,c,0),(0,0,1)))
    for p,n,mat,part in temp.faces:m.face(p@rot.T+(x,y,z),mat,part)


def stairs(m,x,y,z=0,width=.8,rise=.50,run=.75,steps=4):
    for i in range(steps):
        depth=run/steps
        m.box((x,y+depth*(i+.5),z+rise*(i+1)/(steps*2)),(width,depth,rise*(i+1)/steps),'stone','step')


def gate(m,y=-3.35,arched=False,modern=False):
    if modern:
        for x in (-1.22,1.22):m.box((x,y,1.0),(.36,.48,2.0),'concrete','gate_pier')
        for x in np.linspace(-1.02,1.02,11):m.box((x,y,.82),(.045,.06,1.48),'steel','gate_bar')
        for z in (.13,1.55):m.box((0,y,z),(2.1,.10,.08),'steel','gate_rail')
        m.box((1.22,y-.26,1.14),(.31,.04,.56),'blue','banner')
        return
    if arched:m.arch(0,y,1.30,1.04,.25,.62,'limestone',segments=8)
    else:
        for x in (-1.23,1.23):m.box((x,y,1.10),(.37,.68,2.20),'limestone','gate_pier')
        m.box((0,y,2.18),(2.45,.72,.20),'timber','gate_lintel')
    top=1.30+math.sqrt(1.04**2-.99**2) if arched else 2.05
    for x in np.linspace(-.92,.92,10):
        h=1.30+math.sqrt(max(0,1.04**2-x*x)) if arched else 2.05
        m.box((x,y,.05+h/2),(.192,.12,h),'timber','door')
    for z in (.45,1.20):m.box((0,y-.08,z),(2.05,.055,.095),'steel','gate_strap')
    for x in (-1.36,1.36):
        m.box((x,y-.38,1.47),(.30,.045,.85),'blue','banner')


def pitched_roof(m,x,y,z,w,d,rise,material,axis='y'):
    # Axis describes the roof ridge. Explicit bargeboards preserve the profile.
    temp=Mesh('roof');temp.roof(0,0,z,w,d,rise,material)
    for yy in (-d/2,d/2):
        for xx in (-w/2,w/2):temp.beam((xx,yy,z),(0,yy,z+rise),.075,'woodlight' if material in ('slate','thatch') else 'roofmetal','roof_trim')
    rotation=np.array(((0,1,0),(-1,0,0),(0,0,1))) if axis=='x' else np.eye(3)
    for p,n,mat,part in temp.faces:m.face(p@rotation.T+(x,y,0),mat,part)


def lean_to(m,x,y,w=2.4,d=1.25,z=1.6,material='thatch',angle=0):
    # Open frontage, visible posts/braces and a pitched single-plane roof.
    temp=Mesh('lean_to')
    temp.box((0,d/2,.69),(w,.13,1.38),'timber','store_back')
    for xx in (-w/2+.10,w/2-.10):
        for yy in (-d/2+.08,d/2-.08):temp.box((xx,yy,z/2),(.13,.13,z),'timber','shelter_post')
        temp.beam((xx,-d/2,z-.43),(xx+.28*(-1 if xx>0 else 1),-d/2,z),.095,'woodlight','shelter_brace')
    low=[(-w/2-.13,-d/2-.18,z),(w/2+.13,-d/2-.18,z),(w/2+.13,d/2+.12,z+.48),(-w/2-.13,d/2+.12,z+.48)]
    temp.face(low,material,'roof');temp.face([(x,y,zz-.10) for x,y,zz in low[::-1]],'timber','roof')
    for i in range(4):
        a,b=low[i],low[(i+1)%4]
        temp.face([a,(a[0],a[1],a[2]-.1),(b[0],b[1],b[2]-.1),b],material,'roof')
    crate(temp,-w*.22,0,size=.53);crate(temp,w*.20,.03,size=.58)
    c,s=math.cos(angle),math.sin(angle);rot=np.array(((c,-s,0),(s,c,0),(0,0,1)))
    for p,n,mat,part in temp.faces:m.face(p@rot.T+(x,y,0),mat,part)


def supplies(m,positions,modern=False):
    for i,(x,y) in enumerate(positions):
        crate(m,x,y,size=.52 if i%2 else .65)
        if i%2==0:crate(m,x+.06,y,.65,.40)
        else:m.cylinder(x+.43,y,.02,.19,.54,'olive' if modern else 'timber','barrel',n=6)


def roofed_tower(m,x,y,material='stone',roof='slate',height=3.45,w=1.5):
    footprint=[(x-w/2,y-w/2),(x+w/2,y-w/2),(x+w/2,y+w/2),(x-w/2,y+w/2)]
    m.prism(footprint,0,height,material,'tower_wall',.92)
    m.box((x,y,.12),(w+.2,w+.2,.24),'stone','tower_foot')
    m.box((x,y,height-.70),(w+.12,w+.12,.16),'limestone','tower_band')
    m.box((x,y,height),(w+.20,w+.20,.18),'limestone','cornice')
    for z in (height*.38,height-.34):
        slit(m,x,y-w*.48,z,.18,.40,material)
        slit(m,x+w*.48,y,z,.18,.40,material,side='right')
    m.hip(x,y,height+.09,w+.47,w+.47,.82,roof)


def ancient():
    m=Mesh('RO_Ancient')
    path=[(1.14,-3.05),(2.95,-2.70),(3.55,-1.55),(3.4,2.32),(2.32,3.2),(-2.40,3.14),(-3.40,2.20),(-3.65,-1.40),(-2.68,-2.68),(-1.14,-3.05)]
    for si,(a,b) in enumerate(zip(path[:-1],path[1:])):
        a,b=np.array(a),np.array(b);count=max(2,round(np.linalg.norm(b-a)/.34))
        for i in range(count):
            x,y=a+(b-a)*(i+.5)/count;h=1.43+.13*math.sin(i*2.41+si)
            m.cylinder(x,y,0,.175,h,'timber','palisade',n=4)
            m.cone(x,y,h,.175,.23,'woodlight','palisade_tip',n=4)
        for z in (.46,1.12):m.beam((*a,z),(*b,z),.12,'woodlight','palisade_rail')
        mid=(a+b)/2;out=norm((b[1]-a[1],a[0]-b[0]))
        m.beam((*(mid+out*.42),.08),(*mid,1.34),.14,'timber','palisade_buttress')
    x,y=-2.45,1.4
    for dx in (-.72,.72):
        for dy in (-.72,.72):m.cylinder(x+dx,y+dy,0,.11,4.20,'timber','tower_post',n=6)
    m.box((x,y,2.66),(1.95,1.95,.20),'woodlight','tower_deck')
    for z in (.78,1.75):
        for yy in (y-.72,y+.72):m.beam((x-.72,yy,z),(x+.72,yy,z),.14,'timber','tower_brace')
    for yy in (y-.72,y+.72):
        for a,b in [((x-.72,yy,.1),(x+.72,yy,2.65)),((x+.72,yy,.1),(x-.72,yy,2.65))]:m.beam(a,b,.14,'woodlight','tower_brace')
    for xx in (x-.72,x+.72):m.beam((xx,y-.72,.12),(xx,y+.72,2.63),.14,'timber','tower_brace')
    for a,b in [((x-.92,y-.92),(x+.92,y-.92)),((x+.92,y-.92),(x+.92,y+.92)),((x+.92,y+.92),(x-.92,y+.92)),((x-.92,y+.92),(x-.92,y-.92))]:
        m.wall(a,b,.12,.58,'timber','tower_rail',2.77)
        m.beam((*a,3.37),(*b,3.37),.13,'woodlight','tower_rail')
    # Broad tiered thatch silhouette, with exposed crossed crown rafters.
    for z,w,rise in [(4.17,2.65,.35),(4.49,1.95,.38),(4.84,1.10,.39)]:m.hip(x,y,z,w,w,rise,'thatch')
    m.beam((x-.32,y,5.15),(x+.32,y,5.36),.14,'timber','finial')
    m.beam((x,y-.32,5.15),(x,y+.32,5.36),.14,'timber','finial')
    for xx in (x-.32,x+.32):m.beam((xx,y-1.29,.08),(xx,y-.86,2.64),.09,'woodlight','ladder')
    for i in range(10):m.beam((x-.37,y-1.29+i*.043,.18+i*.25),(x+.37,y-1.29+i*.043,.18+i*.25),.07,'woodlight','ladder')
    lean_to(m,1.88,2.13,2.5,1.34,1.57,'thatch')
    supplies(m,[(-2.75,-.25),(2.70,.78)])
    for x in (-1.15,1.15):m.cylinder(x,-3.05,0,.15,1.96,'timber','gate_post',n=6)
    # Sagging cloth instead of a straight beam between two square poles.
    for i in range(6):
        a=-1.1+i*2.2/6;b=a+2.2/6
        za=1.86-.26*(1-(a/1.1)**2);zb=1.86-.26*(1-(b/1.1)**2)
        p=[(a,-3.055,za),(b,-3.055,zb),(b,-3.055,zb-.28),(a,-3.055,za-.28)]
        m.face(p,'blue','banner');m.face(p[::-1],'blue','banner')
    return m


def classical():
    m=Mesh('RO_Classical')
    path=[(1.32,-3.20),(3.40,-3.2),(3.40,2.68),(2.85,3.23),(-2.85,3.23),(-3.4,2.68),(-3.4,-3.2),(-1.32,-3.2)]
    curtain(m,path,1.92,'limestone',.50,walk=True)
    for x in (-2.1,2.1):roofed_tower(m,x,-3.10,'limestone','tile',2.73,w=1.38)
    m.box((0,2.55,1.11),(4.35,1.35,2.22),'limestone','store_wall')
    pitched_roof(m,0,2.55,2.26,1.72,4.7,.54,'tile',axis='x')
    m.box((0,1.855,.92),(.68,.06,1.67),'timber','door');stairs(m,0,1.06,width=.9,rise=.38,run=.73)
    for x in (-1.60,-.88,.92,1.60):slit(m,x,1.85,1.50,.20,.32)
    # Built walks with a broad ascending stair, instead of thin floating strips.
    for side in (-1,1):
        for i in range(9):m.box((side*2.93,-1.55+i*.31,(i+1)*.077),(.70,.32,(i+1)*.154),'stone','wall_stair')
        for yy in (-1.4,-.3,.8,2.1):m.box((side*3.44,yy,.92),(.34,.31,1.84),'limestone','buttress')
    lean_to(m,-2.2,1.10,1.30,1.32,1.72,'timber')
    supplies(m,[(1.70,1.58),(-1.58,1.62)])
    gate(m,-3.18)
    return m


def medieval():
    m=Mesh('RO_Medieval')
    path=[(1.35,-3.28),(3.32,-3.28),(3.40,1.62),(2.30,3.22),(-2.55,3.22),(-3.40,2.25),(-3.4,-3.28),(-1.35,-3.28)]
    curtain(m,path,2.02,'stone',.56,crenels=True)
    for x in (-2.90,2.90):roofed_tower(m,x,-2.83,'stone','slate',3.59,w=1.65)
    gate(m,-3.32,arched=True)
    # Open timber gallery above the actual arched gate, with a long roof ridge.
    m.box((0,-3.32,2.64),(2.87,1.06,.20),'timber','gate_gallery_floor')
    m.box((0,-3.32,3.09),(2.65,.88,.65),'timber','gate_gallery')
    for x in (-.91,0,.91):
        m.box((x,-3.78,3.24),(.52,.07,.43),'charcoal','window')
        m.box((x+.33,-3.83,3.17),(.13,.15,.80),'woodlight','gallery_post')
    pitched_roof(m,0,-3.32,3.58,1.37,3.10,.55,'slate',axis='x')
    # Rear half-timbered store has a projecting open loading bay.
    sx,sy=-2.13,2.13
    m.box((sx,sy,1.12),(1.90,1.80,2.24),'plaster','store_wall')
    for dx in (-.84,0,.84):m.box((sx+dx,sy-.92,1.11),(.13,.10,2.22),'timber','half_timber')
    m.box((sx,sy-.925,1.12),(1.0,.035,1.83),'charcoal','door')
    pitched_roof(m,sx,sy,2.30,2.15,2.03,1.08,'slate')
    lean_to(m,sx,1.50,1.88,1.15,1.79,'slate')
    supplies(m,[(1.0,2.6),(2.65,1.25),(-2.66,.22)])
    return m


def renaissance():
    m=Mesh('RO_Renaissance')
    # A tapered, angled enclosure with real projecting pentagonal gun bastions.
    path=[(1.23,-3.20),(2.05,-3.18),(3.18,-2.45),(3.33,.9),(2.18,3.20),(-1.95,3.20),(-3.22,1.5),(-3.38,-2.38),(-2.05,-3.18),(-1.23,-3.20)]
    curtain(m,path,1.92,'stone',.55)
    for a,b in zip(path[:-1],path[1:]):m.wall(a,b,.57,.22,'brick','wall_band',1.55)
    for sign in (-1,1):
        points=[(1.9,-2.30),(2.00,-3.22),(3.20,-4.15),(4.11,-3.06),(3.23,-2.14)]
        if sign<0:points=[(-x,y) for x,y in points[::-1]]
        m.prism(points,0,1.93,'stone','bastion',.84)
        center=np.mean(points,axis=0);top=[tuple(center+(np.array(p)-center)*.84) for p in points]
        band(m,top,1.93,.32,.24,'brick','bastion_parapet');band(m,top,2.25,.10,.28,'limestone')
        slit(m,sign*3.11,-3.81,1.20,.46,.36,'stone')
    x,y=-.38,2.48
    m.cylinder(x,y,0,1.19,3.67,'stone','tower_wall',8)
    for z in (.18,1.82,3.58):m.cylinder(x,y,z,1.25,.14,'limestone','tower_band',8)
    m.cylinder(x,y,3.72,1.23,1.13,'brick','tower_upper',8)
    m.cylinder(x,y,4.81,1.35,.16,'limestone','cornice',8)
    m.cone(x,y,4.97,1.45,.61,'copper','roof',8)
    m.cylinder(x,y,5.55,.11,.24,'copper','finial',8)
    for side,dx,dy in [('front',0,-1.145),('right',1.145,0),('left',-1.145,0),('back',0,1.145)]:
        for z in (2.65,4.22):slit(m,x+dx,y+dy,z,.19,.47,'limestone',side)
    m.box((x,y-1.16,.84),(.53,.045,1.39),'timber','door');stairs(m,x,y-1.40,width=.8,rise=.4,run=.27)
    lean_to(m,-2.44,.44,2.36,1.14,1.67,'tile',angle=math.pi/2)
    gate(m,-3.20,arched=True);supplies(m,[(2.42,.28),(1.75,1.60)])
    return m


def industrial():
    m=Mesh('RO_Industrial')
    path=[(1.30,-3.18),(3.32,-3.18),(3.30,2.30),(2.50,3.16),(-2.50,3.16),(-3.3,2.3),(-3.32,-3.18),(-1.3,-3.18)]
    curtain(m,path,2.16,'brick',.58)
    for x in (-2.87,2.87):
        m.cylinder(x,-2.81,0,1.14,2.92,'brick','blockhouse',8, taper=.96)
        for z in (.12,1.26,2.80):m.cylinder(x,-2.81,z,1.19,.14,'limestone','tower_band',8)
        m.cone(x,-2.81,3.0,1.38,.57,'roofmetal','roof',8)
        for side,dx,dy in [('front',0,-1.06),('right',1.06,0),('left',-1.06,0)]:slit(m,x+dx,-2.81+dy,2.25,.54,.17,'brick',side)
        for i in range(8):
            angle=i*math.pi/4;m.beam((x,-2.81,3.58),(x+1.36*math.cos(angle),-2.81+1.36*math.sin(angle),3.02),.04,'steel','roof_trim')
    sx,sy=.20,2.37
    m.box((sx,sy,1.09),(4.40,1.48,2.18),'brick','store_wall')
    pitched_roof(m,sx,sy,2.20,1.77,4.69,.46,'roofmetal',axis='x')
    m.box((sx-.7,sy-.76,.95),(.74,.06,1.83),'timber','door')
    slit(m,sx-1.6,sy-.77,1.54,.24,.30,'limestone')
    lean_to(m,1.33,1.65,1.70,.80,1.48,'roofmetal')
    for sign in (-1,1):
        for y in (-.94,.5,1.93):
            points=[(sign*3.06,y-.17),(sign*3.84,y-.17),(sign*3.84,y+.17),(sign*3.06,y+.17)]
            if sign<0:points=points[::-1]
            m.prism(points,0,1.65,'brick','buttress',.58)
    gate(m,-3.20);supplies(m,[(-2.23,1.42),(2.6,.35)])
    return m


def modern_perimeter(m,era):
    # Splayed corners and discrete perimeter masses follow the later concepts.
    path=[(1.33,-3.13),(2.68,-3.13),(3.62,-2.10),(3.62,1.85),(2.62,3.08),(-2.56,3.14),(-3.60,2.01),(-3.62,-1.83),(-2.61,-3.13),(-1.33,-3.13)]
    if era=='Modern':curtain(m,path,1.24,'concrete',.42)
    else:
        for a,b in zip(path[:-1],path[1:]):
            a,b=np.array(a,dtype=float),np.array(b,dtype=float);length=np.linalg.norm(b-a)
            count=max(1,round(length/.97))
            for i in range(count):
                aa=a+(b-a)*(i+.015)/count;bb=a+(b-a)*(i+.985)/count
                m.wall(aa,bb,.40,1.10 if era=='Atomic' else 1.4,'concrete','precast_wall')
            if era=='Atomic':
                for i in range(count+1):
                    q=a+(b-a)*i/count;m.cylinder(*q,1.05,.035,.78,'steel','fence_post',n=4)
                for z in (1.23,1.79):m.beam((*a,z),(*b,z),.045,'steel','fence_rail')
                # Broad diagonal lattice in geometry, no alpha-texture dependency.
                for i in range(count):
                    aa=a+(b-a)*i/count;bb=a+(b-a)*(i+1)/count
                    m.beam((*aa,1.23),(*bb,1.79),.025,'steel','fence_rail')
                    m.beam((*aa,1.79),(*bb,1.23),.025,'steel','fence_rail')
    for x,y in [(-3.15,-2.60),(3.15,-2.63),(-3.08,2.57),(3.12,2.48)]:
        if era=='Information':turned_box(m,(x,y,.72),(1.35,.90,1.44),math.pi/4*(1 if x*y>0 else -1),'gabion','gabion')
        elif era=='Modern':
            for layer in range(2):
                for dx in (-.34,.25):
                    turned_box(m,(x+dx,y,1.40+layer*.22),(.65,.39,.25),.15,'sandbag','sandbag')
        else:
            m.prism([(x-.34,y-.28),(x+.34,y-.28),(x+.34,y+.28),(x-.34,y+.28)],0,1.02,'concrete','buttress',.5)
    gate(m,-3.13,modern=True)


def lattice_mast(m,x,y,z,height,width=.28):
    for i in range(3):
        a=2*math.pi*i/3;b=2*math.pi*(i+1)/3
        foot=(x+width*math.cos(a),y+width*math.sin(a),z)
        top=(x+width*.24*math.cos(a),y+width*.24*math.sin(a),z+height)
        m.beam(foot,top,.055,'steel','mast')
        for j in range(4):
            q=j/4;r=(j+1)/4;ra=width*(1-.76*q);rb=width*(1-.76*r)
            m.beam((x+ra*math.cos(a),y+ra*math.sin(a),z+q*height),(x+rb*math.cos(b),y+rb*math.sin(b),z+r*height),.035,'steel','mast')


def control_block(m,atomic=False):
    x,y=-2.35,1.84;w,d=2.35,2.14
    corners=[(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)]
    m.prism(corners,0,3.58 if atomic else 3.86,'concrete','tower_wall',.83)
    height=3.58 if atomic else 3.86
    m.box((x,y,2.02),(w*.94,d*.94,.14),'limestone','tower_band')
    m.box((x,y,height),(w+.20,d+.20,.22),'concrete','tower_deck')
    for xx in (x-.58,x+.58):slit(m,xx,y-d*.43,height-.54,.65,.27,'concrete')
    for yy in (y-.45,y+.45):slit(m,x+w*.43,yy,height-.54,.54,.27,'concrete','right')
    m.box((x,y-d*.49,.99),(.64,.06,1.60),'olive','door')
    m.box((x,y-d*.53-.19,1.94),(.99,.60,.14),'concrete','door_canopy')
    stairs(m,x,y-d/2-.75,width=.89,rise=.42,run=.72)
    if not atomic:
        band(m,[(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)],height+.11,.23,.13,'concrete','roof_parapet')
        for side in (-1,1):
            xx=x+side*(w/2-.09)
            m.prism([(xx-.10,y-d/2-.17),(xx+.10,y-d/2-.17),(xx+.10,y-d/2+.28),(xx-.10,y-d/2+.28)],0,2.12,'concrete','buttress',.50)
    return x,y,height+.13


def modern():
    m=Mesh('RO_Modern');modern_perimeter(m,'Modern');x,y,z=control_block(m)
    m.box((x,y,z+.13),(.62,.62,.26),'olive','radio_base');lattice_mast(m,x,y,z+.26,1.64,.22)
    m.cylinder(x,y,z+1.90,.038,.70,'steel','mast',6)
    for dx,dy in [(-.95,-.86),(.95,-.86),(0,.9)]:m.beam((x+dx,y+dy,z+.12),(x,y,z+1.79),.026,'steel','wire')
    m.arch_hut(2.15,1.47,2.13,2.66,1.68)
    supplies(m,[(-2.70,-.22),(1.56,-.40)],True)
    return m


def radar(m,x,y,z):
    m.cylinder(x,y,z,.40,.44,'olive','radar_base',8,taper=.80)
    m.box((x,y,z+.66),(.48,.56,.70),'olive','radar_base')
    def dish(u,v):return (x+u,y+.18*u*u+.12*v*v,z+1.49+v)
    for u in np.linspace(-1.37,1.37,7):
        half=.82*math.sqrt(max(0,1-(u/1.55)**2))
        # Segmented curved ribs provide a concave silhouette, not a flat grid.
        vv=np.linspace(-half,half,4)
        for a,b in zip(vv[:-1],vv[1:]):m.beam(dish(u,a),dish(u,b),.042,'steel','radar')
    for v in np.linspace(-.65,.65,5):
        half=1.55*math.sqrt(max(0,1-(v/.85)**2));xx=np.linspace(-half,half,5)
        for a,b in zip(xx[:-1],xx[1:]):m.beam(dish(a,v),dish(b,v),.046,'steel','radar')
    for i in range(20):
        a,b=2*math.pi*i/20,2*math.pi*(i+1)/20
        m.beam(dish(1.55*math.cos(a),.85*math.sin(a)),dish(1.55*math.cos(b),.85*math.sin(b)),.085,'olive','radar')
    for dx in (-.77,.77):m.beam((x,y,z+.65),dish(dx,.65),.075,'olive','radar_base')
    m.beam(dish(0,0),(x,y-.43,z+1.49),.075,'olive','radar_feed')
    m.box((x,y-.45,z+1.49),(.25,.22,.24),'olive','radar_feed')
    for a,b in [((-1.21,-1.1),(1.21,-1.1)),((1.21,-1.1),(1.21,1.1)),((1.21,1.1),(-1.21,1.1)),((-1.21,1.1),(-1.21,-1.1))]:
        for t in (0,.5):
            q=np.array(a)*(1-t)+np.array(b)*t;m.box((x+q[0],y+q[1],z+.36),(.06,.06,.72),'steel','railing')
        for dz in (.32,.71):m.beam((x+a[0],y+a[1],z+dz),(x+b[0],y+b[1],z+dz),.045,'steel','railing')


def atomic():
    m=Mesh('RO_Atomic');modern_perimeter(m,'Atomic');x,y,z=control_block(m,True);radar(m,x,y,z)
    m.arch_hut(2.12,1.47,2.12,2.58,1.72)
    # Enclosed generator and side electrical box distinguish the later shelter.
    m.box((2.12,.15,1.04),(.81,.06,1.45),'olive','door')
    m.box((-.55,1.55,.61),(.43,.56,1.22),'olive','electrical_box')
    supplies(m,[(-2.5,-.39),(1.63,-.48)],True)
    return m


def information():
    m=Mesh('RO_Information');modern_perimeter(m,'Information')
    x,y=-2.29,1.12
    m.box((x,y,1.61),(1.37,1.40,3.22),'concrete','tower_wall')
    for z in (.26,1.81,3.15):m.box((x,y,z),(1.52,1.55,.18),'olive','tower_band')
    # Flared observation cab and wraparound glazing are separate volumes.
    m.prism([(x-.83,y-.83),(x+.83,y-.83),(x+.83,y+.83),(x-.83,y+.83)],3.22,.71,'glass','window',1.15)
    for dx in (-.88,.88):
        for dy in (-.88,.88):m.beam((x+dx*.94,y+dy*.94,3.22),(x+dx*1.08,y+dy*1.08,3.94),.10,'olive','window_frame')
    m.box((x,y,3.17),(1.85,1.85,.19),'concrete','cab_base')
    m.box((x,y,4.01),(2.14,2.14,.23),'concrete','tower_deck')
    for a,b in [((-1,-1),(1,-1)),((1,-1),(1,1)),((1,1),(-1,1)),((-1,1),(-1,-1))]:
        m.beam((x+a[0],y+a[1],4.55),(x+b[0],y+b[1],4.55),.048,'steel','railing')
        m.box((x+a[0],y+a[1],4.31),(.05,.05,.48),'steel','railing')
    lattice_mast(m,x,y,4.13,2.09,.23)
    m.box((x+.27,y,6.15),(.39,.17,.72),'concrete','sensor_panel')
    for z,size in [(5.56,.39),(5.17,.28)]:
        m.box((x,y-.20,z),(size,size*.94,size),'concrete','sensor')
        # Circular front lens sits in the protruding camera housing.
        m.box((x,y-.41,z),(size*.65,.045,size*.65),'glass','sensor_lens')
    m.box((x-.47,y+.33,4.32),(.38,.51,.38),'olive','electrical_box')
    m.box((x,y-.735,.85),(.55,.06,1.58),'olive','door');m.box((x,y-.89,1.69),(.79,.50,.13),'concrete','door_canopy')
    for xx in (x-.79,x-.59):m.beam((xx,y+.79,.1),(xx,y+.79,3.06),.045,'steel','ladder')
    for z in np.linspace(.22,2.97,11):m.beam((x-.80,y+.79,z),(x-.58,y+.79,z),.04,'steel','ladder')
    sx,sy=2.25,2.15
    m.box((sx,sy,.97),(2.62,1.76,1.94),'plaster','store_wall')
    m.box((sx,sy,2.01),(2.84,1.99,.16),'concrete','flat_roof')
    for xx in (sx-1.24,sx+1.24):m.box((xx,sy-.90,.97),(.13,.12,1.94),'steel','corner_trim')
    for i in range(4):
        xx=sx-.99+i*.66
        # Angled panels on brackets preserve the distinct roof equipment.
        temp=Mesh('solar');temp.box((0,0,0),(.61,1.57,.07),'solar','solar')
        angle=.18;rot=np.array(((1,0,0),(0,math.cos(angle),-math.sin(angle)),(0,math.sin(angle),math.cos(angle))))
        for p,n,mat,part in temp.faces:m.face(p@rot.T+(xx,sy,2.25),mat,part)
    m.box((sx-.82,sy-.91,.83),(.59,.06,1.62),'olive','door')
    m.box((sx-.82,sy-1.08,1.70),(.80,.40,.13),'concrete','door_canopy')
    # Low draped canopy on the side supply bay (center remains unobstructed).
    ax=sx+.55;ay=.53
    for xx in (ax-.60,ax+.60):m.box((xx,ay-.44,.68),(.065,.065,1.36),'steel','awning_post')
    for a,b in zip(np.linspace(ax-.68,ax+.68,5)[:-1],np.linspace(ax-.68,ax+.68,5)[1:]):
        za=1.48-.20*(1-((a-ax)/.68)**2);zb=1.48-.20*(1-((b-ax)/.68)**2)
        p=[(a,ay-.53,za),(b,ay-.53,zb),(b,ay+.48,1.67),(a,ay+.48,1.67)]
        m.face(p,'olive','awning');m.face(p[::-1],'olive','awning')
    supplies(m,[(2.25,.53),(-2.6,-.25),(3.07,1.42)],True)
    return m


def variant(original,state,era_index):
    """Simplified state geometry keeps the same origin and clear garrison center."""
    m=Mesh(original.name+'_'+state)
    excluded={'roof','finial','banner','window','window_frame','sensor','sensor_panel','sensor_lens',
              'mast','wire','radar','radar_base','solar','solar_grid','awning','hut_roof','hut_roof_rib',
              'ladder','gate_bar','gate_rail','door','railing','fence_rail','fence_post',
              'roof_trim','radio_base','radar_feed','roof_parapet','sensor_panel','door_canopy','gate_strap'}
    for p,n,mat,part in original.faces:
        if part in excluded:continue
        if state=='UnderConstruction' and part in ('crenel','coping','cornice','tower_rail','palisade_tip'):continue
        q=p.copy()
        if state=='UnderConstruction':q[:,2]*=.54
        else:
            # Uneven broken structure, with a gap in the left front curtain.
            center=q.mean(axis=0)
            if part in ('wall','precast_wall','palisade','palisade_tip','palisade_rail','coping') and center[1]<-3 and -3<center[0]<-1.3:continue
            # The same position must receive the same damage displacement;
            # choosing a height per triangle would split shared wall vertices.
            q[:,2]*=.42+.23*(np.tanh(q[:,0]*.8)+1)/2
            mat='charcoal' if mat in ('timber','woodlight','thatch') else 'rubble'
        m.face(q,mat,part)
    if state=='UnderConstruction':
        material='steel' if era_index>=5 else 'timber'
        for x in (-4.03,4.03):
            for y in (-2,0,2):m.box((x,y,1.33),(.09,.09,2.66),material,'scaffold_post')
            for z in (.9,1.9):m.box((x,0,z),(.45,4.5,.09),'woodlight','scaffold_deck')
    else:
        for i,(x,y) in enumerate([(-2.5,-2.7),(-3.4,-2),(-2.8,1.2),(2.9,-2.6),(3.4,.5)]):
            m.box((x,y,.12+(i%2)*.04),(.46,.52,.24),'rubble','debris')
    return m


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    approval=json.loads(APPROVAL.read_text())
    builders=[ancient,classical,medieval,renaissance,industrial,modern,atomic,information]
    atlas=make_atlas(OUT)
    records=[]; all_meshes=[]
    for i,(builder,selection) in enumerate(zip(builders,approval['selections'])):
        base=builder()
        for state,mesh in [('Constructed',base)]+[(s,variant(base,s,i)) for s in ('UnderConstruction','Pillaged')]:
            record=export(mesh,OUT,atlas)
            record.update(era=selection['era'],era_type=selection['eraType'],state=state,concept=selection['concept'],design=selection['name'])
            record['preview']=mesh.name+'-preview.png'
            render(mesh,atlas).save(OUT/record['preview'])
            if state=='Constructed':
                record['reverse_preview']=mesh.name+'-reverse.png'
                render(mesh,atlas,azimuth=180).save(OUT/record['reverse_preview'])
            records.append(record);all_meshes.append(mesh)
        print(selection['era']+': '+selection['name']+' — '+str(len(base.faces))+' triangles',flush=True)
    manifest={'stage':'architectural revision 2 from approved artwork; GR2 conversion and game integration pending',
              'approval_source':str(APPROVAL.relative_to(ROOT)),
              'design_approval':approval.get('meshApproval'),
              'coordinates':'OBJ/BR2: Z up; GLB: Y up; entrance south; ground at Z=0; no terrain plinth',
              'garrison_clearance':'No constructed geometry intersects the center square x,y in [-1,1]. Visual clearance only; unit scale needs game calibration.',
              'texture_stage':'Original generated material library, UV baked per mesh with ray-sampled cavity shading and ground contact shading; native material/SREF calibration pending.',
              'style_reference':'Locally inspected Civ V Fort_MID_DIFF, Fort_MOD_DIFF and Citadel_Anc_DIFF. Stock textures are not included in this source set.',
              'runtime_status':'No changes to the playable mods. Native GR2 files and claimant-era visual switching are not yet implemented.',
              'models':records}
    (OUT/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    make_gallery(OUT,records,approval)
    with zipfile.ZipFile(ROOT/'dist/Outpost-Era-Model-Sources-v1.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,'Outpost-Era-Model-Sources-v1/'+p.relative_to(OUT).as_posix())
    print('Saved 24 mesh states to '+str(OUT))


if __name__=='__main__':main()
