#!/usr/bin/env python3
"""Irrigation-only source meshes for the game's existing Farm/Terrace Farm art.

No replacement fields, terrain, vegetation or native pixels are exported.
The v3 bridge and export code is reused unchanged. Source units are uncalibrated.
"""
from pathlib import Path
import argparse
import base64
import json
import math
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 'irrigation_v3'))
import build_irrigation_meshes as original
from irrigation_mesh_io import Mesh, unit, make_atlas, export, read_glb, render_glb

OUT = ROOT / 'output/models/irrigated-farm-native-overlay'


def curve(controls, steps=5):
    """Interpolating XY spline; Z is separately linear to forbid overshoot."""
    controls = np.asarray(controls, dtype=float)
    if len(controls) < 2 or (np.diff(controls[:, 2]) > 1e-8).any():
        raise ValueError('Water controls must be level or descending')
    result = []
    for i, (b, c) in enumerate(zip(controls, controls[1:])):
        a = controls[max(i - 1, 0)]
        d = controls[min(i + 2, len(controls) - 1)]
        for t in np.linspace(0, 1, steps, endpoint=False):
            p = .5 * ((2*b) + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t)
            p[2] = b[2] * (1-t) + c[2] * t
            result.append(p)
    return np.array(result + [controls[-1]])


def channel(mesh, points, name, width=.30, wet=True, terminal=True,
            upstream=None, gaps=(), stone=False, start_clearance=0.):
    """Low, battered earth banks with a tapered, closed field end.

    Joints have open mouths. Texture furrows remain on the native farm, rather
    than being represented by a dense lattice of additional mesh segments.
    """
    points = np.asarray(points, dtype=float)
    if len(points) < 2 or (np.diff(points[:, 2]) > 1e-8).any():
        raise ValueError('Uphill channel')
    tangent = np.diff(points, axis=0)
    if (np.linalg.norm(tangent[:, :2], axis=1) < 1e-8).any():
        raise ValueError('Vertical/zero-length segment requires a separate drop')
    normals = np.array([unit((-v[1], v[0], 0)) for v in tangent])
    sides = [normals[0]] + [unit(a+b) / max(.65, np.dot(unit(a+b), b)) for a,b in zip(normals, normals[1:])] + [normals[-1]]
    distance = np.r_[0., np.cumsum(np.linalg.norm(tangent[:, :2], axis=1))]
    remaining = distance[-1] - distance
    half = width/2 * (np.clip(remaining/.8, .35, 1.) if terminal else np.ones(len(points)))
    # A narrow, irregular lip casts a legible contact shadow without the v3 rails.
    bank = 'stone' if stone else 'earth'
    profiles = []
    for i, (p, side, w) in enumerate(zip(points, sides, half)):
        shoulder = .105 + .014 * math.sin(i*.61)
        profiles.append([p + side*s + [0,0,z] for s,z in [
            (-w-shoulder,-.11), (-w-.035,.022), (-w,-.052),
            (w,-.052), (w+.035,.022), (w+shoulder,-.11)]])
    for i, (a,b) in enumerate(zip(points, points[1:])):
        pa,pb = profiles[i:i+2]
        for j in range(5):
            side_sign = -1 if j < 2 else 1
            opening = any(np.linalg.norm((a+b)[:2]/2-np.asarray(g)[:2]) < width*1.2 and
                          np.dot(np.asarray(direction), sides[i])*side_sign > 0 for g,direction in gaps)
            if j != 2 and (opening or distance[i] < start_clearance):
                continue
            material = 'soil' if j == 2 else bank
            mesh.face([pa[j],pb[j],pb[j+1],pa[j+1]], material, name+'_bank')
        if wet:
            sa,sb = sides[i:i+2]
            mesh.face([a-sa*half[i],b-sb*half[i+1],b+sb*half[i+1],a+sa*half[i]],
                      'water',name+'_water',[(0,0),(1,0),(1,1),(0,1)])
    if terminal:
        p = points[-1]; side = sides[-1]; along = unit(tangent[-1]); w = half[-1]
        # Water stops inside a closed earth end. No square cut or ornamental pool.
        cap=[p-side*w+[0,0,-.052],p+side*w+[0,0,-.052],
             p+side*(w+.035)+[0,0,.022],p-side*(w+.035)+[0,0,.022]]
        mesh.face(cap,bank,name+'_terminal')
        mesh.face(cap[::-1],bank,name+'_terminal')
        tip = p+along*.20+[0,0,-.105]
        left_toe,left_crest,_,_,right_crest,right_toe=profiles[-1]
        mesh.face([right_crest,left_crest,tip],bank,name+'_terminal')
        mesh.face([left_toe,tip,left_crest],bank,name+'_terminal')
        mesh.face([right_crest,tip,right_toe],bank,name+'_terminal')
    mesh.routes.append({'name':name,'points':points.tolist(),'width':width,'wet':wet,
                        'upstream':upstream,'end':'closed_field_outlet' if terminal else 'open_joint'})


