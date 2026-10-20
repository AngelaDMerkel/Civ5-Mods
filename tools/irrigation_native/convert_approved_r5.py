#!/usr/bin/env python3
"""Convert the hash-approved R5 sources without rebuilding or redesigning them."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / 'irrigation_v3'))
from tools.civ5_gr2.batch import batch, verify_bundle
from tools.civ5_gr2.br2 import read as read_br2
from tools.civ5_gr2.format import Reader, Node, VariantArray
from tools.civ5_gr2.static import check_dds
from build_concept_models import save_rgba_mips
from build_review_library import verified_r5_approval
from irrigation_mesh_io import read_glb, render_glb
from native_scene import review_glb

OUT = ROOT / 'output/models/irrigated-farm-native-fit'
APPROVAL = ROOT / 'shared/art/irrigated-farm/v3-civ5-direction/model-approval-r5.json'
DIFFUSE = 'RT_IF_R5_Diff.dds'
SREF = 'RT_IF_R5_SREF.dds'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def split_assembly(source, target):
    """Partition sequential triangles into 16-bit meshes, preserving every row."""
    lines = source.read_text().splitlines()
    first, end = lines.index('vertices') + 1, lines.index('triangles')
    assert lines[first-3] == 'meshes:1' and lines[-1] == 'end'
    vertices = lines[first:end]
    assert len(vertices) % 3 == 0
    triangles = [list(map(int, row.split())) for row in lines[end+1:-1]]
    assert triangles == [[i, i+1, i+2] for i in range(0, len(vertices), 3)]
    chunks = [vertices[i:i+65535] for i in range(0, len(vertices), 65535)]
    header = lines[:first-3] + [f'meshes:{len(chunks)}']
    for index, rows in enumerate(chunks):
        header += [f'mesh:"{source.stem}_Part{index}"', 'vertices', *rows, 'triangles']
        header += [f'{i} {i+1} {i+2}' for i in range(0, len(rows), 3)]
    target.write_text('\n'.join([*header, 'end']) + '\n')
    actual = read_br2(target)
    flattened = np.array([v for mesh in actual.meshes for v in mesh.vertices], dtype='<f4')
    expected = np.array([list(map(float, v.split())) for v in vertices], dtype='<f4')
    np.testing.assert_array_equal(flattened, expected)
    return len(chunks)


def native_value(value):
    if isinstance(value, Node):
        return {k: native_value(v) for k, v in value.values.items()}
    if isinstance(value, VariantArray):
        return [native_value(v) for v in value.items]
    if isinstance(value, list):
        return [native_value(v) for v in value]
    return value


def native_scene(path):
    root = Reader(path.read_bytes()).root()
    scene = []
    for mesh in root['Meshes']:
        vertices = mesh['PrimaryVertexData']['Vertices'].items
        arrays = {key: np.array([v[key] for v in vertices], dtype='<f4') for key in
                  ('Position', 'Normal', 'Tangent', 'Binormal', 'TextureCoordinates0')}
        topology = mesh['PrimaryTopology']
        scene.append(dict(name=mesh['Name'], arrays=arrays, transform=np.eye(4),
                          indices=np.array([v['Int16'] & 65535 for v in topology['Indices16']], dtype=np.uint32),
                          groups=native_value(topology['Groups']),
                          materials=[native_value(b['Material']) for b in mesh['MaterialBindings']]))
    return scene


def verify(source, output):
    approval = verified_r5_approval(source)
    assert approval, 'R5 source exports no longer match user approval'
    report = json.loads((output / 'conversion.json').read_text())
    assert report['approval_sha256'] == digest(APPROVAL)
    manifest = json.loads((source / 'models.json').read_text())
    records = {r['name']: r for r in manifest['models']}
    assert {r['name'] for r in report['assets']} == set(records)
    atlas = np.asarray(Image.open(source / 'RT_IF_Diffuse.png').convert('RGBA'))
    check_dds(output / 'inputs' / DIFFUSE)
    check_dds(output / 'inputs' / SREF)
    np.testing.assert_array_equal(np.asarray(Image.open(output / 'inputs' / DIFFUSE).convert('RGBA')), atlas)
    triangles = vertices = mesh_count = 0
    for item in report['assets']:
        name = item['name']; original = source / name / (name + '.br2')
        conversion_source = output / item['conversion_source'] if item['derived_source'] else original
        assert digest(original) == item['approved_br2_sha256']
        assert digest(conversion_source) == item['conversion_br2_sha256']
        folder = output / 'bundles' / name
        result = verify_bundle(folder / (name + '.conversion.json'), conversion_source)
        assert result['native_game']['status'] == 'unverified'
        assert result['files'] == item['files']
        scene = native_scene(folder / (name + '.gr2'))
        p, n, uv = [np.concatenate([part['arrays'][key][part['indices']] for part in scene]) for key in
                    ('Position', 'Normal', 'TextureCoordinates0')]
        _, arrays, _ = read_glb(source / name / (name + '.glb'))
        np.testing.assert_allclose(p, arrays[0], atol=1e-6, rtol=0)
        np.testing.assert_allclose(n, arrays[1], atol=2e-7, rtol=0)
        np.testing.assert_allclose(uv[:, :2], arrays[2], atol=2e-7, rtol=0)
        assert len(p) == records[name]['vertices'] == records[name]['triangles'] * 3
        if item['derived_source']:
            text = original.read_text().splitlines()
            rows = np.array([list(map(float, row.split())) for row in text[text.index('vertices')+1:text.index('triangles')]], dtype='<f4')
            adapted = read_br2(conversion_source)
            np.testing.assert_array_equal(rows, np.array([v for m in adapted.meshes for v in m.vertices], dtype='<f4'))
        for filename in (DIFFUSE, SREF):
            assert digest(folder / filename) == digest(output / 'inputs' / filename)
        vertices += len(p); triangles += len(p)//3; mesh_count += len(scene)
    result = dict(models=len(report['assets']), native_meshes=mesh_count, vertices=vertices,
                  triangles=triangles, gr2_br2_parity=True, gr2_glb_parity=True,
                  approved_exports_unchanged=72, diffuse_base_pixels_lossless=True,
                  native_game='unverified', dynamic_placement='unverified')
    write_json(output / 'validation.json', result)
    return result


def render(output):
    previews = output / 'previews'; previews.mkdir(exist_ok=True)
    for kind in ('Flat', 'GentleHill', 'SteepHill', 'RockyFoothill'):
        name = f'RT_IF_ConceptR5_{kind}_Wet'; folder = output / 'bundles' / name
        glb = previews / (kind + '-native-readback.glb')
        review_glb(native_scene(folder / (name + '.gr2')), folder, glb)
        render_glb(glb, 1000, 750, shadow_bias=.065).save(previews / (kind + '-native-readback.png'))
        print('Rendered converted GR2:', kind, flush=True)


def package(output):
    report = json.loads((output / 'conversion.json').read_text())
    expected = {filename: output / 'inputs' / filename for filename in (DIFFUSE, SREF)}
    for item in report['assets']:
        name = item['name']
        for ext in ('.gr2', '.fxsxml'):
            expected[name+ext] = output / 'bundles' / name / (name+ext)
    for filename in ('conversion.json', 'validation.json', 'README.txt'):
        expected[filename] = output / filename
    archive = output / 'RT_IF_R5_Native_Candidates.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, path in expected.items():
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, path.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == set(expected)
        for name, path in expected.items():assert hashlib.sha256(z.read(name)).hexdigest() == digest(path)
    return dict(path=archive.name, sha256=digest(archive), files=len(expected), archive_parity=True)


def build(source, output, probe):
    approval = verified_r5_approval(source)
    assert approval, 'Conversion requires exact R5 approval hashes'
    assert not output.exists(), 'Use --verify-only for an existing conversion; do not overwrite it'
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.r5-convert-', dir=output.parent) as temporary:
        stage = Path(temporary); inputs = stage / 'inputs'; inputs.mkdir()
        save_rgba_mips(Image.open(source / 'RT_IF_Diffuse.png'), inputs / DIFFUSE)
        save_rgba_mips(Image.new('RGBA', (64,64), (0,0,0,255)), inputs / SREF)
        entries = []; sources = []
        for item in approval['candidates']:
            name = item['name']; original = source / name / (name + '.br2')
            derived = name.endswith('_ConnectedDistrict')
            path = inputs / (name + '.br2') if derived else original
            meshes = split_assembly(original, path) if derived else len(read_br2(path).meshes)
            entries.append(dict(name=name, source=dict(path=os.path.relpath(path, inputs), sha256=digest(path)),
                                diffuse=dict(path=DIFFUSE, sha256=digest(inputs/DIFFUSE)),
                                sref=dict(path=SREF, sha256=digest(inputs/SREF))))
            sources.append(dict(name=name, approved_br2_sha256=digest(original), conversion_br2_sha256=digest(path),
                                derived_source=derived, conversion_source=str(path.relative_to(stage)) if derived else str(original.relative_to(ROOT)),
                                native_meshes=meshes))
        write_json(inputs / 'batch.json', dict(version=1, assets=entries))
        result = batch(inputs / 'batch.json', stage / 'bundles', probe=probe)
        for source_item, converted in zip(sources, result['assets']):
            assert source_item['name'] == converted['name']
            source_item.update(files=converted['files'], independent_reader=converted['independent_reader'])
        write_json(stage / 'conversion.json', dict(revision=5, conversion='completed', profile=result['profile'],
                   approval_sha256=digest(APPROVAL), approved_source_commit=approval['source_commit'],
                   user_request='Native conversion should be made', source_design_approved=True,
                   native_game='unverified', runtime_integration=False, redistributable=False,
                   scale_policy='Approved normalized coordinates retained; UnitsPerMeter=1. Landmark display scale and terrain fitting require native validation.',
                   assembly_policy='ConnectedDistrict is a review fixture, partitioned into three 16-bit meshes without geometry changes; not one improvement tile.',
                   material_policy='Shared BuildingShader static profile; exact RGBA diffuse pixels with full mip chain. Black SREF is a candidate. Alpha, lighting and water appearance require native validation.',
                   assets=sources))
        (stage / 'README.txt').write_text('R5 native-format candidates from the approved source meshes.\n'
            '24 GR2 models, 24 FXSXML wrappers and two shared DDS textures.\n'
            'Geometry/UV/tangent/index preservation is checked; these are not in-game screenshots or installed improvements.\n'
            'Normalized source coordinates are unchanged. Calibrate landmark display scale and terrain placement in the game.\n'
            'ConnectedDistrict is a multi-tile review fixture, not a single improvement. LOD files are separate assets, not automatic switches.\n'
            'Wet/dry states are static; construction/pillaged states and dynamic water animation are not added here.\n'
            'Native-derived textures and Farm1 geometry: local owner review only, not for redistribution.\n'
            'Runtime Farm fallback is unchanged. Native rendering and integration remain pending.\n')
        verify(source, stage)
        stage.rename(output)
    return output



def review_page(output):
    report = json.loads((output / 'conversion.json').read_text())
    rows = []
    for item in report['assets']:
        name = item['name']
        links = ''.join(f'<td><a href="bundles/{name}/{name}.{ext}" download>{ext.upper()}</a></td>' for ext in ('gr2', 'fxsxml'))
        rows.append(f'<tr><td>{html.escape(name)}</td>{links}</tr>')
    template = (HERE / 'native_conversion_review.html').read_text()
    (output / 'review.html').write_text(template.replace('__EXPORT_ROWS__', '\n'.join(rows)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=OUT/'concept-models-r5')
    p.add_argument('--output', type=Path, default=OUT/'native-r5')
    p.add_argument('--probe', type=Path)
    p.add_argument('--verify-only', action='store_true')
    p.add_argument('--render', action='store_true')
    a = p.parse_args(); source=a.source.resolve(); output=a.output.resolve()
    if not a.verify_only:build(source, output, a.probe)
    report=verify(source, output)
    if a.render:render(output)
    report['archive']=package(output)
    write_json(output/'delivery-validation.json', report)
    if (output/'previews/RockyFoothill-native-readback.png').is_file():review_page(output)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':main()
