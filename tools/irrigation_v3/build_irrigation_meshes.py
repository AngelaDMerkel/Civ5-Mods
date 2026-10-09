#!/usr/bin/env python3
"""Build the approved irrigation concept as original modular source meshes.

Run with NumPy and Pillow. No Blender, copied game geometry, or game-file edits.
Coordinates are Z-up, radius-six pointy hexes; native scale is uncalibrated.
"""
from pathlib import Path
import argparse
import base64
import json
import math
import shutil
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from irrigation_mesh_io import Mesh, unit, make_atlas, export, render_glb, read_glb
from refine_geometry import palm, orchard, vegetation, planted_relief, farmstead

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1] if HERE.name=='irrigation_v3' else HERE.parent
OUT=ROOT/'output/models/irrigated-farm-v3' if HERE.name=='irrigation_v3' else ROOT/'rebuilt'
R=6.0; A=math.sqrt(3)*R/2
WATER_WIDTH=.20; WALL_WIDTH=.05; WATER_DEPTH=.055
CROP_GRID=(2.66,2.87)
KINDS={'Flat':(0,0),'GentleHill':(3,.90),'SteepHill':(5,1.65),'RockyFoothill':(4,2.10)}


def polygon(radius,center=(0,0)):
    return np.array([(center[0]+radius*math.cos(math.radians(-30+i*60)),
                      center[1]+radius*math.sin(math.radians(-30+i*60))) for i in range(6)])


HEX=polygon(R)


def clean(poly):
    if len(poly)<3:return []
    result=[]
    for p in poly:
        if not result or np.linalg.norm(p-result[-1])>1e-8:result.append(np.asarray(p))
    if len(result)>1 and np.linalg.norm(result[0]-result[-1])<1e-8:result.pop()
    # Remove collinear vertices, including wraparound, before fan triangulation.
    changed=True
    while changed and len(result)>=3:
        changed=False
        for i in range(len(result)):
            a,b,c=result[i-1],result[i],result[(i+1)%len(result)]
            cross=(b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
            if abs(cross)<1e-8:
                result.pop(i);changed=True;break
    return result if len(result)>=3 else []


def clip(poly,axis,limit,greater):
    output=[]
    if not len(poly):return output
    previous=np.asarray(poly[-1]);pv=(previous[axis]-limit)*(1 if greater else -1)
    for current in poly:
        current=np.asarray(current);cv=(current[axis]-limit)*(1 if greater else -1)
        if (cv>=-1e-10)!=(pv>=-1e-10):
            output.append(previous+(current-previous)*pv/(pv-cv))
        if cv>=-1e-10:output.append(current)
        previous,pv=current,cv
    return output


def patchwork(m, poly, z, origin=(0,0), state='Wet'):
    """Clip a WORLD-aligned parcel grid; neighbors share rows, UV phase and crop."""
    poly=np.asarray(poly,dtype=float);o=np.asarray(origin)+[.37,.61];world=poly+o
    sx,sy=CROP_GRID
    ix0,iy0=np.floor(world.min(axis=0)/[sx,sy]).astype(int)
    ix1,iy1=np.floor(world.max(axis=0)/[sx,sy]).astype(int)
    for ix in range(ix0,ix1+1):
        for iy in range(iy0,iy1+1):
            p=world.copy()
            for axis,limit,greater in [(0,ix*sx,True),(0,(ix+1)*sx,False),(1,iy*sy,True),(1,(iy+1)*sy,False)]:
                p=clip(p,axis,limit,greater)
            p=clean(p)
            if not p:continue
            mat=['barley','vegetables','legumes','barley','vegetables','stubble','legumes','soil'][(ix*7+iy*3)%8]
            if state=='Dry' and mat in ('barley','vegetables','legumes'):mat='dry_crop'
            if state=='Construction':mat='earth'
            if state=='Pillaged':mat='stubble' if (ix+iy)%3 else 'soil'
            uv=(np.asarray(p)-[ix*sx,iy*sy])/[sx,sy]
            local=np.asarray(p)-o
            m.face([(*v,z) for v in local],mat,'crop_surface',uv)
            planted_relief(m,local,z,ix,iy,origin,mat,getattr(m,'lod',0),in_poly)


def cylinder(m,center,radius,height,mat,part,n=6,top=.8):
    x,y,z=center
    low=[(x+radius*math.cos(2*math.pi*i/n),y+radius*math.sin(2*math.pi*i/n),z) for i in range(n)]
    high=[(x+(p[0]-x)*top,y+(p[1]-y)*top,z+height) for p in low]
    m.face(low[::-1],mat,part);m.face(high,mat,part)
    for i in range(n):j=(i+1)%n;m.face([low[i],low[j],high[j],high[i]],mat,part)


def crown(m,x,y,z,r,h,mat,part,n=6):
    ring=[(x+r*math.cos(2*math.pi*i/n),y+r*math.sin(2*math.pi*i/n),z+h*.35) for i in range(n)]
    for i in range(n):
        j=(i+1)%n
        m.face([ring[i],ring[j],(x,y,z+h)],mat,part)
        m.face([ring[j],ring[i],(x,y,z)],mat,part)


def trough(m,points,part='channel',wet=True,width=WATER_WIDTH):
    """Horizontal-width channel loft; the supplied centerline must never rise."""
    points=np.asarray(points,dtype=float)
    if (np.diff(points[:,2])>1e-7).any():raise ValueError(('uphill route',part,points))
    for a,b in zip(points,points[1:]):
        side=unit((-(b-a)[1],(b-a)[0],0))
        # End-to-end rectangular lofts; open ends are intentional snap interfaces.
        for lo,hi,z0,z1,mat,label in [(-width/2,width/2,-WATER_DEPTH-.055,-WATER_DEPTH,'stone','bed'),
             (-width/2-WALL_WIDTH,-width/2,-WATER_DEPTH-.055,.09,'coping','left_rim'),
             (width/2,width/2+WALL_WIDTH,-WATER_DEPTH-.055,.09,'coping','right_rim')]:
            p=[v+side*s+[0,0,z] for v in (a,b) for s,z in [(lo,z0),(hi,z0),(hi,z1),(lo,z1)]]
            # Each run has closed structural end caps; water remains an open plane.
            for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]:
                m.face([p[i] for i in ids],mat,part+'_'+label)
        if wet:
            m.face([a-side*width/2,b-side*width/2,b+side*width/2,a+side*width/2],
                   'water',part+'_water',[(0,0),(1,0),(1,1),(0,1)])
    m.routes.append({'name':part,'points':points.tolist(),'width':width,'wet':wet})


