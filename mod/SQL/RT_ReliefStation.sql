-- The field Caravansary retains the alpha's internal relief-station identifiers.
-- Construction is handled by RT_Construction: stock BNW has no PlayerCanBuild
-- veto or building prerequisite for a worker action. Do not add Unit_Builds rows
-- for this action, which would bypass the Ministry of Coin requirement.
-- Reuse the fort's art and build animation; do not grant its defensive bonus.
INSERT INTO Improvements
    (Type, Description, Civilopedia, Help, ArtDefineTag, OutsideBorders,
     HillsMakesValid, DestroyedWhenPillaged, BuildableOnResources,
     DefenseModifier, PillageGold, PortraitIndex, IconAtlas)
VALUES
    ('IMPROVEMENT_RT_RELIEF_STATION', 'TXT_KEY_RT_RELIEF_STATION',
     'TXT_KEY_RT_RELIEF_STATION_PEDIA', 'TXT_KEY_RT_RELIEF_STATION_HELP',
     'ART_DEF_IMPROVEMENT_FORT', 1, 1, 0, 0, 0, 10, 24, 'TERRAIN_ATLAS');

INSERT INTO Improvement_ValidTerrains (ImprovementType, TerrainType)
SELECT 'IMPROVEMENT_RT_RELIEF_STATION', Type FROM Terrains
WHERE Type IN ('TERRAIN_GRASS', 'TERRAIN_PLAINS', 'TERRAIN_DESERT', 'TERRAIN_TUNDRA', 'TERRAIN_SNOW');

INSERT INTO Improvement_ValidFeatures (ImprovementType, FeatureType)
SELECT 'IMPROVEMENT_RT_RELIEF_STATION', Type FROM Features
WHERE Type IN ('FEATURE_FOREST', 'FEATURE_JUNGLE');

INSERT INTO Builds
    (Type, Description, Help, Time, PrereqTech, ImprovementType,
     EntityEvent, IconIndex, IconAtlas, OrderPriority)
SELECT 'BUILD_RT_RELIEF_STATION', 'TXT_KEY_RT_BUILD_RELIEF_STATION',
       'TXT_KEY_RT_RELIEF_STATION_HELP', Time, 'TECH_ENGINEERING',
       'IMPROVEMENT_RT_RELIEF_STATION', EntityEvent, IconIndex, IconAtlas, OrderPriority
FROM Builds WHERE Type = 'BUILD_FORT';

-- Match fort construction in features, preserving forest/jungle rather than
-- silently removing them. Include the engine's feature work-time prerequisites.
INSERT INTO BuildFeatures (BuildType, FeatureType, PrereqTech, Time, Production, Cost, Remove)
SELECT 'BUILD_RT_RELIEF_STATION', FeatureType, PrereqTech, Time, Production, Cost, Remove
FROM BuildFeatures WHERE BuildType = 'BUILD_FORT';
