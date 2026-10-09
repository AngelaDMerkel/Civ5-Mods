"""Measured GR2 field interfaces. No stock art or object graph. See RESEARCH.md.
Empty animation field types preserve the root contract; animation export is unsupported.
"""
from .format import Definition, Member, Node

SCHEMA = {
    'String': [
        ('String', 8, None, 0),
    ],
    'ParameterSet': [
        ('ParamBlock', 8, None, 0),
        ('ParamCount', 19, None, 0),
        ('ParamNames', 3, 'String', 0),
        ('ParamTypes', 3, 'Int32', 0),
        ('ParamUsage', 3, 'Int32', 0),
        ('ParamRegs', 3, 'Int32', 0),
        ('ParamSize', 3, 'Int32', 0),
        ('ParamSemantics', 3, 'Int32', 0),
        ('ParamStoreIdx', 3, 'Int32', 0),
        ('ParamDataF', 3, 'Real32', 0),
        ('ParamDataI', 3, 'Int32', 0),
        ('ParamDataT', 3, 'String', 0),
        ('ParamActive', 19, None, 0),
        ('ParamFlags', 3, 'Int32', 0),
    ],
    'Int32': [
        ('Int32', 19, None, 0),
    ],
    'Real32': [
        ('Real32', 10, None, 0),
    ],
    'BuildingMaterial': [
        ('ShaderSet', 8, None, 0),
        ('FallbackMtl', 3, 'String', 0),
        ('UseFallbackMtl', 19, None, 0),
        ('AlphaMode', 19, None, 0),
        ('ZMode', 19, None, 0),
        ('AlphaRef', 19, None, 0),
        ('SkinBoneCount', 19, None, 0),
        ('Reflections', 19, None, 0),
        ('Shadows', 19, None, 0),
        ('AlphaSort', 19, None, 0),
        ('Version', 19, None, 0),
        ('Invisible', 19, None, 0),
        ('Z-Fail', 19, None, 0),
        ('typeName', 8, None, 0),
        ('ParameterSetCount', 19, None, 0),
        ('ParameterSet0', 2, 'ParameterSet', 0),
        ('ParameterSet1', 2, 'ParameterSet', 0),
    ],
    'Vertex': [
        ('Position', 10, None, 3),
        ('Normal', 10, None, 3),
        ('Tangent', 10, None, 3),
        ('Binormal', 10, None, 3),
        ('TextureCoordinates0', 10, None, 3),
    ],
    'Root': [
        ('ArtToolInfo', 2, 'ArtTool', 0),
        ('ExporterInfo', 2, 'Exporter', 0),
        ('FromFileName', 8, None, 0),
        ('Textures', 4, 'Texture', 0),
        ('Materials', 4, 'Material', 0),
        ('Skeletons', 4, 'Skeleton', 0),
        ('VertexDatas', 4, 'VertexData', 0),
        ('TriTopologies', 4, 'Topology', 0),
        ('Meshes', 4, 'Mesh', 0),
        ('Models', 4, 'Model', 0),
        ('TrackGroups', 4, 'TrackGroup', 0),
        ('Animations', 4, 'Animation', 0),
        ('ExtendedData', 5, None, 0),
    ],
    'ArtTool': [
        ('FromArtToolName', 8, None, 0),
        ('ArtToolMajorRevision', 19, None, 0),
        ('ArtToolMinorRevision', 19, None, 0),
        ('ArtToolPointerSize', 19, None, 0),
        ('UnitsPerMeter', 10, None, 0),
        ('Origin', 10, None, 3),
        ('RightVector', 10, None, 3),
        ('UpVector', 10, None, 3),
        ('BackVector', 10, None, 3),
        ('ExtendedData', 5, None, 0),
    ],
    'Exporter': [
        ('ExporterName', 8, None, 0),
        ('ExporterMajorRevision', 19, None, 0),
        ('ExporterMinorRevision', 19, None, 0),
        ('ExporterCustomization', 19, None, 0),
        ('ExporterBuildNumber', 19, None, 0),
        ('ExtendedData', 5, None, 0),
    ],
    'Texture': [
        ('FromFileName', 8, None, 0),
        ('TextureType', 19, None, 0),
        ('Width', 19, None, 0),
        ('Height', 19, None, 0),
        ('Encoding', 19, None, 0),
        ('SubFormat', 19, None, 0),
        ('Layout', 1, 'PixelLayout', 0),
        ('Images', 3, 'Image', 0),
        ('ExtendedData', 5, None, 0),
    ],
    'PixelLayout': [
        ('BytesPerPixel', 19, None, 0),
        ('ShiftForComponent', 19, None, 4),
        ('BitsForComponent', 19, None, 4),
    ],
    'Image': [
        ('MIPLevels', 3, 'MIPLevel', 0),
    ],
    'MIPLevel': [
        ('Stride', 19, None, 0),
        ('PixelBytes', 3, 'UInt8', 0),
    ],
    'UInt8': [
        ('UInt8', 12, None, 0),
    ],
    'Material': [
        ('Name', 8, None, 0),
        ('Maps', 3, 'MaterialMap', 0),
        ('Texture', 2, 'Texture', 0),
        ('ExtendedData', 5, None, 0),
    ],
    'MaterialMap': [
        ('Usage', 8, None, 0),
        ('Map', 2, 'Material', 0),
    ],
    'Skeleton': [
        ('Name', 8, None, 0),
        ('Bones', 3, 'Bone', 0),
        ('LODType', 19, None, 0),
        ('ExtendedData', 5, None, 0),
    ],
    'Bone': [
        ('Name', 8, None, 0),
        ('ParentIndex', 19, None, 0),
        ('Transform', 9, None, 0),
        ('InverseWorldTransform', 10, None, 16),
        ('LODError', 10, None, 0),
        ('ExtendedData', 5, None, 0),
    ],
    'VertexData': [
        ('Vertices', 7, None, 0),
        ('VertexComponentNames', 3, 'ComponentName', 0),
        ('VertexAnnotationSets', 3, 'VertexAnnotation', 0),
    ],
    'ComponentName': [
        ('String', 8, None, 0),
    ],
    'VertexAnnotation': [
        ('Name', 8, None, 0),
        ('VertexAnnotations', 7, None, 0),
        ('IndicesMapFromVertexToAnnotation', 19, None, 0),
        ('VertexAnnotationIndices', 3, 'Index32', 0),
    ],
    'Index32': [
        ('Int32', 19, None, 0),
    ],
    'Topology': [
        ('Groups', 3, 'Group', 0),
        ('Indices', 3, 'Index32', 0),
        ('Indices16', 3, 'Index16', 0),
        ('VertexToVertexMap', 3, 'Index32', 0),
        ('VertexToTriangleMap', 3, 'Index32', 0),
        ('SideToNeighborMap', 3, 'Index32', 0),
        ('BonesForTriangle', 3, 'Index32', 0),
        ('TriangleToBoneIndices', 3, 'Index32', 0),
        ('TriAnnotationSets', 3, 'TriAnnotation', 0),
    ],
    'Group': [
        ('MaterialIndex', 19, None, 0),
        ('TriFirst', 19, None, 0),
        ('TriCount', 19, None, 0),
    ],
    'Index16': [
        ('Int16', 15, None, 0),
    ],
    'TriAnnotation': [
        ('Name', 8, None, 0),
        ('TriAnnotations', 7, None, 0),
        ('IndicesMapFromTriToAnnotation', 19, None, 0),
        ('TriAnnotationIndices', 3, 'Index32', 0),
    ],
    'Mesh': [
        ('Name', 8, None, 0),
        ('PrimaryVertexData', 2, 'VertexData', 0),
        ('MorphTargets', 3, 'MorphTarget', 0),
        ('PrimaryTopology', 2, 'Topology', 0),
        ('MaterialBindings', 3, 'MaterialBinding', 0),
        ('BoneBindings', 3, 'BoneBinding', 0),
        ('ExtendedData', 5, None, 0),
    ],
    'MorphTarget': [
        ('ScalarName', 8, None, 0),
        ('VertexData', 2, 'VertexData', 0),
        ('DataIsDeltas', 19, None, 0),
    ],
    'MaterialBinding': [
        ('Material', 2, 'Material', 0),
    ],
    'BoneBinding': [
        ('BoneName', 8, None, 0),
        ('OBBMin', 10, None, 3),
        ('OBBMax', 10, None, 3),
        ('TriangleIndices', 3, 'Index32', 0),
    ],
    'Model': [
        ('Name', 8, None, 0),
        ('Skeleton', 2, 'Skeleton', 0),
        ('InitialPlacement', 9, None, 0),
        ('MeshBindings', 3, 'MeshBinding', 0),
        ('ExtendedData', 5, None, 0),
    ],
    'MeshBinding': [
        ('Mesh', 2, 'Mesh', 0),
    ],
    'TrackGroup': [
        ('Name', 8, None, 0),
        ('VectorTracks', 3, 'VectorTrack', 0),
        ('TransformTracks', 3, 'TransformTrack', 0),
        ('TransformLODErrors', 3, 'LODError', 0),
        ('TextTracks', 3, 'TextTrack', 0),
        ('InitialPlacement', 9, None, 0),
        ('AccumulationFlags', 19, None, 0),
        ('LoopTranslation', 10, None, 3),
        ('PeriodicLoop', 2, 'PeriodicLoop', 0),
        ('RootMotion', 2, 'TransformTrack', 0),
        ('ExtendedData', 5, None, 0),
    ],
    'VectorTrack': [
        ('Name', 8, None, 0),
        ('TrackKey', 20, None, 0),
        ('Dimension', 19, None, 0),
        ('ValueCurve', 1, 'Curve', 0),
    ],
    'Curve': [
        ('CurveData', 5, None, 0),
    ],
    'TransformTrack': [
        ('Name', 8, None, 0),
        ('Flags', 19, None, 0),
        ('OrientationCurve', 1, 'Curve', 0),
        ('PositionCurve', 1, 'Curve', 0),
        ('ScaleShearCurve', 1, 'Curve', 0),
    ],
    'LODError': [
        ('Real32', 10, None, 0),
    ],
    'TextTrack': [
        ('Name', 8, None, 0),
        ('Entries', 3, 'TextEntry', 0),
    ],
    'TextEntry': [
        ('TimeStamp', 10, None, 0),
        ('Text', 8, None, 0),
    ],
    'PeriodicLoop': [
        ('Radius', 10, None, 0),
        ('dAngle', 10, None, 0),
        ('dZ', 10, None, 0),
        ('BasisX', 10, None, 3),
        ('BasisY', 10, None, 3),
        ('Axis', 10, None, 3),
    ],
    'Animation': [
        ('Name', 8, None, 0),
        ('Duration', 10, None, 0),
        ('TimeStep', 10, None, 0),
        ('Oversampling', 10, None, 0),
        ('TrackGroups', 4, 'TrackGroup', 0),
    ],
}

DEFINITIONS = {name: Definition() for name in SCHEMA}
for name, fields in SCHEMA.items():
    DEFINITIONS[name].members = [Member(key, kind, DEFINITIONS.get(sub), width)
                                 for key, kind, sub, width in fields]

def node(kind, **values):
    return Node(DEFINITIONS[kind], values)