def flat_overlay(stone=False, wet=True):
    mesh = Mesh('RT_IF_Native_Flat_'+('Stone' if stone else 'Earth')+('' if wet else '_Dry'))
    main = curve([(-2.9,3.25,.16),(-2.65,2.2,.158),(-2.45,1.4,.155),
                  (-2.,-.2,.15),(-2.2,-1.6,.145),(-1.45,-3.5,.14)])
    first, second = main[10], main[20]
    branch_a = curve([first,(-.9,1.8,first[2]-.004),(.8,1.4,first[2]-.008),(2.8,1.8,first[2]-.012)])
    branch_b = curve([second,(-.7,-1.55,second[2]-.002),(1.2,-2.3,second[2]-.004),(2.9,-2.15,second[2]-.008)])
    channel(mesh,main,'main',.32,wet,gaps=((first,branch_a[1]-first),(second,branch_b[1]-second)),stone=stone)
    channel(mesh,branch_a,'branch_a',.25,wet,upstream='main',stone=stone,start_clearance=.28)
    channel(mesh,branch_b,'branch_b',.25,wet,upstream='main',stone=stone,start_clearance=.28)
    mesh.meta={'category':'overlay','base_art':'ART_DEF_IMPROVEMENT_FARM','root':'main',
               'variant':'low_stone_banks' if stone else 'earthen_banks','native_fit_verified':False,
               'placement':'layout study; fit channels to native parcel paths before integration'}
    return mesh


def edge_piece(connected, wet=True):
    """Local +X edge component. Opposite neighbors rotate this by 180 degrees."""
    mesh = Mesh('RT_IF_Native_Edge_'+('Open' if connected else 'Closed')+('' if wet else '_Dry'))
    end = original.A if connected else original.A-.95
    pts = curve([(original.A-2.1,0,.14),(end,0,.14)])
    channel(mesh,pts,'edge',.28,wet,terminal=not connected)
    mesh.meta={'category':'edge','connected':connected,'edge_x':original.A,
               'open_socket':[original.A,0,.14] if connected else None,
               'terminal_setback':0 if connected else .95}
    return mesh


def terrace_header(wet=True):
    mesh = Mesh('RT_IF_Native_Terrace_Header'+('' if wet else '_Dry'))
    pts = curve([(-2.,.2,.16),(-1.65,-.65,.158),(-.65,-1.1,.155),(.55,-.95,.15),(1.55,-.45,.145)])
    channel(mesh,pts,'header',.27,wet)
    mesh.meta={'category':'overlay_component','base_art':'ART_DEF_IMPROVEMENT_TERRACE_FARM',
               'native_fit_verified':False,'placement':'one header fitted to a native level bench; do not terrain-warp into an uphill segment'}
    return mesh


def select_edges(neighbors, water_links):
    if not 0 <= neighbors < 64 or not 0 <= water_links < 64 or water_links & ~neighbors:
        raise ValueError('A shared water joint requires an irrigated neighbor')
    # Native farm artwork supplies crop boundaries. Only selected hydraulic
    # routes get a connector; a neighbor alone must not create a dense 6-way web.
    return {str(i):('open_joint' if water_links & (1<<i) else 'closed_field_outlet') for i in range(6)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--quick',action='store_true')
    args=parser.parse_args(); out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    make_atlas(out)
    meshes=[flat_overlay(),flat_overlay(stone=True),flat_overlay(wet=False),
            edge_piece(True),edge_piece(False),edge_piece(True,False),edge_piece(False,False),
            terrace_header(),terrace_header(False)]
    # Keep the actual v3 aqueduct geometry intact, including its straight grade.
    meshes += [m for m in original.parts() if m.name.startswith('RT_IF_Aqueduct_') or m.name=='RT_IF_MountainIntake']
    records=[export(m,out) for m in meshes]
    manifest={'version':1,'status':'unapproved native-farm overlay source study',
              'native_base_policy':'Use installed Farm and Incan Terrace Farm assets; no replacement fields or terrain.',
              'native_game_validation':False,'models':records,
              'native_textures_included':False,'source_units':'normalized; not calibrated to native farm geometry',
              'material_input':'original v3 review atlas, reused only for irrigation surfaces',
              'adjacency_policy':'water_links must be a subset of irrigated neighbors; inactive route ends use Closed'}
    (out/'models.json').write_text(json.dumps(manifest,indent=2)+'\n')
    layouts=[]
    for mask in range(64):
        for water in range(64):
            if not water & ~mask:
                layouts.append({'neighbors':mask,'water_links':water,'ends':select_edges(mask,water)})
    (out/'edge-layouts.json').write_text(json.dumps(layouts,indent=2)+'\n')
    cards=[]
    for rec in records:
        _,(p,n,uv),_=read_glb(out/rec['name']/(rec['name']+'.glb'))
        cards.append({'name':rec['name'],'label':rec['name'].replace('RT_IF_','').replace('_',' '),
                      'category':rec['category'],'triangles':rec['triangles'],'bounds':rec['bounds_z_up'],
                      'groups':rec['groups'],'data':base64.b64encode(np.concatenate((p,n,uv),axis=1).astype('<f4').tobytes()).decode()})
    html=(HERE.parent/'irrigation_v3/irrigation_viewer.html').read_text()
    html=html.replace('__ASSET_DATA__',json.dumps(cards,separators=(',',':')))
    html=html.replace('__ATLAS_DATA__','data:image/png;base64,'+base64.b64encode((out/'RT_IF_Diffuse.png').read_bytes()).decode())
    html=html.replace('Irrigated farm · v3', 'Native farm · irrigation overlays')
    html=html.replace('Connected terrain assembly', 'Irrigation-only source components')
    html=html.replace('Original source meshes', 'Native farm additions · source study')
    (out/'TECHNICAL_NOTES.txt').write_text((HERE/'README.md').read_text())
    (out/'index.html').write_text(html)
    if not args.quick:
        for name in ['RT_IF_Native_Flat_Earth','RT_IF_Native_Flat_Stone','RT_IF_Native_Edge_Closed','RT_IF_Native_Terrace_Header']:
            render_glb(out/name/(name+'.glb'),850,610).save(out/(name+'-preview.png'))
    print(json.dumps({'output':str(out),'models':len(records),'triangles':sum(r['triangles'] for r in records),'neighbor_water_combinations':len(layouts)},indent=2))


if __name__=='__main__':main()
