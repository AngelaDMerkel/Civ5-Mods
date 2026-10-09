"""Civ V BuildingShader static profile, authored from measured Fort interfaces."""
import hashlib
import json
import math
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

from .br2 import IDENTITY, asset_name, read
from .format import FormatError, Reader, VariantArray, Writer, require
from .schema import DEFINITIONS, node

PROFILE = 'civ5-building-static-v1'
TRANSFORM = [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1]


def scalar_array(kind, key, values):
    return [node(kind, **{key: value}) for value in values]


def parameter_set(name, names, types, usage, regs, sizes, semantics, storage, textures=(), integers=()):
    return node('ParameterSet', ParamBlock=name, ParamCount=len(names),
                ParamNames=scalar_array('String', 'String', names),
                **{key: scalar_array('Int32', 'Int32', values) for key, values in {
                    'ParamTypes': types, 'ParamUsage': usage, 'ParamRegs': regs, 'ParamSize': sizes,
                    'ParamSemantics': semantics, 'ParamStoreIdx': storage, 'ParamFlags': [8]*len(names),
                    'ParamDataI': integers}.items()},
                ParamDataT=scalar_array('String', 'String', textures), ParamDataF=[], ParamActive=1)


def material(name, diffuse, sref):
    global_set = parameter_set('BuildingGlobal',
        ['ViewInverseMatrix', 'ViewProjMatrix', 'ViewMatrix', 'f4ControlValues', 'f3FogColor',
         'v3CameraWorld', 'fWaterHeight', 'OverlayProjection', 'f4FOWBaseScale'],
        [0]*9, [1, 1, 1, 0, 0, 0, 0, 1, 0],
        [851968, 65535, 327679, -65532, -65531, -65530, -65529, 589823, 851967],
        [64, 64, 64, 16, 16, 16, 16, 64, 16], [12, 4, 3, -1, -1, -1, -1, -1, -1], [-1]*9)
    texture_set = parameter_set('BuildingTextures',
        ['Diffuse', 'BuildingSREF', 'Irradiance', 'SpecSharp', 'SpecSoft', 'ColorCorrection',
         'DistanceFogRamp', 'FOWMask', 'FOWBaseLayer', 'FOWColorKey'],
        [6, 6, 7, 7, 7, 10, 6, 6, 6, 10], [0]*10,
        [-65536, -65535, -65534, -65533, -65532, -65530, -65531, -65529, -65528, -65527],
        [16]*10, [42]+[-1]*9, [0, 4, 8, 12, 16, -4, 20, 24, 28, 32],
        [diffuse, '', '', '', sref] + ['']*31, [0]*4)
    extension = node('BuildingMaterial', ShaderSet='BuildingShader',
        FallbackMtl=scalar_array('String', 'String', ['']), UseFallbackMtl=0,
        AlphaMode=8, ZMode=4, AlphaRef=128, SkinBoneCount=0, Reflections=0,
        Shadows=1, AlphaSort=0, Version=4, Invisible=0, typeName='FireGrafixMaterial',
        ParameterSetCount=2, ParameterSet0=global_set, ParameterSet1=texture_set, **{'Z-Fail': 0})
    maps = []
    for usage, filename in [('Diffuse', diffuse), ('BuildingSREF', sref)]:
        texture = node('Texture', FromFileName=filename, TextureType=0, Width=0, Height=0,
                       Encoding=1, SubFormat=0, Images=[], Layout=node('PixelLayout',
                       BytesPerPixel=4, ShiftForComponent=[0, 8, 16, 24], BitsForComponent=[8]*4))
        maps.append(node('MaterialMap', Usage=usage, Map=node('Material', Name=name+'_'+usage,
                                                           Maps=[], Texture=texture)))
    return node('Material', Name=name, Maps=maps, ExtendedData=extension)


