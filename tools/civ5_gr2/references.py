"""Read-only local reference extraction. Never include extracts in releases."""
import hashlib
import json
import struct
from pathlib import Path

from .format import FormatError, require


def extract_fort(fpk, destination):
    data = Path(fpk).read_bytes()
    require(data[:10] == b'\x06\0\0\0FPK_\0\0', 'unsupported FPK header')
    require(len(data) >= 14, 'truncated FPK')
    count = struct.unpack_from('<I', data, 10)[0]
    require(count <= 100000, 'unreasonable FPK entry count')
    entries = []
    offset = 14
    for _ in range(count):
        require(offset + 4 <= len(data), 'truncated FPK entry')
        length = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        padded = (length + 3) // 4 * 4
        require(0 < length <= 1024 and offset + padded + 16 <= len(data), 'invalid FPK filename')
        name = data[offset:offset + length].decode('utf-8')
        require(Path(name).name == name and '\\' not in name and name not in ('.', '..'), 'unsafe FPK path')
        offset += padded
        _, size, start = struct.unpack_from('<QII', data, offset)
        offset += 16
        require(start + size <= len(data), 'FPK payload out of bounds')
        entries.append((name, start, size))
    result = []
    destination = Path(destination)
    selected = []
    for name, start, size in entries:
        require(start >= offset, 'FPK payload overlaps directory')
        if name in {'fort_mid.gr2', 'hb_fort_mid.gr2', 'pl_fort_mid.gr2',
                    'fort_mod.gr2', 'hb_fort_mod.gr2', 'pl_fort_mod.gr2',
                    'fort_mid.fxsxml', 'hb_fort_mid.fxsxml', 'pl_fort_mid.fxsxml',
                    'fort_mod.fxsxml', 'hb_fort_mod.fxsxml', 'pl_fort_mod.fxsxml',
                    'improvementmodels_stringdatabase.gsd'}:
            content = data[start:start + size]
            target = destination / name
            require(not target.exists() or target.read_bytes() == content, f'refusing to replace different reference: {target}')
            selected.append((target, content))
            result.append({'name': name, 'bytes': size, 'sha256': hashlib.sha256(content).hexdigest()})
    require(len(selected) == 13, 'expected six Fort GR2s, six wrappers and matching GSD')
    destination.mkdir(parents=True, exist_ok=True)
    for target, content in selected:
        target.write_bytes(content)
    manifest = {'source': str(Path(fpk).resolve()), 'source_sha256': hashlib.sha256(data).hexdigest(), 'files': result}
    (destination / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def summarize(reader):
    root = reader.root()
    def primitive(node):
        return {k: ([next(iter(n.values.values())) for n in v] if isinstance(v, list) else v)
                for k, v in node.values.items()}
    materials = []
    for material in root.values.get('Materials', []):
        extra = material['ExtendedData']
        record = {'name': material['Name']}
        if extra:
            record['settings'] = {k: v for k, v in extra.values.items() if isinstance(v, (str, int, float))}
            record['parameter_sets'] = [primitive(extra[f'ParameterSet{i}']) for i in range(extra['ParameterSetCount'])]
        materials.append(record)
    meshes = []
    for mesh in root.values.get('Meshes', []):
        vertices = mesh['PrimaryVertexData']['Vertices']
        topology = mesh['PrimaryTopology']
        meshes.append({'name': mesh['Name'], 'vertices': len(vertices.items),
                       'stride': vertices.definition.size(),
                       'layout': [{'name': m.name, 'kind': m.kind, 'width': m.width} for m in vertices.definition.members],
                       'indices': len(topology['Indices']) + len(topology['Indices16']),
                       'groups': [n.values for n in topology['Groups']],
                       'materials': [n['Material']['Name'] for n in mesh['MaterialBindings']],
                       'bones': [n['BoneName'] for n in mesh['BoneBindings']]})
    return {'validation': 'structural only; native rendering unverified', 'version': reader.header[0],
            'tag': f'0x{reader.header[9]:08x}', 'string_database_id': reader.header[14],
            'sections': [{'compression': s[0], 'encoded_bytes': s[2], 'decoded_bytes': s[3],
                          'relocations': s[8], 'marshalling_records': s[10]} for s in reader.sections],
            'materials': materials, 'meshes': meshes,
            'models': [{'name': n['Name'], 'skeleton': n['Skeleton']['Name'],
                        'placement': n['InitialPlacement'],
                        'meshes': [v['Mesh']['Name'] for v in n['MeshBindings']]} for n in root.values.get('Models', [])]}
