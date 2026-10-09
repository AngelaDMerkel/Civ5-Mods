#!/usr/bin/env python3
"""Author the first low-poly map-model sources, with no game asset dependency.

Outputs editable OBJ/MTL, portable GLB and a rigid-root Nexus Buddy BR2 transfer
mesh. GR2 conversion/material binding and engine scale checks remain external.
BR2 layout reference: Deliverator's Civilization-Blender-Scripts/io_export_br2.py.
These source assets never enter the playable mod until that conversion is done.
"""
from pathlib import Path
import json
import math
import struct
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/models/first-pass'
COLORS = {
    'sandstone': (190, 161, 113), 'limestone': (233, 212, 167),
    'terracotta': (174, 82, 49), 'roof': (133, 67, 42),
    'timber': (101, 72, 45), 'shadow': (47, 48, 40),
    'water': (49, 132, 143), 'awning': (202, 145, 60),
    'grey_stone': (144, 146, 133), 'iron': (65, 76, 77),
    'soil': (141, 119, 84), 'charred': (79, 69, 58),
    'rubble': (152, 128, 91), 'banner': (133, 50, 37),
    'grain': (206, 185, 121), 'plaster': (214, 188, 136),
}
NAMES = list(COLORS)


def norm(v):
    a = np.array(v, dtype=float)
    return a / np.linalg.norm(a)


