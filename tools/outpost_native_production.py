#!/usr/bin/env python3
"""Stage actual Outpost database/art and RO_Eras for a disposable native probe.

The macOS DLC fixture serializes SQL results from an in-memory copy of BNW.
It does not install a playable DLC or exercise the full claims/UI lifecycle.
"""
import argparse
import hashlib
import json
import shutil
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

from build import manifest, modbuddy, write_xml
from civ5_gr2.harness import FIXTURES, FIXTURE_ID

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'mods/resource-outposts/src'


def prepare(database, output):
    if output.exists():
        raise ValueError('Use a fresh production probe directory')
    original=sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True)
    db=sqlite3.connect(':memory:'); original.backup(db); original.close()
    for name in ('RO_Outposts.sql', 'RO_Art.sql', 'RO_Eras.sql'):
        db.executescript((SOURCE/'SQL'/name).read_text())
    xml=ET.Element('GameData')
    schema=ET.SubElement(xml, 'Table', name='RO_OutpostEras')
    for _, name, kind, required, default, primary in db.execute('PRAGMA table_info(RO_OutpostEras)'):
        attrs=dict(name=name,type=kind.lower())
        if required: attrs['notnull']='true'
        if primary: attrs['primarykey']='true'
        if name in ('ImprovementType','ArtDefineTag','ModelStem'): attrs['unique']='true'
        ET.SubElement(schema,'Column',**attrs)
    family="(SELECT ImprovementType FROM RO_OutpostEras UNION SELECT 'IMPROVEMENT_RT_RESOURCE_OUTPOST')"
    art="(SELECT ArtDefineTag FROM RO_OutpostEras UNION SELECT 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST')"
    queries={
        'Improvements':f'Type IN {family}', 'Builds':"Type='BUILD_RT_RESOURCE_OUTPOST'",
        'Improvement_ResourceTypes':f'ImprovementType IN {family}',
        'Improvement_ValidFeatures':f'ImprovementType IN {family}',
        'BuildFeatures':"BuildType='BUILD_RT_RESOURCE_OUTPOST'",
        'IconTextureAtlases':"Atlas IN ('RO_OUTPOST_PORTRAITS','RO_OUTPOST_ACTION')",
        'ArtDefine_LandmarkTypes':f'Type IN {art}',
        'ArtDefine_Landmarks':f'ImprovementType IN {art}',
        'ArtDefine_StrategicView':f'StrategicViewType IN {art}',
        'RO_OutpostEras':'1=1',
    }
    counts={}
    for table,where in queries.items():
        cursor=db.execute(f'SELECT * FROM {table} WHERE {where}')
        columns=[c[0] for c in cursor.description]
        node=ET.SubElement(xml,table); counts[table]=0
        for values in cursor:
            row=ET.SubElement(node,'Row'); counts[table]+=1
            for key,value in zip(columns,values):
                if key!='ID' and value is not None: ET.SubElement(row,key).text=str(value)
    db.close()
    output.mkdir(parents=True)
    for folder in ('XML','Lua','Maps','Text'): (output/folder).mkdir()
    write_xml(xml,output/'XML/CG2_Production.xml')
    shutil.copytree(SOURCE/'Art',output/'Art')
    shutil.copyfile(SOURCE/'Text/RO_Text.xml',output/'Text/RO_Text.xml')
    shutil.copyfile(SOURCE/'Lua/RO_Eras.lua',output/'Lua/RO_Eras.lua')
    shutil.copyfile(ROOT/'mods/resource-outposts/tests/native/RO_ProductionScene.lua',output/'Lua/CG2_Scene.lua')
    shutil.copyfile(FIXTURES/'CG2_StaticTest.lua',output/'Maps/CG2_StaticTest.lua')
    files={p.relative_to(output).as_posix():p for p in sorted(output.rglob('*')) if p.is_file()}
    spec=dict(id=FIXTURE_ID,version=1,name='Outpost Production Art Probe',
              description='Disposable native art binding and era setter probe; no claims or management UI.',
              actions=['Text/RO_Text.xml','XML/CG2_Production.xml'],entry='Lua/CG2_Scene.lua')
    mod=manifest(files,spec); mod.find('References').clear(); mod.find('Blocks').clear()
    entry=ET.SubElement(mod.find('EntryPoints'),'EntryPoint',type='MapScript',file='Maps/CG2_StaticTest.lua')
    ET.SubElement(entry,'Name').text='Outpost production probe'
    ET.SubElement(entry,'Description').text='Fresh diagnostic scene only.'
    write_xml(mod,output/'Outpost Production Art Probe.modinfo')
    write_xml(modbuddy(files,mod,spec),output/'Outpost Production Art Probe.civ5proj')
    hashes={p.relative_to(SOURCE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(SOURCE.rglob('*')) if p.is_file()}
    (output/'fixture.json').write_text(json.dumps(dict(source_hashes=hashes,rows=counts,
        scope='Native RO_Eras and production database/art only; claims, UI and save lifecycle excluded'),indent=2)+'\n')
    print('Prepared production probe:', counts)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); prepare(args.database,args.output)