def bridge(m,start,end,ground=lambda x,y:0,wet=True,lod=0,part='aqueduct'):
    """Straight graded waterline; variable piers and true extruded arch openings."""
    a,b=np.asarray(start,dtype=float),np.asarray(end,dtype=float)
    if b[2]>a[2]+1e-8:raise ValueError('Aqueduct would carry water uphill')
    d=b[:2]-a[:2];length=np.linalg.norm(d);u=unit(d);side=np.array((-u[1],u[0]))
    count=max(1,round(length/1.45));step=length/count;thickness=.15
    pier=.2;depth=.39;segments=5 if lod else 8
    def xyz(x,y,z):return [*(a[:2]+u*x+side*y),z]
    def deck(x):return a[2]+(b[2]-a[2])*x/length-WATER_DEPTH-.055
    for i in range(count+1):
        x=i*step;xy=a[:2]+u*x;z=ground(*xy)-.03;h=deck(x)-z
        if h>0:
            q=Mesh('pier');q.box((x,0,z+h/2),(pier,depth,h),'stone',part+'_pier')
            # Convert local X into route direction without rotating vertical coordinates.
            angle=math.degrees(math.atan2(u[1],u[0]));m.append(q,(*a[:2],0),angle)
    for i in range(count):
        left,right=i*step+pier/2,(i+1)*step-pier/2
        mid=(left+right)/2;rad=(right-left)/2
        base=max(ground(*(a[:2]+u*x)) for x in np.linspace(left,right,9))
        available=min(deck(left),deck(right))-base
        if available<.24:
            # The land nearly reaches the deck: a low stone sill, not a fake arch.
            if available>.01:
                q=Mesh('sill');q.box((mid,0,base+available/2),(right-left,depth,available),'stone',part+'_sill')
                m.append(q,(*a[:2],0),math.degrees(math.atan2(u[1],u[0])))
            continue
        rise=min(rad*.88,available-.12);spring=min(deck(left),deck(right))-.12-rise
        # Spandrels run from a sampled arch intrados to the underside of the deck.
        xs=np.linspace(left,right,segments+1)
        for x0,x1 in zip(xs,xs[1:]):
            z0=spring+rise*math.sqrt(max(0,1-((x0-mid)/rad)**2))
            z1=spring+rise*math.sqrt(max(0,1-((x1-mid)/rad)**2))
            for sign in (-1,1):
                p=[xyz(x0,sign*depth/2,z0),xyz(x1,sign*depth/2,z1),
                   xyz(x1,sign*depth/2,deck(x1)),xyz(x0,sign*depth/2,deck(x0))]
                m.face(p if sign<0 else p[::-1],'stone',part+'_spandrel')
            m.face([xyz(x0,-depth/2,z0),xyz(x0,depth/2,z0),xyz(x1,depth/2,z1),xyz(x1,-depth/2,z1)],'stone',part+'_intrados')
            m.face([xyz(x0,-depth/2,deck(x0)),xyz(x1,-depth/2,deck(x1)),xyz(x1,depth/2,deck(x1)),xyz(x0,depth/2,deck(x0))],'stone',part+'_deck')
    trough(m,[a,b],part,wet)


