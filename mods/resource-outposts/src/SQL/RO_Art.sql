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

-- The public build uses shared Ancient scaffolding. Completed sites immediately
-- select their claimant-era variant through RO_Eras; build progress is unchanged.
INSERT INTO ArtDefine_LandmarkTypes (Type, LandmarkType, FriendlyName)
VALUES ('ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST', 'Improvement', 'Resource Outpost');
INSERT INTO ArtDefine_Landmarks
    (Era, State, Scale, ImprovementType, LayoutHandler, ResourceType, Model, TerrainContour, Tech)
VALUES
    ('Any', 'Constructed', 6, 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST', 'SNAPSHOT', 'ART_DEF_RESOURCE_ALL', 'RO_Ancient.fxsxml', 0, NULL),
    ('Any', 'UnderConstruction', 6, 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST', 'SNAPSHOT', 'ART_DEF_RESOURCE_ALL', 'RO_Ancient_UnderConstruction.fxsxml', 0, NULL),
    ('Any', 'Pillaged', 6, 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST', 'SNAPSHOT', 'ART_DEF_RESOURCE_ALL', 'RO_Ancient_Pillaged.fxsxml', 0, NULL);
INSERT INTO ArtDefine_StrategicView (StrategicViewType, TileType, Asset)
VALUES ('ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST', 'Improvement', 'RO_OutpostStrategic.dds');
UPDATE Improvements SET ArtDefineTag = 'ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST'
WHERE Type = 'IMPROVEMENT_RT_RESOURCE_OUTPOST';
