"""Validate packaged Outpost meshes against the reviewed native conversion pins."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from civ5_gr2.format import Reader
from civ5_gr2.static import check_dds


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_runtime(root, stage):
    pins_path = root / 'tools/civ5_gr2/manifests/resource-outposts-v1.json'
    pins = {a['name']: a for a in json.loads(pins_path.read_text())['assets']}
    report = json.loads((root / 'mods/resource-outposts/docs/native-art-manifest.json').read_text())
    assert report['profile'] == 'civ5-building-static-v1'
    assert report['batch_sha256'] == sha(pins_path)
    assert len(report['assets']) == len(pins) == 24
    assert {a['name'] for a in report['assets']} == set(pins)
    manifest = ET.parse(stage / 'Resource Outposts.modinfo').getroot()
    vfs = {Path(n.text).name: stage / n.text for n in manifest.find('Files') if n.get('import') == '1'}
    expected = {}
    for asset in report['assets']:
        name = asset['name']
        pin = pins[name]
        assert asset['source_br2_sha256'] == pin['source']['sha256']
        assert asset['structural_validation'] == 'passed'
        assert asset['independent_reader']['status'] == 'passed'
        files = asset['files']
        assert set(files) == {name + '.gr2', name + '.fxsxml', name + '_diffuse.dds', 'RO_Era_BlackSpec.dds'}
        assert files[name + '_diffuse.dds'] == pin['diffuse']['sha256']
        assert files['RO_Era_BlackSpec.dds'] == pin['sref']['sha256']
        for filename, digest in files.items():
            assert expected.setdefault(filename, digest) == digest, 'Conflicting shared native asset'
            assert filename in vfs and vfs[filename] == stage / 'Art/Models' / filename
            assert sha(vfs[filename]) == digest, 'Native asset changed: ' + filename
        wrapper = ET.parse(vfs[name + '.fxsxml']).getroot()
        assert wrapper.tag == 'Asset'
        assert [e.tag for e in wrapper] == ['Mesh', 'Texture', 'Texture']
        assert [e.get('file') for e in wrapper] == [name + '.gr2', name + '_diffuse.dds', 'RO_Era_BlackSpec.dds']
        model = Reader(vfs[name + '.gr2'].read_bytes()).root()
        assert len(model['Models']) == len(model['Materials']) == 1
        assert model['Models'][0]['Name'] == name
        material = model['Materials'][0]['ExtendedData']
        assert material['ShaderSet'] == 'BuildingShader' and material['SkinBoneCount'] == 0
        textures = material['ParameterSet1']['ParamDataT']
        assert textures[0]['String'] == name + '_diffuse.dds'
        assert textures[4]['String'] == 'RO_Era_BlackSpec.dds'
    assert len(expected) == 73
    assert {p.name for p in (stage / 'Art/Models').iterdir()} == set(expected)
    for filename in expected:
        if filename.endswith('.dds'):
            check_dds(vfs[filename])
    print('Outpost native art: 24 pinned GR2/FXSXML models, 25 DDS textures, BuildingShader and VFS imports validated')
