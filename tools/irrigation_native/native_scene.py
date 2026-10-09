"""Native mesh inspection/export. Source coordinates are retained in Z-up space."""
from pathlib import Path
import io
import json
import math
import struct
import numpy as np
from PIL import Image


def filename(value):
    return value.replace('\\', '/').rsplit('/', 1)[-1].lower()


def diffuse(material):
    for item in material['Maps']:
        if item['Usage'] in ('BaseTextureMap', 'Diffuse') and item['Map'].get('Texture'):
            return filename(item['Map']['Texture']['FromFileName'])
    raise ValueError('No native diffuse texture: '+str(material['Name']))


def transform(value):
    flags = value[0]
    matrix = np.eye(4)
    if flags & 1:
        matrix[:3, 3] = value[1:4]
    if flags & 2:
        x, y, z, w = value[4:8]
        matrix[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                         [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                         [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    if flags & 4:
        matrix[:3, :3] = matrix[:3, :3] @ np.array(value[8:17]).reshape(3, 3).T
    return matrix


def parts(root):
    """Exclude stencil helpers from visible exports; leave the GR2 graph intact."""
    result = []
    for model in root['Models']:
        for binding in model['MeshBindings']:
            mesh = binding['Mesh']
            if all('Stencil' in b['Material']['ExtendedData']['ShaderSet'] for b in mesh['MaterialBindings']):
                continue
            vertices = mesh['PrimaryVertexData']['Vertices']
            # This export supports rigid landmarks, not skinned units/animations.
            if any('BoneWeights' in v or 'BoneIndices' in v for v in vertices):
                raise ValueError('Skinned mesh requires a different exporter')
            arrays = {key: np.asarray([v[key] for v in vertices], dtype='<f4')
                      for key in ('Position', 'Normal', 'Tangent', 'Binormal', 'TextureCoordinates0')}
            top = mesh['PrimaryTopology']
            ix = top['Indices16'] or top['Indices']
            indices = np.array([next(v for k, v in item.items() if not k.startswith('_')) for item in ix], dtype=np.uint32)
            if len(indices) % 3 or indices.max() >= len(vertices):
                raise ValueError('Invalid native triangle indices')
            result.append({'name': mesh['Name'], 'arrays': arrays, 'indices': indices,
                           'transform': transform(model['InitialPlacement']),
                           'groups': [{k: g[k] for k in ('MaterialIndex', 'TriFirst', 'TriCount')} for g in top['Groups']],
                           'materials': [b['Material'] for b in mesh['MaterialBindings']]})
    return result


def write_glb(scene, texture_dir, destination):
    """Keep native indexed vertices, UVs, tangents and individual model transforms."""
    destination = Path(destination)
    blob, views, accessors, images, textures, materials, meshes, nodes = bytearray(), [], [], [], [], [], [], []
    image_ids, material_ids = {}, {}
    def add(data):
        blob.extend(b'\0'*(-len(blob) % 4))
        offset = len(blob); blob.extend(data)
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(data)})
        return len(views)-1
    def acc(data, kind, integer=False):
        data = np.asarray(data, dtype='<u4' if integer else '<f4')
        item = {'bufferView': add(data.tobytes()), 'componentType': 5125 if integer else 5126,
                'count': len(data), 'type': kind}
        if not integer:
            item.update(min=data.min(axis=0).tolist(), max=data.max(axis=0).tolist())
        accessors.append(item)
        return len(accessors)-1
    def material(native):
        name = native['Name']
        if name not in material_ids:
            path = diffuse(native)
            if path not in image_ids:
                stream = io.BytesIO()
                Image.open(Path(texture_dir)/path).convert('RGBA').save(stream, format='PNG')
                images.append({'bufferView': add(stream.getvalue()), 'mimeType': 'image/png', 'name': path})
                textures.append({'source': len(images)-1})
                image_ids[path] = len(textures)-1
            material_ids[name] = len(materials)
            materials.append({'name': name, 'doubleSided': True, 'alphaMode': native.get('_previewAlphaMode', 'MASK'), 'alphaCutoff': .5,
                              'pbrMetallicRoughness': {'baseColorTexture': {'index': image_ids[path]},
                                                     'metallicFactor': 0, 'roughnessFactor': 1},
                              'extras': {'nativeShader': native['ExtendedData']['ShaderSet'],
                                         'shaderApproximation': 'glTF preview; not the Civ V renderer'}})
        return material_ids[name]
    for part in scene:
        a = part['arrays']
        sign = np.sign(np.sum(np.cross(a['Normal'], a['Tangent'])*a['Binormal'], axis=1))
        tangent = np.column_stack((a['Tangent'], np.where(sign == 0, 1, sign)))
        attrs = {'POSITION': acc(a['Position'], 'VEC3'), 'NORMAL': acc(a['Normal'], 'VEC3'),
                 'TANGENT': acc(tangent, 'VEC4'), 'TEXCOORD_0': acc(a['TextureCoordinates0'][:, :2], 'VEC2'),
                 '_CIV5_TEXCOORD0': acc(a['TextureCoordinates0'], 'VEC3'),
                 '_CIV5_BINORMAL': acc(a['Binormal'], 'VEC3')}
        primitives = []
        for group in part['groups']:
            first, count = group['TriFirst']*3, group['TriCount']*3
            primitives.append({'attributes': attrs, 'indices': acc(part['indices'][first:first+count], 'SCALAR', True),
                               'material': material(part['materials'][group['MaterialIndex']])})
        meshes.append({'name': part['name'], 'primitives': primitives})
        nodes.append({'name': part['name'], 'mesh': len(meshes)-1,
                      'matrix': part['transform'].T.flatten().tolist()})
    # One basis change at the root: preserve all native authored transforms.
    nodes.append({'name': 'Civ V Z-up to glTF Y-up', 'rotation': [-math.sqrt(.5), 0, 0, math.sqrt(.5)],
                  'children': list(range(len(nodes)))})
    doc = {'asset': {'version': '2.0', 'generator': 'Realistic Terrain native asset importer'},
           'buffers': [{'byteLength': len(blob)}], 'bufferViews': views, 'accessors': accessors,
           'images': images, 'textures': textures, 'materials': materials, 'meshes': meshes,
           'nodes': nodes, 'scenes': [{'nodes': [len(nodes)-1]}], 'scene': 0}
    write_container(doc, blob, destination)
    return doc


def write_container(doc, blob, destination):
    encoded = json.dumps(doc, separators=(',', ':')).encode()
    encoded += b' '*(-len(encoded) % 4)
    blob += b'\0'*(-len(blob) % 4)
    Path(destination).write_bytes(struct.pack('<5I', 0x46546c67, 2, 28+len(encoded)+len(blob), len(encoded), 0x4e4f534a)
                                 + encoded+struct.pack('<2I', len(blob), 0x004e4942)+blob)


def world_arrays(part):
    a, m = part['arrays'], part['transform']
    p = a['Position'] @ m[:3, :3].T + m[:3, 3]
    n = a['Normal'] @ np.linalg.inv(m[:3, :3])
    n /= np.linalg.norm(n, axis=1)[:, None]
    return p, n


def review_glb(scene, texture_dir, destination, *, texture_names=None, cell=2048, columns=None, opaque_texture_names=None):
    """Flatten an inspection copy for the existing CPU renderer, separate from source GLB."""
    names = texture_names or sorted({diffuse(m) for part in scene for m in part['materials']})
    cols = columns or len(names); rows = math.ceil(len(names)/cols)
    opaque = set(opaque_texture_names or ()) | {diffuse(m) for part in scene for m in part['materials'] if m.get('_previewAlphaMode') == 'OPAQUE'}
    atlas = Image.new('RGBA', (cell*cols, cell*rows), (0, 0, 0, 0))
    for i, name in enumerate(names):
        im = Image.open(Path(texture_dir)/name).convert('RGBA')
        if name in opaque:
            im.putalpha(255)  # Terrain diffuse alpha encodes blend weight, not opacity.
        atlas.paste(im.resize((cell, cell), Image.Resampling.LANCZOS if cell < im.width else Image.Resampling.NEAREST), ((i % cols)*cell, (i//cols)*cell))
    ps, ns, ts = [], [], []
    for part in scene:
        p, n = world_arrays(part)
        for group in part['groups']:
            ix = part['indices'][group['TriFirst']*3:(group['TriFirst']+group['TriCount'])*3]
            t = part['arrays']['TextureCoordinates0'][ix, :2].copy()
            index = names.index(diffuse(part['materials'][group['MaterialIndex']]))
            t[:, 0] = (np.clip(t[:, 0], 0, 1)+index % cols)/cols
            t[:, 1] = (np.clip(t[:, 1], 0, 1)+index//cols)/rows
            ps.append(p[ix]); ns.append(n[ix]); ts.append(t)
    p, n, uv = map(np.concatenate, (ps, ns, ts))
    blob, views, accs = bytearray(), [], []
    def add(data):
        blob.extend(b'\0'*(-len(blob) % 4)); off = len(blob); blob.extend(data)
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data)})
        return len(views)-1
    for data, kind in ((p, 'VEC3'), (n, 'VEC3'), (uv, 'VEC2')):
        accs.append({'bufferView': add(np.array(data, dtype='<f4').tobytes()), 'componentType': 5126,
                     'count': len(data), 'type': kind, 'min': data.min(0).tolist(), 'max': data.max(0).tolist()})
    stream = io.BytesIO(); atlas.save(stream, format='PNG'); image = add(stream.getvalue())
    doc = {'asset': {'version': '2.0', 'generator': 'Local native review copy; UVs packed only for CPU rendering'},
           'buffers': [{'byteLength': len(blob)}], 'bufferViews': views, 'accessors': accs,
           'images': [{'bufferView': image, 'mimeType': 'image/png'}], 'textures': [{'source': 0}],
           'materials': [{'doubleSided': True, 'alphaMode': 'MASK', 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0}}],
           'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'material': 0}]}],
           'nodes': [{'mesh': 0, 'rotation': [-math.sqrt(.5), 0, 0, math.sqrt(.5)]}],
           'scenes': [{'nodes': [0]}], 'scene': 0}
    write_container(doc, blob, destination)
    return p, n, uv