def in_poly(point,poly):
    p=np.asarray(point)
    return all((poly[(i+1)%len(poly),0]-poly[i,0])*(p[1]-poly[i,1])
               -(poly[(i+1)%len(poly),1]-poly[i,1])*(p[0]-poly[i,0])>=-1e-7 for i in range(len(poly)))


def terrace_rings(kind):
    steps,height=KINDS[kind]
    if not steps:return [(HEX,0)]
    # Unequal bench widths and off-center summits break the concentric stamp.
    center=np.array((-.32,.55) if kind=='RockyFoothill' else (.12,.30))
    shapes={'GentleHill':[4.68,3.25,1.54], 'SteepHill':[4.72,3.87,2.98,2.09,1.24], 'RockyFoothill':[4.65,3.53,2.45,1.28]}
    result=[(HEX,0)]
    for i,r in enumerate(shapes[kind],1):
        p=polygon(r)*np.array((.93,1.01))
        p*=np.array([1.00,.94,1.04,1.00,.93,1.02])[:,None]
        p+=center+np.array((-.12*(i-1),.055*(i-1)))
        result.append((p,height*i/steps))
    return result


def surface_height(kind,x,y):
    z=0
    for p,h in terrace_rings(kind):
        if in_poly((x,y),p):z=h
    return z


def inlet(kind):return np.array((0,.42,KINDS[kind][1]+.65))


def wall_segments(a,b):
    """Notch retaining walls at the distribution chute instead of crossing water."""
    d=b-a;cuts=[0.,1.];half=WATER_WIDTH/2+WALL_WIDTH+.035
    for axis,value in [(0,-half),(0,half),(1,.42)]:
        if abs(d[axis])>1e-9:
            t=(value-a[axis])/d[axis]
            if 0<t<1:cuts.append(t)
    cuts=sorted(set(round(t,10) for t in cuts))
    for t0,t1 in zip(cuts,cuts[1:]):
        mid=a+d*(t0+t1)/2
        if mid[1]<.42 and abs(mid[0])<half:continue
        yield a+d*t0,a+d*t1


