-- Resource access outside borders is maintained by RO_Outposts. Once a city
-- acquires the tile, ResourceTrade lets the native engine take over accounting.
INSERT INTO Improvements
    (Type, Description, Civilopedia, Help, ArtDefineTag, OutsideBorders,
     BuildableOnResources, DestroyedWhenPillaged, DefenseModifier,
     PillageGold, PortraitIndex, IconAtlas)
SELECT 'IMPROVEMENT_RT_RESOURCE_OUTPOST', 'TXT_KEY_RT_RESOURCE_OUTPOST',
       'TXT_KEY_RT_RESOURCE_OUTPOST_PEDIA', 'TXT_KEY_RT_RESOURCE_OUTPOST_HELP',
       ArtDefineTag, 1, 0, 0, DefenseModifier, PillageGold, PortraitIndex, IconAtlas
FROM Improvements WHERE Type = 'IMPROVEMENT_FORT';

INSERT INTO Improvement_ResourceTypes (ImprovementType, ResourceType, ResourceMakesValid, ResourceTrade)
SELECT DISTINCT 'IMPROVEMENT_RT_RESOURCE_OUTPOST', r.Type, 1, 1
FROM Resources r JOIN Improvement_ResourceTypes ir ON ir.ResourceType = r.Type
WHERE r.ResourceClassType IN ('RESOURCECLASS_RUSH', 'RESOURCECLASS_MODERN', 'RESOURCECLASS_LUXURY')
  AND ir.ResourceTrade = 1 AND ir.ImprovementType IN
      ('IMPROVEMENT_MINE', 'IMPROVEMENT_QUARRY', 'IMPROVEMENT_PASTURE',
       'IMPROVEMENT_CAMP', 'IMPROVEMENT_PLANTATION', 'IMPROVEMENT_WELL');

INSERT INTO Improvement_ValidFeatures (ImprovementType, FeatureType)
SELECT 'IMPROVEMENT_RT_RESOURCE_OUTPOST', FeatureType FROM Improvement_ValidFeatures
WHERE ImprovementType = 'IMPROVEMENT_FORT';

INSERT INTO Builds
    (Type, Description, Help, Time, PrereqTech, ImprovementType, EntityEvent, IconIndex, IconAtlas, OrderPriority)
SELECT 'BUILD_RT_RESOURCE_OUTPOST', 'TXT_KEY_RT_BUILD_RESOURCE_OUTPOST',
       'TXT_KEY_RT_RESOURCE_OUTPOST_HELP', Time, 'TECH_ENGINEERING',
       'IMPROVEMENT_RT_RESOURCE_OUTPOST', EntityEvent, IconIndex, IconAtlas, OrderPriority
FROM Builds WHERE Type = 'BUILD_FORT';

INSERT INTO BuildFeatures (BuildType, FeatureType, PrereqTech, Time, Production, Cost, Remove)
SELECT 'BUILD_RT_RESOURCE_OUTPOST', FeatureType, PrereqTech, Time, Production, Cost, Remove
FROM BuildFeatures WHERE BuildType = 'BUILD_FORT';
-- Deliberately no Unit_Builds entry: the custom action enforces neutral land,
-- resource visibility and the resource's ordinary extraction technology.
