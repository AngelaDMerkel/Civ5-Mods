"""Build a disposable native-render fixture; never install or claim game success."""
import json
import math
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .batch import verify_bundle
from .format import require

FIXTURE_ID = '2b0f606d-dc3e-4c4c-bebf-ec3b7c464979'
FIXTURES = Path(__file__).with_name('fixtures')


def fixture_xml(name, scale):
    root = ET.Element('GameData')
    def row(table, **values):
        item=ET.SubElement(ET.SubElement(root, table), 'Row')
        for key,value in values.items():
            ET.SubElement(item,key).text=str(value)
    row('Improvements', Type='IMPROVEMENT_CG2_STATIC', Description='TXT_KEY_CG2_STATIC',
        ArtDefineTag='ART_DEF_IMPROVEMENT_CG2_STATIC', OutsideBorders=1,
        PortraitIndex=24, IconAtlas='TERRAIN_ATLAS')
    row('ArtDefine_LandmarkTypes', Type='ART_DEF_IMPROVEMENT_CG2_STATIC',
        LandmarkType='Improvement', FriendlyName='GR2 test candidate')
    for state in ('Constructed','UnderConstruction','Pillaged'):
        row('ArtDefine_Landmarks', Era='Any', State=state, Scale=scale,
            ImprovementType='ART_DEF_IMPROVEMENT_CG2_STATIC', LayoutHandler='SNAPSHOT',
            ResourceType='ART_DEF_RESOURCE_ALL', Model=name+'.fxsxml', TerrainContour=0)
    row('Language_en_US', Tag='TXT_KEY_CG2_STATIC', Text='GR2 test candidate')
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)+b'\n'


def harness(manifest, source, output, scale=6):
    require(isinstance(scale,(float,int)) and math.isfinite(scale) and 0 < scale <= 100, 'test scale must be between 0 and 100')
    manifest, output = Path(manifest), Path(output)
    evidence=verify_bundle(manifest, source)
    require(not output.exists(), 'test fixture destination must not exist')
    # Reuse the repository manifest/ModBuddy generators without registering a
    # third release. This package exists only in the ignored test staging tree.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    try:
        from build import manifest as make_manifest, modbuddy, write_xml
    finally:
        sys.path.pop(0)
    name=evidence['name']
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.gr2-fixture-',dir=output.parent) as temp:
        stage=Path(temp)/'fixture';stage.mkdir()
        for filename in evidence['files']:
            target=stage/'Art'/filename;target.parent.mkdir(exist_ok=True)
            shutil.copyfile(manifest.parent/filename,target)
        (stage/'XML').mkdir();(stage/'XML/CG2_Art.xml').write_bytes(fixture_xml(name,scale))
        (stage/'Maps').mkdir();shutil.copyfile(FIXTURES/'CG2_StaticTest.lua',stage/'Maps/CG2_StaticTest.lua')
        (stage/'Lua').mkdir()
        scene=(FIXTURES/'CG2_Scene.lua').read_text().replace('__MODEL__',name).replace('__SCALE__',str(scale)).replace('__HASH__',evidence['files'][name+'.gr2'])
        (stage/'Lua/CG2_Scene.lua').write_text(scene)
        files={p.relative_to(stage).as_posix():p for p in sorted(stage.rglob('*')) if p.is_file()}
        spec={'id':FIXTURE_ID,'version':1,'name':'GR2 Static Render Test',
              'description':'Disposable native renderer fixture; not a playable mod release.',
              'actions':['XML/CG2_Art.xml'],'entry':'Lua/CG2_Scene.lua'}
        mod=make_manifest(files,spec)
        # The normal builder supplies Outposts/Terrain relationships; this
        # independent diagnostic has only its existing BNW dependency.
        mod.find('References').clear();mod.find('Blocks').clear()
        mod.find('Properties/Teaser').text='Disposable native GR2 renderer fixture.'
        entry=ET.SubElement(mod.find('EntryPoints'),'EntryPoint',type='MapScript',file='Maps/CG2_StaticTest.lua')
        ET.SubElement(entry,'Name').text='GR2 Static Rendering Test'
        ET.SubElement(entry,'Description').text='Two players, no city states; fresh game only.'
        write_xml(mod,stage/'GR2 Static Render Test.modinfo')
        write_xml(modbuddy(files,mod,spec),stage/'GR2 Static Render Test.civ5proj')
        report={'fixture_id':FIXTURE_ID,'name':name,'scale':scale,'gr2_sha256':evidence['files'][name+'.gr2'],
                'native_game':{'status':'unverified'},'scene':'candidate at 8,8; stock Fort at 10,8',
                'scope':'only CG2_StaticTest map on elapsed turn zero; no automatic turns or saves'}
        (stage/'fixture.json').write_text(json.dumps(report,indent=2)+'\n')
        stage.rename(output)
    return report