def tile(kind,state='Wet',lod=0,origin=(0,0),name=None):
    m=Mesh(name or f'RT_IF_{kind}_{state}'+('_LOD1' if lod else ''))
    m.lod=lod
    rings=terrace_rings(kind);wet=state=='Wet'
    for k,(outer,z) in enumerate(rings):
        if k==len(rings)-1:
            patchwork(m,outer,z+.014,origin,state)
        else:
            inner,nextz=rings[k+1]
            for i in range(6):
                j=(i+1)%6
                patchwork(m,[outer[i],outer[j],inner[j],inner[i]],z+.014,origin,state)
                # Outward-facing retaining face, no artificial full-hex pedestal.
                for wa,wb in wall_segments(inner[i],inner[j]):
                    m.face([(*wa,z),(*wb,z),(*wb,nextz),(*wa,nextz)],'stone','retaining_wall')
                    # A thin cap sits entirely inside the planted bench.
                    center=inner.mean(axis=0);ca=(wa-center)*.984+center;cb=(wb-center)*.984+center
                    m.face([(*wa,nextz+.022),(*wb,nextz+.022),(*cb,nextz+.022),(*ca,nextz+.022)],'coping','wall_coping')
    # Highest-bench inlet and a side chute that steps down the terrace faces.
    # Walk the polygon boundaries explicitly, keeping every sample monotone.
    start=inlet(kind);points=[start.tolist(),[0,.12,KINDS[kind][1]+.13]]
    if len(rings)>1:
        x=.0
        for p,z in rings[:0:-1]:
            crossings=[]
            for a,b in zip(p,np.roll(p,-1,axis=0)):
                if (a[0]<=x<=b[0] or b[0]<=x<=a[0]) and abs(b[0]-a[0])>1e-8:
                    crossings.append(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
            y=min(crossings);points.append([x,y+.075,z+.13])
            lower=rings[max(0,next(i for i,r in enumerate(rings) if r[1]==z)-1)][1]
            points.append([x,y-.075,lower+.13])
    points.append([0,-A+.22,.13])
    trough(m,points,'terrace_distribution',wet)
    vegetation(m,kind,state,lod,surface_height,in_poly,HEX)
    # Place the farm store on the wide lowest bench, away from the water route.
    x,y=2.55,-2.80
    if kind!='Flat':x,y=-2.75,-3.30
    z=surface_height(kind,x,y)
    farmstead(m,x,y,z+.02,state)
    if state=='Construction':
        for x,y in [(-1,0),(2,1)]:
            z=surface_height(kind,x,y)
            m.box((x,y,z+.09),(.6,.3,.18),'wood','stored_timbers')
    elif state=='Pillaged':
        for x,y in [(-1.1,-2),(1.4,-3.6)]:
            z=surface_height(kind,x,y)
            m.box((x,y,z+.08),(.32,.28,.16),'stone','repair_rubble')
    m.meta={'category':'tile','terrain':kind,'state':state,'lod':lod,'tile_radius':R,
            'inlet':inlet(kind).tolist(),'ground_edge_z':.014,
            'surface_policy':'terrain-adapted source overlay; native terrain fitting not executed',
            'edge_ports':[{'edge':i,'normal':[math.cos(i*math.pi/3),math.sin(i*math.pi/3)],
                           'xy':[A*math.cos(i*math.pi/3),A*math.sin(i*math.pi/3)],
                           'water_width':WATER_WIDTH,'z':'chosen by shared-edge grade contract'} for i in range(6)]}
    return m


def socket_table():
    rows=[]
    def rot(mask,k):return ((mask<<k)|(mask>>(6-k)))&63 if k else mask
    for mask in range(64):
        canonical=min(rot(mask,k) for k in range(6))
        rotation=next(k for k in range(6) if rot(canonical,k)==mask)
        rows.append({'mask':mask,'canonical_mask':canonical,'rotation_steps':rotation,
                     'edges':[i for i in range(6) if mask&(1<<i)]})
    return {'radius':R,'apothem':A,'edge_order':'E, NE, NW, W, SW, SE; +60-degree steps',
            'water_width':WATER_WIDTH,'wall_width':WALL_WIDTH,'water_depth':WATER_DEPTH,
            'canonical_count':len(set(r['canonical_mask'] for r in rows)),'layouts':rows,
            'note':'Connectivity inventory, not automatic native art. Each used edge must also pass elevation/grade checks.'}


def parts():
    result=[]
    for name,points in [('Straight',[(-1.5,0,.18),(1.5,0,.18)]),
                        ('Bend60',[(-1.5,0,.18),(0,0,.18),(.75,1.299,.18)]),
                        ('Drop',[(-1.4,0,1.1),(0,0,1.1),(.35,0,.2),(1.4,0,.2)])]:
        m=Mesh('RT_IF_Channel_'+name);trough(m,points)
        m.meta={'category':'connector','ports':[points[0],points[-1]]};result.append(m)
    # Open junction at a small triangular chamber, with no hidden cross-wall.
    m=Mesh('RT_IF_Channel_Fork');center=np.array((0,0,.18));r=.34
    chamber=polygon(r)
    m.face([(*p,.18) for p in chamber],'water','junction_water')
    m.face([(*p,.06) for p in chamber],'stone','junction_bed')
    for angle in (0,120,240):
        d=np.array((math.cos(math.radians(angle)),math.sin(math.radians(angle)),0))
        trough(m,[center+d*r*.84,center+d*1.5],'junction_branch')
    for i in (1,3,5):
        a,b=chamber[i],chamber[(i+1)%6];mid=(a+b)/2;delta=b-a
        q=Mesh('bank');q.box((0,0,.145),(np.linalg.norm(delta),WALL_WIDTH,.27),'coping','junction_bank')
        m.append(q,(*mid,0),math.degrees(math.atan2(delta[1],delta[0])))
    m.meta={'category':'connector','ports':[(center+np.array((math.cos(a),math.sin(a),0))*1.5).tolist() for a in (0,2*math.pi/3,4*math.pi/3)]};result.append(m)
    for name,length,height,fall in [('Short',3.4,1.05,.025),('Long',6.0,1.8,.04),('Mountain',4.7,2.6,.11)]:
        for lod in (0,1):
            m=Mesh('RT_IF_Aqueduct_'+name+('_LOD1' if lod else ''))
            p=[(-length/2,0,height),(length/2,0,height-fall)]
            bridge(m,*p,lod=lod)
            m.meta={'category':'connector','lod':lod,'ports':p,'conform_to_terrain':False,'grade':fall/length};result.append(m)
    m=Mesh('RT_IF_MountainIntake')
    for x in (-.27,.27):m.box((x,.02,.41),(.13,.43,.82),'stone','intake_jamb')
    m.box((0,.02,.87),(.7,.5,.14),'coping','intake_lintel')
    m.box((0,.24,.4),(.42,.025,.72),'shadow','spring_opening')
    trough(m,[(0,.16,.26),(0,-.8,.24)],'intake_water')
    m.meta={'category':'source','ports':[[0,-.8,.24]]};result.append(m)
    for m in [palm(),orchard(),palm(1),orchard(1)]:m.meta={'category':'vegetation'};result.append(m)
    return result


def axial(q,r):return np.array((2*A*q+A*r,1.5*R*r))


def scene():
    m=Mesh('RT_IF_ConnectedDistrict')
    layout=[(-1,1,'RockyFoothill'),(0,1,'SteepHill'),(0,0,'GentleHill'),
            (-1,0,'Flat'),(1,0,'Flat'),(0,-1,'Flat')]
    samples=[]
    for q,r,kind in layout:
        xy=axial(q,r);part=tile(kind,origin=xy)
        m.append(part,(*xy,0),prefix=f'tile_{q}_{r}_')
        samples.append({'q':q,'r':r,'kind':kind,'center':xy.tolist(),'inlet':(inlet(kind)+[*xy,0]).tolist()})
    def ground(x,y):
        for entry in samples:
            xy=np.array((x,y))-entry['center']
            if in_poly(xy,HEX):return surface_height(entry['kind'],*xy)
        return 0
    source=np.array((-16.2,13.6,4.65))
    # Original low-poly rock is presentation context only, not a game replacement.
    center=np.array((-18.2,14.0));rng=np.random.default_rng(85)
    ring=np.array([center+np.array((math.cos(i*math.pi/5),math.sin(i*math.pi/5)))*(3.3+rng.uniform(-.5,.5)) for i in range(10)])
    middle=np.array([((p-center)*.60+center+[.15,-.1]).tolist()+[2.3+rng.uniform(-.4,.5)] for p in ring])
    for i in range(10):
        j=(i+1)%10
        m.face([(*ring[i],0),(*ring[j],0),middle[j]],'rock','context_mountain')
        m.face([(*ring[i],0),middle[j],middle[i]],'rock','context_mountain')
        m.face([middle[i],middle[j],(-18.5,14.6,6.3)],'rock','context_mountain')
    # Small spring opening and stone lip embedded on the rock face.
    m.box((source[0]-.1,source[1]+.12,source[2]+.23),(.32,.25,.56),'shadow','context_spring')
    # A directed, monotone tree. Every tile inlet has a path to the single source.
    links=[(-1,0),(0,1),(1,2),(0,3),(2,4),(2,5)]
    graph=[]
    for parent,child in links:
        a=source if parent==-1 else np.array(samples[parent]['inlet'])
        b=np.array(samples[child]['inlet'])
        bridge(m,a,b,ground=ground,part=f'feeder_{parent}_{child}')
        graph.append({'parent':parent,'child':child,'start':a.tolist(),'end':b.tolist()})
    m.meta={'category':'assembly','tiles':samples,'source':source.tolist(),'feeder_graph':graph,
            'context_parts':['context_mountain','context_spring'],'native_status':'source demonstration, not game integration'}
    return m


# Terrain and the water distribution network are jointly authored in v3.
import natural_farms
import sys
natural_farms.bind(sys.modules[__name__])
from natural_farms import tile, surface_height, terrace_rings, inlet, trough, scene

def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true',help='Skip static renders')
    parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();OUT=args.output.resolve()
    OUT.mkdir(parents=True,exist_ok=True);atlas=make_atlas(OUT)
    meshes=[]
    for kind in KINDS:
        for state in ('Wet','Dry','Construction','Pillaged'):meshes.append(tile(kind,state))
        meshes.append(tile(kind,lod=1))
    meshes+=parts();meshes.append(scene())
    records=[]
    for m in meshes:
        record=export(m,OUT);records.append(record)
        print(m.name,len(m.faces),'triangles',flush=True)
    (OUT/'connectors.json').write_text(json.dumps(socket_table(),indent=2)+'\n')
    manifest={'version':3,'source_units':'normalized; tile circumradius 6.0; not engine-calibrated',
              'approved_concept':'irrigated-farm-adjacency-v6.png','model_design_status':'unapproved v3 review','models':records,
              'materials':'original painted alpha atlas; native textures inspected only',
              'native_status':'OBJ/GLB/BR2 source kit; GR2 conversion, engine fitting and dynamic placement pending'}
    (OUT/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Self-contained offline viewer: the binary vertex arrays come from the GLBs.
    cards=[]
    ordered=sorted(records,key=lambda r:(0 if r['category']=='assembly' else 1 if r['name'].endswith('_Wet') else 2,r['name']))
    for rec in ordered:
        _,(p,n,uv),_=read_glb(OUT/rec['name']/(rec['name']+'.glb'))
        data=np.concatenate((p,n,uv),axis=1).astype('<f4').tobytes()
        cards.append({'name':rec['name'],'label':rec['name'].removeprefix('RT_IF_').replace('_',' · '),
                      'category':rec['category'],'triangles':rec['triangles'],
                      'bounds':rec['bounds_z_up'],'groups':rec['groups'],
                      'data':base64.b64encode(data).decode()})
    html=(HERE/'irrigation_viewer.html').read_text()
    html=html.replace('__ASSET_DATA__',json.dumps(cards,separators=(',',':')))
    html=html.replace('__ATLAS_DATA__','data:image/png;base64,'+base64.b64encode((OUT/'RT_IF_Diffuse.png').read_bytes()).decode())
    (OUT/'index.html').write_text(html)
    shutil.copy2(HERE/'irrigation_mesh_notes.txt',OUT/'TECHNICAL_NOTES.txt')
    if not args.quick:
        for kind in KINDS:
            name=f'RT_IF_{kind}_Wet'
            render_glb(OUT/name/(name+'.glb'),900,680).save(OUT/(name+'-preview.png'))
        name='RT_IF_ConnectedDistrict'
        render_glb(OUT/name/(name+'.glb'),1600,1120,azimuth=-74,elevation=47).save(OUT/'connected-district-preview.png')
        render_glb(OUT/name/(name+'.glb'),1600,1120,azimuth=-74,elevation=47,wire=True).save(OUT/'connected-district-wireframe.png')
        sheet=Image.new('RGB',(1800,1470),(232,226,210));d=ImageDraw.Draw(sheet)
        try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',25)
        except OSError:font=ImageFont.load_default()
        for i,kind in enumerate(KINDS):
            x=(i%2)*900;y=(i//2)*735;name=f'RT_IF_{kind}_Wet'
            sheet.paste(Image.open(OUT/(name+'-preview.png')),(x,y+45))
            rec=next(r for r in records if r['name']==name)
            d.text((x+24,y+10),f'{kind}  /  {rec["triangles"]:,} triangles',font=font,fill=(55,61,45))
        sheet.save(OUT/'tile-kit-preview.png')
    source=OUT/'source';source.mkdir(exist_ok=True)
    for filename in ('build_irrigation_meshes.py','irrigation_mesh_io.py','irrigation_viewer.html','validate_irrigation_meshes.py','irrigation_mesh_notes.txt','refine_geometry.py','refine_materials.py','natural_farms.py','painted_atlas.png','texture-prompt.txt','render_flow_review.py'):
        path=HERE/filename
        if path.exists():shutil.copy2(path,source/filename)
    from refine_materials import SOURCE_ATLAS,SOURCE_PROMPT
    shutil.copy2(SOURCE_ATLAS,source/'painted_atlas.png')
    shutil.copy2(SOURCE_PROMPT,source/'texture-prompt.txt')
    provenance=SOURCE_ATLAS.with_name('provenance.json')
    if provenance.exists():
        shutil.copy2(provenance,OUT/'provenance.json')
        shutil.copy2(provenance,source/'provenance.json')
    print('Exports complete:',OUT)


if __name__=='__main__':main()
