"""Hash-pinned batch inputs and bundle verification shared by every mod."""
import json
import tempfile
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from .br2 import asset_name, read
from .format import FormatError, require
from .static import PROFILE, check_dds, convert, sha, verify_conversion


def read_json(path):
    try:
        value = json.loads(Path(path).read_text())
    except ValueError as e:
        raise FormatError(f'invalid JSON: {path}') from e
    require(isinstance(value, dict), 'expected JSON object')
    return value


def verify_bundle(manifest_path, source):
    """Recheck bytes and semantics; never promote a claimed native game status."""
    manifest_path, source = Path(manifest_path), Path(source)
    m = read_json(manifest_path)
    require(m.get('profile') == PROFILE, 'unsupported conversion profile')
    name = asset_name(m.get('name', ''))
    require(m.get('source_br2_sha256') == sha(source.read_bytes()), 'BR2 source hash mismatch')
    files = m.get('files')
    require(isinstance(files, dict) and len(files) == 4, 'expected GR2, FXSXML and two DDS files')
    folded = set()
    for filename, digest in files.items():
        require(isinstance(filename, str) and Path(filename).name == filename, 'invalid bundle path')
        asset_name(Path(filename).stem)
        require(filename.lower() not in folded, 'case-insensitive bundle filename collision')
        folded.add(filename.lower())
        require(sha((manifest_path.parent/filename).read_bytes()) == digest, f'bundle hash mismatch: {filename}')
    require(name+'.gr2' in files and name+'.fxsxml' in files, 'model filenames missing from bundle')
    try:
        wrapper = ET.parse(manifest_path.parent/(name+'.fxsxml')).getroot()
    except ET.ParseError as e:
        raise FormatError('invalid FXSXML') from e
    require(wrapper.tag == 'Asset' and [e.tag for e in wrapper] == ['Mesh', 'Texture', 'Texture'], 'invalid static FXSXML structure')
    paths = [e.get('file') for e in wrapper]
    require(paths[0] == name+'.gr2' and len(set(paths)) == 3 and set(paths) == set(files)-{name+'.fxsxml'}, 'FXSXML file references differ from bundle')
    for path in paths[1:]:
        require(Path(path).suffix.lower() == '.dds', 'expected DDS texture')
        check_dds(manifest_path.parent/path)
    records = verify_conversion((manifest_path.parent/paths[0]).read_bytes(), read(source), name, *paths[1:])
    require(m.get('meshes') == records, 'manifest geometry evidence mismatch')
    return {'name': name, 'structural_validation': 'passed', 'source_comparison': 'passed',
            'native_game': {'status': 'unverified'}, 'files': files, 'meshes': records}


def batch(manifest_path, output, *, probe=None):
    manifest_path, output = Path(manifest_path), Path(output)
    m = read_json(manifest_path)
    require(m.get('version') == 1 and isinstance(m.get('assets'), list) and m['assets'], 'expected batch version 1 and nonempty assets')
    require(len(m['assets']) <= 256, 'batch exceeds 256 models')
    require(not output.exists(), 'batch destination must not already exist; use a fresh directory')
    inputs, names, vfs = [], set(), {}
    # Validate all pins and VFS collisions before converting the first asset.
    for asset in m['assets']:
        require(isinstance(asset, dict), 'invalid batch asset')
        name = asset_name(asset.get('name', ''))
        require(name.lower() not in names, 'duplicate batch model name')
        names.add(name.lower())
        paths = {}
        for key in ('source', 'diffuse', 'sref'):
            entry = asset.get(key)
            require(isinstance(entry, dict) and isinstance(entry.get('path'), str), f'missing {key} input')
            path = manifest_path.parent/entry['path']
            digest = sha(path.read_bytes())
            require(digest == entry.get('sha256'), f'input hash mismatch: {path}')
            paths[key] = path
            if key != 'source':
                filename = path.name.lower()
                require(filename not in vfs or vfs[filename] == digest, f'conflicting texture VFS name: {path.name}')
                vfs[filename] = digest
        units = asset.get('units_per_meter', 1)
        require(isinstance(units, (int, float)) and math.isfinite(units) and units > 0, 'invalid units_per_meter')
        inputs.append((name, paths, units))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.civ5-gr2-batch-', dir=output.parent) as temp:
        stage = Path(temp)/'bundle'; stage.mkdir()
        records = []
        for name, paths, units in inputs:
            result = convert(paths['source'], stage/name, paths['diffuse'], paths['sref'], name=name,
                             units_per_meter=units, probe=probe)
            verify_bundle(stage/name/(name+'.conversion.json'), paths['source'])
            records.append(result)
        report = {'version': 1, 'profile': PROFILE, 'batch_sha256': sha(manifest_path.read_bytes()),
                  'conversion': 'completed', 'native_game': {'status': 'unverified'}, 'assets': records}
        (stage/'batch.conversion.json').write_text(json.dumps(report, indent=2)+'\n')
        require(not output.exists(), 'batch destination appeared during conversion')
        # All assets are complete before exposing the output directory.
        stage.rename(output)
    return report
