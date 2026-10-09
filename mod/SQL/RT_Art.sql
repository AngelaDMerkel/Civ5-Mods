-- Selected round-three art: Logistics B, Ministry portrait B, station A,
-- worker action B, Ministry painting A. Atlas cells retain native UI padding.
INSERT INTO IconTextureAtlases (Atlas, IconSize, Filename, IconsPerRow, IconsPerColumn)
VALUES ('RT_PORTRAITS', 32, 'RT_Portraits32.dds', 4, 1),
       ('RT_PORTRAITS', 45, 'RT_Portraits45.dds', 4, 1),
       ('RT_PORTRAITS', 64, 'RT_Portraits64.dds', 4, 1),
       ('RT_PORTRAITS', 80, 'RT_Portraits80.dds', 4, 1),
       ('RT_PORTRAITS', 128, 'RT_Portraits128.dds', 4, 1),
       ('RT_PORTRAITS', 214, 'RT_Portraits214.dds', 4, 1),
       ('RT_PORTRAITS', 256, 'RT_Portraits256.dds', 4, 1),
       ('RT_CARAVANSARY_ACTION', 32, 'RT_CaravansaryAction32.dds', 1, 1),
       ('RT_CARAVANSARY_ACTION', 45, 'RT_CaravansaryAction45.dds', 1, 1),
       ('RT_CARAVANSARY_ACTION', 64, 'RT_CaravansaryAction64.dds', 1, 1);

UPDATE Technologies SET IconAtlas = 'RT_PORTRAITS', PortraitIndex = 0
WHERE Type = 'TECH_RT_CARAVAN_LOGISTICS';
UPDATE Buildings SET IconAtlas = 'RT_PORTRAITS', PortraitIndex = 1,
    WonderSplashImage = 'RT_MinistryOfCoin_Wonder.dds', WonderSplashAnchor = 'R,T'
WHERE Type = 'BUILDING_CARAVANSARY';
UPDATE Improvements SET IconAtlas = 'RT_PORTRAITS', PortraitIndex = 2
WHERE Type = 'IMPROVEMENT_RT_RELIEF_STATION';
UPDATE Builds SET IconAtlas = 'RT_CARAVANSARY_ACTION', IconIndex = 0
WHERE Type = 'BUILD_RT_RELIEF_STATION';