def build_graph(model, name, diffuse, sref, units_per_meter=1):
    require(math.isfinite(units_per_meter) and units_per_meter > 0, 'units per meter must be positive and finite')
    mat = material(name+'_Material', diffuse, sref)
    bone = node('Bone', Name=model.bone, ParentIndex=-1, Transform=TRANSFORM,
                InverseWorldTransform=IDENTITY, LODError=0)
    skeleton = node('Skeleton', Name=model.bone, Bones=[bone], LODType=0)
    meshes, vertex_data, topologies = [], [], []
    for source in model.meshes:
        vertices = [node('Vertex', Position=v[:3], Normal=v[3:6], Tangent=v[16:19],
                         Binormal=v[19:22], TextureCoordinates0=v[6:8]+[0]) for v in source.vertices]
        vd = node('VertexData', Vertices=VariantArray(DEFINITIONS['Vertex'], vertices),
                  VertexComponentNames=scalar_array('ComponentName', 'String',
                    ['Position', 'Normal', 'Tangent', 'Binormal', 'TextureCoordinates0']), VertexAnnotationSets=[])
        indices = [i for tri in source.triangles for i in tri]
        topology = node('Topology', Groups=[node('Group', MaterialIndex=0, TriFirst=0, TriCount=len(source.triangles))],
                        Indices16=scalar_array('Index16', 'Int16', [i if i < 32768 else i-65536 for i in indices]))
        bounds = [[f(v[axis] for v in source.vertices) for axis in range(3)] for f in (min, max)]
        mesh = node('Mesh', Name=source.name, PrimaryVertexData=vd, PrimaryTopology=topology,
                    MaterialBindings=[node('MaterialBinding', Material=mat)],
                    BoneBindings=[node('BoneBinding', BoneName=model.bone, OBBMin=bounds[0], OBBMax=bounds[1])])
        meshes.append(mesh); vertex_data.append(vd); topologies.append(topology)
    return node('Root', ArtToolInfo=node('ArtTool', FromArtToolName='civ5-gr2 BR2 static converter',
                ArtToolMajorRevision=1, ArtToolMinorRevision=0, ArtToolPointerSize=32,
                UnitsPerMeter=units_per_meter, Origin=[0]*3, RightVector=[1, 0, 0], UpVector=[0, 0, 1], BackVector=[0, -1, 0]),
                ExporterInfo=node('Exporter', ExporterName='civ5-gr2 '+PROFILE, ExporterMajorRevision=1,
                                  ExporterMinorRevision=0, ExporterCustomization=0, ExporterBuildNumber=1),
                FromFileName=name+'.br2', Textures=[], Materials=[mat], Skeletons=[skeleton],
                VertexDatas=vertex_data, TriTopologies=topologies, Meshes=meshes,
                Models=[node('Model', Name=name, Skeleton=skeleton, InitialPlacement=TRANSFORM,
                             MeshBindings=[node('MeshBinding', Mesh=m) for m in meshes])])


def vertex_bytes(mesh):
    return b''.join(struct.pack('<15f', *v[:6], *v[16:22], *v[6:8], 0) for v in mesh.vertices)


def index_bytes(mesh):
    return b''.join(struct.pack('<3H', *t) for t in mesh.triangles)


def verify_conversion(data, model, name, diffuse, sref):
    reader = Reader(data)
    root = reader.root()
    require(reader.header[14] == 0 and all(s[0] == 0 for s in reader.sections), 'output must be uncompressed and self-contained')
    require(len(root['Meshes']) == len(model.meshes), 'mesh count mismatch')
    require(len(root['Models']) == len(root['Skeletons']) == len(root['Materials']) == 1, 'static root binding mismatch')
    require(root['Models'][0]['Name'] == name and root['Models'][0]['InitialPlacement'] == TRANSFORM, 'model placement mismatch')
    skeleton = root['Skeletons'][0]
    require(root['Models'][0]['Skeleton'] is skeleton, 'model/skeleton reference mismatch')
    require(len(skeleton['Bones']) == 1, 'rigid skeleton mismatch')
    bone = skeleton['Bones'][0]
    require(bone['Name'] == model.bone and bone['ParentIndex'] == -1 and bone['Transform'] == TRANSFORM
            and bone['InverseWorldTransform'] == IDENTITY, 'static bone transform mismatch')
    require(not root['TrackGroups'] and not root['Animations'], 'unexpected animation records')
    records = []
    for i, (source, mesh) in enumerate(zip(model.meshes, root['Meshes'])):
        vd, topology = mesh['PrimaryVertexData'], mesh['PrimaryTopology']
        require(root['VertexDatas'][i] is vd and root['TriTopologies'][i] is topology
                and root['Models'][0]['MeshBindings'][i]['Mesh'] is mesh, 'mesh graph reference mismatch')
        require(mesh['Name'] == source.name, 'mesh name mismatch')
        require(len(mesh['BoneBindings']) == 1 and mesh['BoneBindings'][0]['BoneName'] == model.bone, 'bone binding mismatch')
        require(len(mesh['MaterialBindings']) == 1 and mesh['MaterialBindings'][0]['Material'] is root['Materials'][0], 'material binding mismatch')
        expected_v, expected_i = vertex_bytes(source), index_bytes(source)
        actual_v = b''.join(struct.pack('<15f', *v['Position'], *v['Normal'], *v['Tangent'],
                                      *v['Binormal'], *v['TextureCoordinates0']) for v in vd['Vertices'].items)
        actual_i = b''.join(struct.pack('<H', v['Int16'] & 65535) for v in topology['Indices16'])
        require(actual_v == expected_v, 'vertex stream differs from float32 BR2 source')
        require(actual_i == expected_i and not topology['Indices'], 'triangle indices/winding differ from BR2 source')
        require(len(topology['Groups']) == 1 and topology['Groups'][0].values == {
            'MaterialIndex': 0, 'TriFirst': 0, 'TriCount': len(source.triangles)}, 'material triangle group mismatch')
        records.append({'vertices': len(source.vertices), 'indices': 3*len(source.triangles),
                        'vertex_crc32': zlib.crc32(expected_v), 'index_crc32': zlib.crc32(expected_i)})
    extra = root['Materials'][0]['ExtendedData']
    require(extra['ShaderSet'] == 'BuildingShader' and extra['SkinBoneCount'] == 0, 'shader profile mismatch')
    textures = extra['ParameterSet1']
    require(textures['ParamDataT'][0]['String'] == diffuse and textures['ParamDataT'][4]['String'] == sref, 'texture parameter mismatch')
    return records