class Mesh:
    def __init__(self, name):
        self.name, self.faces = name, []

    def face(self, vertices, material, part='structure'):
        # All procedural primitives supply outward-facing winding.
        for i in range(1, len(vertices) - 1):
            p = np.array([vertices[0], vertices[i], vertices[i+1]], dtype=float)
            n = np.cross(p[1]-p[0], p[2]-p[0])
            assert np.linalg.norm(n) > 1e-9, (part, p)
            self.faces.append((p, norm(n), material, part))

    def box(self, center, size, material, part='structure'):
        cx, cy, cz = center; x, y, z = np.array(size)/2
        p = [(cx+dx*x, cy+dy*y, cz+dz*z) for dx,dy,dz in
             [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.face([p[i] for i in ids], material, part)

    def ring(self, center, outer, inner, height, material, segments=16, part='well'):
        x,y,z = center
        for i in range(segments):
            a,b = 2*math.pi*i/segments, 2*math.pi*(i+1)/segments
            p = [(x+r*math.cos(t), y+r*math.sin(t), z+h) for h in (0,height)
                 for r,t in [(outer,a),(outer,b),(inner,b),(inner,a)]]
            for ids in [(0,1,5,4),(3,7,6,2),(4,5,6,7),(0,3,2,1),(0,4,7,3),(1,2,6,5)]:
                self.face([p[j] for j in ids],material,part)

    def arch(self, x,y,spring,radius,thickness,depth,material,segments=12):
        # Real arch opening, including front/back stone faces and intrados.
        for i in range(segments):
            a,b = math.pi*i/segments, math.pi*(i+1)/segments
            p=[(x+r*math.cos(t), yy, spring+r*math.sin(t)) for yy in (y-depth/2,y+depth/2)
               for r,t in [(radius,a),(radius+thickness,a),(radius+thickness,b),(radius,b)]]
            for ids in [(0,1,2,3),(7,6,5,4),(1,5,6,2),(0,3,7,4),(0,4,5,1),(3,2,6,7)]:
                self.face([p[j] for j in ids],material,'gateway_arch')
        for sign in (-1,1):
            self.box((x+sign*(radius+thickness/2),y,spring/2),(thickness,depth,spring),material,'gate_pier')

    def beam(self,a,b,width,material,part='beam'):
        a,b=np.array(a),np.array(b); tangent=norm(b-a)
        side=norm(np.cross(tangent,(0,0,1) if abs(tangent[2])<.9 else (1,0,0)))*width/2
        up=norm(np.cross(tangent,side))*width/2
        p=[q+s*side+t*up for q in (a,b) for s,t in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.face([p[j] for j in ids],material,part)

    def roof(self,x,y,z,w,d,rise,material='roof'):
        p=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),
           (x,y-d/2,z+rise),(x,y+d/2,z+rise)]
        for ids in [(0,1,4),(3,5,2),(0,4,5,3),(4,1,2,5),(0,3,2,1)]:
            self.face([p[j] for j in ids],material,'roof')


def well(m,x,y):
    m.ring((x,y,.12),.64,.46,.62,'limestone')
    m.box((x,y,.25),(.88,.88,.06),'water','well_water')
    for dx in (-.83,.83):
        m.box((x+dx,y,1.02),(.13,.13,1.8),'timber','well_post')
    m.roof(x,y,1.92,2.05,1.45,.46,'awning')


def caravansary():
    m=Mesh('RT_Caravansary')
    m.box((0,0,.04),(9,9,.08),'soil','foundation')
    for x in (-3.65,3.65):
        m.box((x,.1,1.14),(1.55,7.6,2.2),'sandstone','lodgings')
        m.roof(x,.1,2.24,1.85,7.9,.5)
        for y in (-2.5,-.5,1.5,3.2):
            m.box((x+(.79 if x<0 else -.79),y,.91),(.04,.55,1.55),'shadow','stable_door')
    m.box((0,3.72,1.2),(5.8,1.3,2.3),'plaster','storehouse')
    m.box((0,3.72,2.45),(6.1,1.6,.22),'terracotta','cornice')
    m.arch(0,-3.7,2.35,1.15,.43,1.1,'limestone')
    for x in (-2.24,2.24):
        m.box((x,-3.7,2),(1.37,1.16,3.9),'sandstone','gateway_wing')
        m.box((x,-4.31,2),(.23,.13,3.9),'limestone','pilaster')
    m.box((0,-3.7,4.13),(5.85,1.48,.42),'limestone','entablature')
    m.box((0,-3.7,4.4),(6.12,1.65,.17),'terracotta','coping')
    well(m,-1.35,.4)
    m.box((1.75,2.25,.5),(.85,.7,.85),'timber','crate')
    m.box((2.15,1.2,.35),(.7,.55,.55),'grain','supply_bale')
    return m


def ministry():
    m=Mesh('RT_MinistryOfCoin')
    for i in range(3):
        m.box((0,-.15,.12+i*.15),(7.9-i*.55,6.7-i*.35,.15),'limestone','terrace')
    m.box((.55,1,3.25),(5,4.1,5.6),'terracotta','counting_house')
    m.box((.55,1,6.09),(5.4,4.5,.24),'limestone','upper_cornice')
    m.box((.55,1,6.25),(4.85,3.95,.12),'sandstone','flat_roof')
    m.box((-1.75,-1.0,2.3),(3.6,2.8,3.7),'terracotta','front_office')
    m.box((-1.75,-1,4.23),(4,3.2,.25),'limestone','lower_cornice')
    m.box((1.55,-1.72,1.9),(2.4,1.6,2.9),'limestone','entrance')
    m.box((1.55,-2.535,1.64),(1.32,.05,2.45),'shadow','door')
    m.box((1.55,-1.72,3.47),(2.75,1.85,.24),'limestone','portal_lintel')
    for i in range(4):
        m.box((1.55,-3.35+i*.21,.18+i*.11),(2.45,.48,.22),'limestone','stairs')
    for x in (-.95,.55,2.05):
        m.box((x,-1.07,4.95),(.32,.045,.94),'shadow','upper_window')
    for y in (0,1.4,2.5):
        m.box((3.07,y,4.95),(.045,.32,.94),'shadow','side_window')
    for x in (-2.75,-1.4):
        m.box((x,-2.425,3.26),(.32,.045,.74),'shadow','office_window')
    m.face([(-3.52,-2.42,2.88),(-.07,-2.42,2.88),(-.07,-3.42,2.28),(-3.52,-3.42,2.28)],'awning','market_awning')
    m.face([(-3.52,-3.42,2.28),(-.07,-3.42,2.28),(-.07,-2.42,2.88),(-3.52,-2.42,2.88)],'awning','awning_underside')
    for x in (-3.35,-.22):
        m.box((x,-3.3,1.38),(.14,.14,1.9),'timber','awning_post')
    return m


def outpost():
    m=Mesh('RO_ResourceOutpost')
    m.box((0,0,.04),(8.6,8.6,.08),'soil','foundation')
    for x in (-3.4,3.4): m.box((x,0,1.15),(.55,6.8,2.2),'grey_stone','curtain_wall')
    m.box((0,3.4,1.15),(6.8,.55,2.2),'grey_stone','curtain_wall')
    for x in (-2.35,2.35): m.box((x,-3.4,1.15),(2.1,.55,2.2),'grey_stone','gate_wall')
    m.arch(0,-3.4,1.55,.9,.3,.65,'limestone',8)
    for x in (-3.4,3.4):
        for y in (-3.4,3.4):
            m.box((x,y,1.55),(1.5,1.5,3),'grey_stone','watchtower')
            m.box((x,y,3.03),(1.7,1.7,.2),'limestone','tower_cap')
            for dx,dy in [(-.65,-.65),(.65,-.65),(.65,.65),(-.65,.65)]:
                m.box((x+dx,y+dy,3.35),(.36,.36,.55),'grey_stone','crenel')
    for x in (-2,-.7,.7,2):
        m.box((x,3.4,2.47),(.54,.6,.48),'grey_stone','crenel')
    m.box((-1.05,1.5,.92),(2.7,1.95,1.7),'timber','storehouse')
    m.roof(-1.05,1.5,1.8,2.95,2.2,.68)
    m.box((1.7,.6,.62),(1.1,1.1,1.12),'timber','crate')
    m.box((1.3,-.95,.39),(1.5,.8,.66),'iron','resource_store')
    m.box((-.9,-1.3,2),(.12,.12,3.9),'timber','flagpole')
    m.box((-.29,-1.3,3.48),(1.2,.04,.65),'banner','banner')
    return m


def irrigation():
    m=Mesh('RT_IrrigationWorks')
    m.box((0,0,.04),(8.7,7.7,.08),'soil','foundation')
    # Open reservoir and branching stone channels, with opaque water surfaces.
    for x in (-2.2,2.2): m.box((x,-1,.58),(.3,4.1,1),'limestone','basin_wall')
    for y in (-3.05,1.05): m.box((0,y,.58),(4.7,.3,1),'limestone','basin_wall')
    m.box((0,-1,.6),(4.1,3.8,.04),'water','reservoir')
    for x in (-.6,.6): m.box((x,2.4,1.45),(.23,2.6,.8),'limestone','feeder_channel')
    m.box((0,2.4,1.2),(1.0,2.6,.07),'water','channel_water')
    for y in (1.75,3.1):
        for x in (-.48,.48): m.box((x,y,.7),(.32,.43,1.3),'sandstone','channel_pier')
    for x in (-.8,.8): m.box((x,.95,1.25),(.25,.3,2.35),'timber','sluice_frame')
    m.box((0,.95,2.48),(1.95,.42,.23),'timber','sluice_header')
    m.box((0,.95,1.3),(1.2,.2,1.6),'timber','sluice_gate')
    m.box((0,.95,2.63),(.15,.15,.55),'iron','gate_screw')
    m.box((-3,1.55,1.2),(1.7,2.9,2.2),'plaster','keeper_house')
    m.box((-3,1.55,2.4),(1.95,3.15,.22),'terracotta','flat_roof')
    m.box((-3,.08,.94),(.66,.05,1.5),'shadow','door')
    # Small outlet toward surrounding farms; no change to water gameplay rules.
    for x in (-.54,.54): m.box((x,-3.58,.37),(.22,1.1,.45),'limestone','outlet')
    m.box((0,-3.58,.28),(.86,1.1,.03),'water','outlet_water')
    return m


def variant(original, state):
    m=Mesh(original.name+'_'+state)
    for p,n,mat,part in original.faces:
        if state == 'UnderConstruction':
            if part in ('roof','banner','well_water','water') or 'cornice' in part or 'coping' in part: continue
            q=p.copy(); q[:,2]*=.48
        else:
            if part in ('roof','banner','awning','market_awning','awning_underside','well_water','crenel'): continue
            q=p.copy(); q[:,2]*=.63
            mat='charred' if mat in ('timber','awning','banner') else ('rubble' if mat not in ('soil','shadow') else mat)
        m.face(q,mat,part)
    if state == 'UnderConstruction':
        for x in (-4,4):
            for y in (-3,0,3): m.box((x,y,1.75),(.12,.12,3.5),'timber','scaffold_post')
            for z in (1.15,2.5): m.box((x,0,z),(.48,6.8,.15),'timber','scaffold_deck')
    else:
        for i in range(8):
            x=-2.9+(i%4)*1.75; y=-2.1+(i//4)*2.6
            m.box((x,y,.22),(.7,.56,.37),'rubble','debris')
    return m


def face_uv(material):
    index=NAMES.index(material); x,y=index%4,index//4
    # Interior of a solid-color cell, leaving generous filtering/mipmap gutters.
    return [(x/4+.04,1-(y/4+.04)),(x/4+.21,1-(y/4+.04)),(x/4+.04,1-(y/4+.21))]


def export(mesh):
    folder=OUT/mesh.name; folder.mkdir(parents=True,exist_ok=True)
    obj=['# Original source mesh; Z up. Units require calibration in Civ V.', 'mtllib '+mesh.name+'.mtl']
    positions=[]; normals=[]; uvs=[]; last=None
    for p,n,mat,part in mesh.faces:
        start=len(positions)+1
        uv=face_uv(mat)
        for v,t in zip(p,uv):
            positions.append(v.tolist()); normals.append(n.tolist()); uvs.append(t)
            obj.extend(['v '+' '.join(f'{f:.6f}' for f in v), 'vt '+' '.join(f'{f:.6f}' for f in t),
                        'vn '+' '.join(f'{f:.6f}' for f in n)])
        if last != part: obj.append('g '+part); last=part
        obj.append('usemtl RT_Palette')
        obj.append('f '+' '.join(f'{i}/{i}/{i}' for i in range(start,start+3)))
    (folder/(mesh.name+'.obj')).write_text('\n'.join(obj)+'\n')
    (folder/(mesh.name+'.mtl')).write_text('newmtl RT_Palette\nKa 0.15 0.15 0.15\nKd 1 1 1\nKs 0 0 0\nNs 1\nd 1\nillum 1\nmap_Kd ../RT_MapPalette.png\n')
    # One rigid world bone. Every vertex has a complete 255/255 weight.
    br=['// Rigid static mesh authored by Realistic Terrain; conversion unverified',
        'skeleton', '0 "World" -1 0 0 0 0 0 0 1 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1',
        'meshes:1', 'mesh:"'+mesh.name+'"', 'vertices']
    for i,(pos,n,uv) in enumerate(zip(positions,normals,uvs)):
        p=mesh.faces[i//3][0]
        tangent=norm(p[1]-p[0]); bitangent=-norm(np.cross(n,tangent))
        fields=list(pos)+list(n)+[uv[0],1-uv[1]]+[0,0,0,0,255,0,0,0]+list(tangent)+list(bitangent)
        br.append(' '.join(str(int(v)) if 8<=j<16 else f'{v:.8f}' for j,v in enumerate(fields)))
    br.append('triangles'); br.extend(f'{i} {i+1} {i+2}' for i in range(0,len(positions),3)); br.append('end')
    (folder/(mesh.name+'.br2')).write_text('\n'.join(br)+'\n')
    # GLB 2.0 includes the preview texture and converts Z-up to glTF Y-up.
    blob=bytearray(); views=[]; accessors=[]
    def add(data):
        while len(blob)%4: blob.append(0)
        offset=len(blob); blob.extend(data); views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data)})
        return len(views)-1
    def accessor(values,typ):
        data=np.asarray(values,dtype='<f4'); view=add(data.tobytes())
        a={'bufferView':view,'componentType':5126,'count':len(values),'type':typ}
        if typ=='VEC3': a.update(min=data.min(axis=0).tolist(),max=data.max(axis=0).tolist())
        accessors.append(a); return len(accessors)-1
    posidx=accessor(positions,'VEC3'); normidx=accessor(normals,'VEC3')
    uvidx=accessor([(u,1-v) for u,v in uvs],'VEC2')
    imageview=add((OUT/'RT_MapPalette.png').read_bytes())
    gltf={'asset':{'version':'2.0','generator':'Realistic Terrain source-model builder'},
          'buffers':[{'byteLength':len(blob)}], 'bufferViews':views,'accessors':accessors,
          'images':[{'bufferView':imageview,'mimeType':'image/png'}],
          'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],
          'textures':[{'source':0,'sampler':0}],
          'materials':[{'name':'RT_Palette','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1}}],
          'meshes':[{'name':mesh.name,'primitives':[{'attributes':{'POSITION':posidx,'NORMAL':normidx,'TEXCOORD_0':uvidx},'material':0}]}],
          'nodes':[{'mesh':0,'rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)]}], 'scenes':[{'nodes':[0]}],'scene':0}
    js=json.dumps(gltf,separators=(',',':')).encode(); js+=b' '*((-len(js))%4); blob+=b'\0'*((-len(blob))%4)
    glb=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob
    (folder/(mesh.name+'.glb')).write_bytes(glb)
    bbox=np.array(positions)
    return {'name':mesh.name,'triangles':len(mesh.faces),'vertices':len(positions),
            'bounds_z_up':[bbox.min(axis=0).tolist(),bbox.max(axis=0).tolist()],
            'files':[mesh.name+'/'+mesh.name+suffix for suffix in ('.obj','.mtl','.br2','.glb')],
            'gr2_status':'not converted; Nexus Buddy import, material binding and scale validation pending'}


def render(mesh, width=720, height=570, azimuth=-52):
    # Deterministic orthographic source-mesh render, not a simulated game image.
    ss=2
    pixels=np.full((height*ss,width*ss,3),(26,35,42),dtype=np.uint8)
    depth=np.full((height*ss,width*ss),-np.inf)
    a=math.radians(azimuth); e=math.radians(31)
    camera=norm((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))
    right=norm(np.cross((0,0,1),camera)); up=norm(np.cross(camera,right))
    allp=np.vstack([p for p,_,_,_ in mesh.faces]); center=(allp.min(axis=0)+allp.max(axis=0))/2
    projected=np.array([((p-center)@right,(p-center)@up) for p in allp]); span=projected.max(axis=0)-projected.min(axis=0)
    scale=min((width-70)/span[0],(height-75)/span[1])*ss
    sun=norm((-.4,-.65,1))
    for p,n,mat,part in mesh.faces:
        if n@camera < 0: continue
        coords=np.array([(width*ss/2+(v-center)@right*scale,height*ss/2-(v-center)@up*scale) for v in p])
        lo=np.maximum(np.floor(coords.min(axis=0)).astype(int),(0,0))
        hi=np.minimum(np.ceil(coords.max(axis=0)).astype(int),(width*ss-1,height*ss-1))
        if np.any(hi<lo): continue
        x0,y0=coords[0]; x1,y1=coords[1]; x2,y2=coords[2]
        denominator=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(denominator)<1e-8: continue
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]; xx=xx+.5; yy=yy+.5
        w0=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/denominator
        w1=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/denominator
        w2=1-w0-w1; z=p@camera
        triangle_depth=w0*z[0]+w1*z[1]+w2*z[2]
        region=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        visible=(w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)&(triangle_depth>region)
        light=.59+.41*max(0,n@sun)
        color=tuple(round(c*light) for c in COLORS[mat])
        region[visible]=triangle_depth[visible]
        pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][visible]=color
    return Image.fromarray(pixels).resize((width,height),Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    palette=Image.new('RGBA',(256,256)); d=ImageDraw.Draw(palette)
    for i,color in enumerate(COLORS.values()):
        x,y=(i%4)*64,(i//4)*64; d.rectangle((x,y,x+63,y+63),fill=color+(255,))
    palette.save(OUT/'RT_MapPalette.png'); palette.save(OUT/'RT_MapPalette.dds')
    Image.new('RGBA',(4,4),(128,128,255,255)).save(OUT/'RT_MapFlatNormal.dds')
    Image.new('RGBA',(4,4),(0,0,0,255)).save(OUT/'RT_MapBlackSpec.dds')
    base=[caravansary(),ministry(),outpost(),irrigation()]
    meshes=base+[variant(m,state) for m in (base[0],base[2]) for state in ('UnderConstruction','Pillaged')]
    records=[export(m) for m in meshes]
    for m in meshes: render(m).save(OUT/(m.name+'-preview.png'))
    sheet=Image.new('RGB',(1440,1300),(26,35,42)); draw=ImageDraw.Draw(sheet)
    try: font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',25)
    except OSError: font=ImageFont.load_default()
    labels=['Caravansary - gateway','Ministry of Coin - counting house','Resource Outpost - fortified stores','Irrigation Works - sluice and basin']
    for i,(m,label) in enumerate(zip(base,labels)):
        x=(i%2)*720; y=(i//2)*650
        sheet.paste(render(m),(x,y+50))
        draw.text((x+30,y+18),label,font=font,fill='#e5d5ae')
        draw.text((x+30,y+610),f'{len(m.faces)} triangles | source mesh preview',font=font,fill='#aabbc5')
    sheet.save(OUT/'four-structures-preview.png')
    manifest={'stage':'source models; not installed in Civ V', 'coordinates':'OBJ/BR2: Z-up; GLB: Y-up; centered footprint, foundation at Z=0',
              'materials':'Original solid-color palette, UV mapped; final surface texturing/engine shader calibration pending',
              'format_reference':'https://github.com/deliverator23/Civilization-Blender-Scripts/blob/master/Blender-2.7-Addons/io_export_br2.py',
              'models':records}
    (OUT/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(ROOT/'dist/Map-Model-Sources-v1.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(OUT.rglob('*')):
            if file.is_file(): archive.write(file,'Map-Model-Sources-v1/'+file.relative_to(OUT).as_posix())
    print(json.dumps([{'model':r['name'],'triangles':r['triangles']} for r in records],indent=2))


if __name__=='__main__': main()
