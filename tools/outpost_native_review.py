#!/usr/bin/env python3
"""Prepare disposable era/state render scenes from verified Outpost conversions.

Never installs files or starts Civ V. Use the shared locked background runner
after WSDLC packaging. Source designs and production assets are not modified.
"""
import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from civ5_gr2.batch import verify_bundle
from civ5_gr2.harness import FIXTURES, FIXTURE_ID, fixture_xml
from build import manifest, modbuddy, write_xml

ROOT = Path(__file__).resolve().parents[1]
ERAS = ('Ancient', 'Classical', 'Medieval', 'Renaissance', 'Industrial', 'Modern', 'Atomic', 'Information')
STATES = ('', '_UnderConstruction', '_Pillaged')


def prepare(batch, sources, output, era, scale=6, terrain='grass'):
    if output.exists():
        raise ValueError('Use a fresh fixture directory')
    stem = 'RO_' + era
    records = []
    for suffix in STATES:
        name = stem + suffix
        records.append(verify_bundle(batch/name/(name+'.conversion.json'), sources/name/(name+'.br2')))
    output.mkdir(parents=True)
    for folder in ('Art', 'XML', 'Maps', 'Lua'):
        (output/folder).mkdir()
    for record in records:
        for filename in record['files']:
            dest = output/'Art'/filename
            data = (batch/record['name']/filename).read_bytes()
            if dest.exists() and dest.read_bytes() != data:
                raise ValueError('Conflicting shared texture')
            dest.write_bytes(data)
    xml = ET.fromstring(fixture_xml(stem, scale))
    for row in xml.findall('ArtDefine_Landmarks/Row'):
        state = row.findtext('State')
        suffix = '' if state == 'Constructed' else '_' + state
        row.find('Model').text = stem + suffix + '.fxsxml'
    builds = ET.SubElement(xml, 'Builds')
    row = ET.SubElement(builds, 'Row')
    for key, value in dict(Type='BUILD_CG2_STATIC', ImprovementType='IMPROVEMENT_CG2_STATIC',
                           Description='TXT_KEY_CG2_STATIC', Time=1000).items():
        ET.SubElement(row, key).text = str(value)
    write_xml(xml, output/'XML/CG2_Art.xml')
    shutil.copyfile(FIXTURES/'CG2_StaticTest.lua', output/'Maps/CG2_StaticTest.lua')
    scene = (ROOT/'mods/resource-outposts/tests/native/RO_RenderScene.lua').read_text().replace('__ERA__', era).replace('__SCALE__', str(scale)).replace('__TERRAIN__', terrain)
    (output/'Lua/CG2_Scene.lua').write_text(scene)
    files = {p.relative_to(output).as_posix(): p for p in sorted(output.rglob('*')) if p.is_file()}
    spec = dict(id=FIXTURE_ID, version=1, name='Outpost Native Review',
                description='Disposable Outpost era/state renderer fixture.',
                actions=['XML/CG2_Art.xml'], entry='Lua/CG2_Scene.lua')
    mod = manifest(files, spec)
    mod.find('References').clear(); mod.find('Blocks').clear()
    entry = ET.SubElement(mod.find('EntryPoints'), 'EntryPoint', type='MapScript', file='Maps/CG2_StaticTest.lua')
    ET.SubElement(entry, 'Name').text='Outpost Native Review'
    ET.SubElement(entry, 'Description').text='Fresh diagnostic scene only.'
    write_xml(mod, output/'Outpost Native Review.modinfo')
    write_xml(modbuddy(files, mod, spec), output/'Outpost Native Review.civ5proj')
    (output/'fixture.json').write_text(json.dumps(dict(era=era, scale=scale, terrain=terrain, assets=records,
        native_game='unverified', coordinates=dict(intact=[8,8], construction=[10,8], pillaged=[8,10], fort=[10,10])), indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--sources', type=Path, default=ROOT/'output/models/outpost-eras-v1')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--era', choices=ERAS)
    parser.add_argument('--terrain', choices=('grass', 'mixed'), default='grass')
    args=parser.parse_args()
    for era in (args.era,) if args.era else ERAS:
        prepare(args.batch, args.sources, args.output/era, era, terrain=args.terrain)
        print('Prepared', era, flush=True)


if __name__ == '__main__':
    main()
