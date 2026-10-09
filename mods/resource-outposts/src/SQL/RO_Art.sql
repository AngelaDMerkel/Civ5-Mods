-- User-selected Guarded storehouse: emblem B and construction glyph B.
-- One-cell atlases are also used directly by the additive management UI.
INSERT INTO IconTextureAtlases (Atlas, IconSize, Filename, IconsPerRow, IconsPerColumn)
VALUES ('RO_OUTPOST_PORTRAITS', 32, 'RO_OutpostPortrait32.dds', 1, 1),
       ('RO_OUTPOST_PORTRAITS', 45, 'RO_OutpostPortrait45.dds', 1, 1),
       ('RO_OUTPOST_PORTRAITS', 64, 'RO_OutpostPortrait64.dds', 1, 1),
       ('RO_OUTPOST_PORTRAITS', 80, 'RO_OutpostPortrait80.dds', 1, 1),
       ('RO_OUTPOST_PORTRAITS', 128, 'RO_OutpostPortrait128.dds', 1, 1),
       ('RO_OUTPOST_PORTRAITS', 214, 'RO_OutpostPortrait214.dds', 1, 1),
       ('RO_OUTPOST_PORTRAITS', 256, 'RO_OutpostPortrait256.dds', 1, 1),
       ('RO_OUTPOST_ACTION', 32, 'RO_OutpostAction32.dds', 1, 1),
       ('RO_OUTPOST_ACTION', 45, 'RO_OutpostAction45.dds', 1, 1),
       ('RO_OUTPOST_ACTION', 64, 'RO_OutpostAction64.dds', 1, 1);

UPDATE Improvements SET IconAtlas = 'RO_OUTPOST_PORTRAITS', PortraitIndex = 0
WHERE Type = 'IMPROVEMENT_RT_RESOURCE_OUTPOST';
UPDATE Builds SET IconAtlas = 'RO_OUTPOST_ACTION', IconIndex = 0
WHERE Type = 'BUILD_RT_RESOURCE_OUTPOST';

-- A distinct art tag lets the strategic icon differ from the stock Fort.
-- Retain all native Fort era/state model rows until approved meshes are ready
-- for native integration. This changes neither the Fort nor the outpost rules.
INSERT INTO ArtDefine_LandmarkTypes (Type, LandmarkType, FriendlyName)
SELECT 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST', LandmarkType, 'Resource Outpost'
FROM ArtDefine_LandmarkTypes WHERE Type = 'ART_DEF_IMPROVEMENT_FORT';
INSERT INTO ArtDefine_Landmarks
    (Era, State, Scale, ImprovementType, LayoutHandler, ResourceType, Model, TerrainContour, Tech)
SELECT Era, State, Scale, 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST',
       LayoutHandler, ResourceType, Model, TerrainContour, Tech
FROM ArtDefine_Landmarks WHERE ImprovementType = 'ART_DEF_IMPROVEMENT_FORT';
INSERT INTO ArtDefine_StrategicView (StrategicViewType, TileType, Asset)
VALUES ('ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST', 'Improvement', 'RO_OutpostStrategic.dds');
UPDATE Improvements SET ArtDefineTag = 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST'
WHERE Type = 'IMPROVEMENT_RT_RESOURCE_OUTPOST';