def check_dds(path):
    data = path.read_bytes()
    require(len(data) >= 128 and data[:4] == b'DDS ' and struct.unpack_from('<I', data, 4)[0] == 124, f'invalid DDS: {path}')
    height, width = struct.unpack_from('<II', data, 12)
    require(0 < width <= 16384 and 0 < height <= 16384, f'invalid DDS dimensions: {path}')
    mipmaps = max(1, struct.unpack_from('<I', data, 28)[0])
    require(mipmaps <= max(width, height).bit_length(), 'invalid DDS mip count')
    fourcc = data[84:88]
    require(struct.unpack_from('<I', data, 76)[0] == 32, 'invalid DDS pixel format header')
    require(struct.unpack_from('<I', data, 112)[0] == 0, 'cubemap/volume DDS is outside the static texture profile')
    flags = struct.unpack_from('<I', data, 80)[0]
    expected = 128
    if fourcc in (b'DXT1', b'DXT3', b'DXT5'):
        require(flags & 4, 'DDS FOURCC flag missing')
        for level in range(mipmaps):
            expected += max(1, (max(1,width>>level)+3)//4) * max(1, (max(1,height>>level)+3)//4) * (8 if fourcc == b'DXT1' else 16)
    else:
        require(fourcc == b'\0'*4 and struct.unpack_from('<I', data, 88)[0] == 32, 'only DXT1/3/5 or 32-bit DDS are supported')
        require(flags & 64 and not flags & 4, 'DDS RGB flags invalid')
        expected += sum(max(1,width>>i)*max(1,height>>i)*4 for i in range(mipmaps))
    require(len(data) == expected, f'DDS payload/mip size mismatch: {path}')
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def convert(source, output, diffuse, sref, *, name=None, probe=None, units_per_meter=1):
    source, output, diffuse, sref = map(Path, (source, output, diffuse, sref))
    name = asset_name(name or source.stem)
    for path in (diffuse, sref):
        require(path.suffix.lower() == '.dds', 'texture must be DDS')
        asset_name(path.stem)
    require(diffuse.name.lower() != sref.name.lower(), 'diffuse/SREF VFS names must differ')
    model = read(source)
    texture_data = {diffuse.name: check_dds(diffuse), sref.name: check_dds(sref)}
    graph = build_graph(model, name, diffuse.name, sref.name, units_per_meter)
    data = Writer().encode(graph)
    records = verify_conversion(data, model, name, diffuse.name, sref.name)
    independent = {'status': 'not run'}
    if probe:
        with tempfile.TemporaryDirectory(prefix='civ5-gr2-probe-') as temp:
            path = Path(temp)/f'{name}.gr2'; path.write_bytes(data)
            try:
                result = subprocess.run([str(Path(probe).resolve()), str(path)], capture_output=True, text=True, timeout=60)
            except subprocess.TimeoutExpired as e:
                raise FormatError('independent reader timed out after 60 seconds') from e
            require(result.returncode == 0, f'independent reader failed ({result.returncode}): {result.stderr[:500]}')
            try:
                report = json.loads(result.stdout)
            except ValueError as e:
                raise FormatError('independent reader returned invalid JSON') from e
            require(report.get('reader') == 'OpenGR2' and report.get('meshes') == records, 'independent vertex/index counts or CRCs differ from source')
            independent = {'status': 'passed', 'reader': 'OpenGR2', 'probe_sha256': sha(Path(probe).read_bytes())}
    asset = ET.Element('Asset')
    ET.SubElement(asset, 'Mesh', file=name+'.gr2', source='civ5-gr2')
    for filename in texture_data:
        ET.SubElement(asset, 'Texture', file=filename, source='civ5-gr2')
    ET.indent(asset, space='  ')
    wrapper = ET.tostring(asset, encoding='utf-8', xml_declaration=True)+b'\n'
    payloads = {name+'.gr2': data, name+'.fxsxml': wrapper, **texture_data}
    manifest = {'profile': PROFILE, 'name': name, 'source_br2_sha256': sha(source.read_bytes()),
                'structural_validation': 'passed', 'conversion': 'completed',
                'independent_reader': independent, 'native_game': {'status': 'unverified'},
                'units_per_meter': units_per_meter, 'meshes': records,
                'geometry_policy': 'float32 BR2 positions, normals, tangents, binormals, UVs and winding unchanged; UV third component zero; full root weights represented by rigid binding',
                'files': {n: sha(b) for n,b in payloads.items()}}
    payloads[name+'.conversion.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    # Refuse all conflicting writes before creating any output, including source aliases.
    require(output.resolve() != source.parent.resolve(), 'conversion output must be separate from approved sources')
    for filename, content in payloads.items():
        target = output/filename
        require(not target.exists() or target.read_bytes() == content, f'refusing to overwrite different output: {target}')
    output.mkdir(parents=True, exist_ok=True)
    for filename, content in payloads.items():
        target = output/filename
        if not target.exists():
            target.write_bytes(content)
    return manifest
