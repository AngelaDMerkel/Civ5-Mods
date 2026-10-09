#!/usr/bin/env python3
"""Import an owner's installed Civ V farm assets into an ignored local workspace."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from native_fpk import Archive
from native_gr2 import Reader, build_decoder
from gr2_writer import Writer
from native_scene import parts, diffuse, write_glb, review_glb, regular_farm_states, selected_models

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent/'irrigation_v3'))
from irrigation_mesh_io import render_glb
OUT = ROOT/'output/models/irrigated-farm-native-fit'


def semantic(value):
    if isinstance(value, dict):
        return {k: semantic(v) for k, v in value.items() if not k.startswith('_')}
    if isinstance(value, list):
        return [semantic(v) for v in value]
    return value


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def import_assets(game, output, quick=False):
    output.mkdir(parents=True, exist_ok=True)
    cache = output/'native-local'; cache.mkdir(exist_ok=True)
    archives = {}
    records = []
    def extract(pack, name):
        if pack not in archives:
            archives[pack] = Archive(game/'Resource'/pack)
        target = archives[pack].extract(name, cache)
        records.append({'archive': pack, 'entry': name.lower(), 'sha256': digest(target), 'bytes': target.stat().st_size})
        return target
    definitions = [('medieval_farm', 'ImprovementModels', 'improvementmodels', 'ImprovementTextures'),
                   ('modern_farm', 'ImprovementModels', 'improvementmodels', 'ImprovementTextures'),
                   ('incan_terrace_farm', 'ConquestDeluxeModels', 'conquestdeluxemodels', 'ConquestDeluxeTextures'),
                   ('hb_incan_terrace_farm', 'ConquestDeluxeModels', 'conquestdeluxemodels', 'ConquestDeluxeTextures'),
                   ('pl_incan_terrace_farm', 'ConquestDeluxeModels', 'conquestdeluxemodels', 'ConquestDeluxeTextures')]
    definitions += [(era+'_farm'+str(variant), 'ImprovementModels', 'improvementmodels', 'ImprovementTextures')
                    for era in ('medieval', 'modern') for variant in (1, 2, 3)]
    decoder = build_decoder(output/'codec')
    models = []
    for name, pack, database, texture_pack in definitions:
        meshpath = extract('Common/'+pack+'.fpk', name+'.gr2')
        wrapper = extract('Common/'+pack+'.fpk', name+'.fxsxml')
        gsd = extract('Common/'+pack+'.fpk', database+'_stringdatabase.gsd')
        reader = Reader(meshpath, gsd, decoder)
        root = reader.root()
        states = regular_farm_states(root) if name[-1:] in ('1', '2', '3') else None
        names = states['constructed'] if states else [m['Name'] for m in root['Models']]
        scene = parts(selected_models(root, names))
        if states:
            # Keep visible state materials; the tree-cut stencil stays a stock reference.
            for item in ET.parse(wrapper).getroot().findall('Texture'):
                if item.attrib['file'].lower() == 'generic_grey_8.dds':
                    continue  # Stencil helper is not part of the visible GLB.
                extract('DX9/'+texture_pack+'.fpk', item.attrib['file'])
        for texture in sorted({diffuse(m) for p in scene for m in p['materials']}):
            extract('DX9/'+texture_pack+'.fpk', texture)
        folder = output/name; folder.mkdir(exist_ok=True)
        source = folder/(name+'.glb')
        write_glb(scene, cache, source)
        roundtrip = folder/(name+'-uncompressed.gr2')
        Writer(reader).write(roundtrip, root)
        if semantic(Reader(roundtrip).root()) != semantic(root):
            raise ValueError('Native GR2 graph changed during round trip: '+name)
        model = {'name': name, 'source_sha256': digest(meshpath),
                 'vertices': sum(len(p['arrays']['Position']) for p in scene),
                 'triangles': sum(len(p['indices'])//3 for p in scene),
                 'visible_meshes': [p['name'] for p in scene],
                 'native_graph_round_trip': True, 'glb': str(source.relative_to(output)),
                 'preview_model_names': names, 'construction_states': states,
                 'source_coordinate_system': semantic(root['ArtToolInfo'])}
        models.append(model)
        if not quick and name in ('medieval_farm', 'incan_terrace_farm', 'medieval_farm1', 'modern_farm1'):
            review = folder/(name+'-review.glb')
            review_glb(scene, cache, review)
            render_glb(review, 1000, 750, elevation=50).save(folder/(name+'-mesh-preview.png'))
    farm_types = extract('Common/MiscData.fpk', 'farm_types.xml')
    table = ET.parse(farm_types).getroot()
    crops = []
    for item in table.find('Crops_Africa'):
        name = Path(item.attrib['albedo']).name.lower()
        extract('DX9/DecalTextures.fpk', name)
        crops.append(name)
    if not quick:
        sheet = Image.new('RGB', (1024, 600), '#ded8c8'); draw = ImageDraw.Draw(sheet)
        draw.text((20, 12), 'ACTUAL CIV V CROP DECALS — Crops_Africa / farm_types.xml', fill='#252924')
        for i, name in enumerate(crops):
            im = Image.open(cache/name).convert('RGBA')
            x, y = (i % 4)*256, 40+(i//4)*280
            sheet.paste(im.resize((256, 256)), (x, y), im.resize((256, 256)))
            draw.text((x+8, y+260), name, fill='#252924')
        sheet.save(output/'native-flat-crop-decals.png')
    regular_crops = {}
    for family in ('Crops_Africa', 'Crops_America', 'Crops_Asia', 'Crops_Europe'):
        regular_crops[family] = []
        for item in table.find(family):
            name = item.attrib['albedo'].replace('\\', '/').rsplit('/', 1)[-1].lower()
            extract('DX9/DecalTextures.fpk', name)
            regular_crops[family].append(name)
    manifest = {'status': 'Native source import and experimental GR2 round-trip; engine validation pending',
                'native_game_validation': False, 'redistributable': False,
                'source_installation': str(game), 'extracted_assets': records, 'models': models,
                'flat_farm_finding': 'Farm GR2s contain props. farm_types.xml separately references regional crop decals. Engine parcel placement has not been reproduced or hooked.',
                'crop_family': 'Crops_Africa', 'crop_decals': crops,
                'regular_crop_families': regular_crops,
                'regular_crop_policy': 'Keep the FARM layout handler and stock crop textures. No desert-specific family is inferred; engine selection and parcel placement remain native-test work.'}
    (output/'native-import.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-assets', type=Path, required=True, help='Civ V Assets directory containing Resource/')
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    result = import_assets(args.game_assets.resolve(), args.output.resolve(), args.quick)
    print(json.dumps({'output': str(args.output.resolve()), 'models': result['models']}, indent=2))


if __name__ == '__main__':
    main()
