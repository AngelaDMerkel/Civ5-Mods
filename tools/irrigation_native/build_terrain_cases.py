#!/usr/bin/env python3
"""Native-art irrigation review: readable canals, terrain families and junctions."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import numpy as np
from native_fpk import Archive
from native_gr2 import Reader
from build_regular_farms import constructed
from native_scene import parts, diffuse, write_glb, review_glb
from gr2_writer import Writer
from import_native_farms import OUT
from build_native_fit import Surface, subdivide, overlay_graph
from build_overlays import Mesh, channel, curve, original, unit, export
from terrain_scene import ground, crops, translated, floodplain, hill_height, rock_height, load_rock_height, ROCK_CENTER
from irrigation_mesh_io import render_glb


DESCRIPTIONS = {
 'terrace': ('Terraced hill', 'Wider carrier on native wall caps; enlarged aqueduct. Native farm mesh and UVs retained.'),
 'flat_desert': ('Flat desert', 'Neighbor-fed carrier with one branch between authored parcels using actual Civ V crop decals.'),
 'flat_grassland': ('Flat grassland', 'The same irrigation component on native grassland material; identical inlet elevation.'),
 'floodplain': ('River-fed floodplain', 'A river intake feeding the farm at river level, with native floodplain bank vegetation.'),
 'terrace_flat': ('Terrace → flat desert', 'A lined descent over native terrace steps meets a lower flat channel at a shared port.'),
 'floodplain_desert': ('Floodplain → desert', 'One continuous carrier crosses a same-level tile boundary; branches end inside the fields.'),
 'mountain_terrace': ('Mountain → terrace', 'A rock-face intake supplies an aqueduct at falling grade, joining the native terrace carrier.')}


def pipe(mesh, points, name, width, wet, terminal=True, upstream=None, stone=False,
         relief=3., gaps=(), start_clearance=0., widths=None):
    channel(mesh, points, name, width=width, wet=wet, terminal=terminal,
            upstream=upstream, stone=stone, profile_scale=relief,
            gaps=gaps, start_clearance=start_clearance, widths=widths,
            bank_scale=3.5, bank_material='coping')


def aqueduct(mesh, start, end, surface, wet, name, upstream=None, scale=4.5):
    q = Mesh('bridge')
    original.bridge(q, np.array(start)/scale, np.array(end)/scale,
                    ground=lambda x,y: surface(x*scale, y*scale)/scale,
                    wet=wet, part=name)
    for p,n,uv,mat,part in q.faces:
        mesh.faces.append((p*scale,n,uv,mat,part))
    mesh.routes += [dict(r, points=(np.array(r['points'])*scale).tolist(),
                        width=r['width']*scale, upstream=upstream, end='open_joint') for r in q.routes]


def terrace(surface, wet, terminal=True):
    mesh = Mesh('terrace')
    header = subdivide([(3.7,11.56,15.10),(-5.82,11.56,15.085),
                        (-12.61,6.73,15.07),(-14.03,3.52,15.055)])
    pipe(mesh, header, 'terrace_header', .90, wet, terminal, 'terrace_supply', True, 4.2)
    aqueduct(mesh, (10.25,23.3,15.28), header[0], surface.height, wet, 'terrace_supply')
    return mesh


def flat(wet, inlet=.38, outlet=.30, connected=False, river=False):
    mesh = Mesh('flat'); drop = inlet-outlet
    controls = [(29.2 if river else 30.,5,inlet),(18,5,inlet-drop*.25),
                (5,6,inlet-drop*.5),(-5,4,inlet-drop*.7),(-18,5,inlet-drop*.9),
                (-30 if connected else -26,5 if connected else 4.5,outlet)]
    main = curve(controls, steps=5); join = main[10]
    branch = curve([join,(4,-3,join[2]-.01),(0,-12,join[2]-.025),(1,-23,join[2]-.035)])
    pipe(mesh, main, 'flat_carrier', 1.15, wet, not connected, gaps=((join,branch[1]-join),))
    pipe(mesh, branch, 'flat_branch', .82, wet, upstream='flat_carrier', start_clearance=.65)
    return mesh


def route(mesh, name):
    return next(r for r in mesh.routes if r['name']==name)


def flat_context(props, center=(0,0), grass=False):
    return [ground('authored_flat_ground', lambda x,y:0.,
                   'afri_grassland_d.dds' if grass else 'afri_desert_d.dds', center, subdivisions=1)] + crops(center) + translated(props, (center[0]-10,center[1]-10,0), 'native_flat_')


def compose(key, native, props, wet=True):
    native_surface = Surface(native)
    hill = lambda x,y: hill_height(native_surface,x,y)
    terrace_context = native+[ground('authored_hill_under_native_farm',hill)]
    external = []; seams = []
    if key=='terrace':
        mesh=terrace(native_surface,wet); context=terrace_context
        external=[{'route':'terrace_supply','kind':'higher_neighbor_or_mountain_socket'}]
    elif key in ('flat_desert','flat_grassland'):
        mesh=flat(wet); context=flat_context(props,grass=key=='flat_grassland')
        external=[{'route':'flat_carrier','kind':'irrigated_neighbor_socket'}]
    elif key=='floodplain':
        mesh=flat(wet,.44,.36,river=True);context=flat_context(props)+floodplain()
        external=[{'route':'flat_carrier','kind':'visible_river','height':.44}]
    elif key=='floodplain_desert':
        mesh=flat(wet,.44,.36,connected=True,river=True)
        second=flat(wet,.36,.28);mesh.append(second,(-60,0,0),prefix='desert_')
        route(mesh,'desert_flat_carrier')['upstream']='flat_carrier'
        context=flat_context(props)+floodplain()+flat_context(props,(-60,0))
        seams=[{'from':'flat_carrier','to':'desert_flat_carrier','point':[-30,5,.36]}]
        external=[{'route':'flat_carrier','kind':'visible_river','height':.44}]
    elif key=='terrace_flat':
        mesh=terrace(native_surface,wet,terminal=False)
        start=np.array(route(mesh,'terrace_header')['points'][-1]); finish=np.array([-30.,5.,.38])
        context=terrace_context+flat_context(props,(-60,0))
        surf=Surface(context)
        xy=np.linspace(start[:2],finish[:2],110)
        direction=xy[-1]-xy[0]; side=unit((-direction[1],direction[0],0))[:2]
        heights=np.array([max(surf.height(*(p+side*v)) for v in (-.575,0,.575)) for p in xy])
        safe=np.maximum.accumulate(heights[::-1])[::-1]+.38
        # Delay each drop until after clearing its measured riser. This keeps
        # interpolation from cutting diagonally through the uphill retaining wall.
        z=np.r_[start[2],safe[:-1]]; z=np.minimum.accumulate(z)
        if np.any(z < heights+.30):raise ValueError('Native descending route lacks head/clearance')
        z[-1]=finish[2]
        descent=np.column_stack((xy,z))
        pipe(mesh,descent,'terrace_descent',1.15,wet,False,'terrace_header',True,3.,
             widths=np.linspace(.90,1.15,len(descent)))
        receiver=flat(wet,.38,.30);mesh.append(receiver,(-60,0,0),prefix='lower_')
        route(mesh,'lower_flat_carrier')['upstream']='terrace_descent'
        seams=[{'from':'terrace_descent','to':'lower_flat_carrier','point':finish.tolist()}]
        external=[{'route':'terrace_supply','kind':'higher_neighbor_or_mountain_socket'}]
    elif key=='mountain_terrace':
        mesh=terrace(native_surface,wet)
        rock=ground('authored_rocky_source_terrain',rock_height,'afri_mountain_base_d.dds',center=ROCK_CENTER,subdivisions=20)
        context=terrace_context+[rock]; surface=Surface(context)
        finish=np.array(route(mesh,'terrace_supply')['points'][0])
        candidates=np.linspace(ROCK_CENTER,finish[:2],240)
        xy=next(p for p in candidates if surface.height(*p)<finish[2]-.60)
        start=np.array([*xy,surface.height(*xy)+.90])
        if start[2]<finish[2]:raise ValueError('Mountain source is too low')
        aqueduct(mesh,start,finish,surface.height,wet,'mountain_span','mountain_intake_water')
        route(mesh,'terrace_supply')['upstream']='mountain_span'
        raw=next(p for p in original.parts() if p.name=='RT_IF_MountainIntake')
        scale=4.5; angle=math.atan2(*(finish-start)[:2][::-1])+math.pi/2
        rot=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
        offset=start-rot@(np.array([0,-.8,.24])*scale)
        for p,n,uv,mat,part in raw.faces:
            if not wet and part.endswith('_water'):continue
            mesh.faces.append((p*scale@rot.T+offset,n@rot.T,uv,mat,'mountain_'+part))
        for r in raw.routes:
            mesh.routes.append(dict(r,name='mountain_'+r['name'],points=(np.array(r['points'])*scale@rot.T+offset).tolist(),width=r['width']*scale,wet=wet,upstream=None,end='open_joint'))
        external=[{'route':'mountain_intake_water','kind':'visible_rock_face_intake'}]
    else:raise ValueError(key)
    mesh.name='RT_IF_'+key.title().replace('_','')+('' if wet else '_Dry')
    mesh.meta={'category':'terrain_case','case':key,'wet':wet,'native_authoring_units':True,
               'external_inputs':external,'shared_ports':seams,'native_engine_test':False,
               'native_mesh_policy':'Terrace and Farm props unchanged; terrain and flat parcel placement are authored fixtures.'}
    return mesh,context


def extract_context(out, game):
    cache=out/'native-local';records=[]
    for pack,names in [('DX9/TerrainTextures.fpk',['afri_desert_d.dds','afri_grassland_d.dds','afri_mountain_base_d.dds','river_diffuse.dds']),
                       ('DX9/DecalTextures.fpk',['floodplains_d.dds'])]:
        archive=Archive(game/'Resource'/pack)
        for name in names:
            p=archive.extract(name,cache)
            records.append({'archive':pack,'entry':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    relative='Assets/terrain/pieces/Mountain/Africa/Afri_Mountain_1_1_H.dds'
    target=cache/'afri_mountain_1_1_h.dds';shutil.copyfile(game/relative,target)
    records.append({'loose_asset':relative,'entry':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    load_rock_height(target)
    return records


def save_overlay(reader, mesh, folder, cache):
    record=export(mesh,folder)
    graph=overlay_graph(reader.root(),mesh);path=folder/(mesh.name+'.gr2')
    Writer(reader).write(path,graph);scene=parts(Reader(path).root())
    write_glb(scene,cache,folder/(mesh.name+'.glb'))
    (folder/(mesh.name+'.fxsxml')).write_text('<?xml version="1.0"?>\n<Asset>\n'
        f'<Mesh file="{mesh.name}.gr2"/>\n<Texture file="RT_IF_Native_Diff.dds"/>\n'
        '<Texture file="RT_IF_Native_SREF.dds"/>\n</Asset>\n')
    obj=folder/mesh.name/(mesh.name+'.obj')
    obj.write_text(obj.read_text().replace('Normalized units, not engine-calibrated.', 'Native farm authoring units; engine fitting pending.'))
    return record,scene


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--quick',action='store_true')
    parser.add_argument('--only',choices=list(DESCRIPTIONS))
    args=parser.parse_args();out=args.output.resolve();folder=out/'terrain-review';folder.mkdir(exist_ok=True)
    imported=json.loads((out/'native-import.json').read_text());cache=out/'native-local'
    provenance=extract_context(out,Path(imported['source_installation']))
    reader=Reader(out/'incan_terrace_farm/incan_terrace_farm-uncompressed.gr2');native=parts(reader.root())
    props=parts(constructed(Reader(out/'medieval_farm1/medieval_farm1-uncompressed.gr2').root()))
    for name in ['RT_IF_Diffuse.png','RT_IF_Native_Diff.dds','RT_IF_Native_SREF.dds']:
        shutil.copyfile(out/'irrigation-fit'/name,folder/name)
    keys=[args.only] if args.only else list(DESCRIPTIONS)
    cases=[]
    for key in keys:
        print('Building '+key,flush=True)
        mesh,context=compose(key,native,props)
        rec,overlay=save_overlay(reader,mesh,folder,cache)
        dry,_=compose(key,native,props,False);dryrec,_=save_overlay(reader,dry,folder,cache)
        scene=context+overlay
        write_glb(scene,cache,folder/(key+'-combined.glb'))
        if key=='terrace':write_glb(native+overlay,cache,folder/'terrace-source-with-irrigation.glb')
        cases.append({'key':key,'label':DESCRIPTIONS[key][0],'description':DESCRIPTIONS[key][1],
                      'context':context,'overlay':overlay,'record':rec,'dry_record':dryrec,'scene':scene,
                      'view_degrees':[20,48] if key=='mountain_terrace' else [55,57]})
    # The shared atlas retains original crop pixels; terrain blend-alpha is
    # interpreted as opaque by the review shader, as specified in its materials.
    texture_names=sorted({diffuse(m) for c in cases for p in c['scene'] for m in p['materials']})
    opaque_names={diffuse(m) for c in cases for p in c['scene'] for m in p['materials'] if m.get('_previewAlphaMode')=='OPAQUE'}
    for c in cases:
        review=folder/(c['key']+'-review.glb')
        review_glb(c['scene'],cache,review,texture_names=texture_names,cell=512,columns=4,opaque_texture_names=opaque_names)
        if not args.quick:
            print('Rendering '+c['key'],flush=True)
            render_glb(review,960,720,azimuth=c['view_degrees'][0],elevation=c['view_degrees'][1],shadow_bias=.25).save(folder/(c['key']+'-preview.png'))
            render_glb(review,240,180,azimuth=c['view_degrees'][0],elevation=c['view_degrees'][1],shadow_bias=.25).save(folder/(c['key']+'-distance.png'))
    manifest={'status':'diagnostic fixtures, not the accepted native farm design baseline; engine layout integration pending',
              'native_engine_test':False,'proprietary_reference_output':True,'source_assets':provenance,
              'prominence':{'previous_terrace_water_width':.44,'terrace_water_width':.90,'flat_carrier_width':1.15,
                            'density_policy':'one carrier plus at most one flat-field branch; most plot seams dry'},
              'cases':[{k:v for k,v in c.items() if k not in ('context','overlay','scene')} for c in cases]}
    (folder/'terrain-cases.json').write_text(json.dumps(manifest,indent=2)+'\n')
    from terrain_viewer import build_viewer
    build_viewer(folder,cases)
    print(json.dumps({'output':str(folder),'cases':len(cases)},indent=2))


if __name__=='__main__':main()
