-- Claimant-era variants share gameplay data. The legacy improvement and build
-- remain the public entry; GraphicalOnly prevents duplicate Civilopedia entries.
CREATE TABLE RO_OutpostEras (
    EraType TEXT PRIMARY KEY,
    ImprovementType TEXT NOT NULL UNIQUE,
    ArtDefineTag TEXT NOT NULL UNIQUE,
    FallbackEra TEXT NOT NULL,
    ModelStem TEXT NOT NULL UNIQUE
);
INSERT INTO RO_OutpostEras (EraType, ImprovementType, ArtDefineTag, FallbackEra, ModelStem)
VALUES
    ('ERA_ANCIENT', 'IMPROVEMENT_RO_OUTPOST_ANCIENT', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_ANCIENT', 'Ancient', 'RO_Ancient'),
    ('ERA_CLASSICAL', 'IMPROVEMENT_RO_OUTPOST_CLASSICAL', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_CLASSICAL', 'Ancient', 'RO_Classical'),
    ('ERA_MEDIEVAL', 'IMPROVEMENT_RO_OUTPOST_MEDIEVAL', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_MEDIEVAL', 'Ancient', 'RO_Medieval'),
    ('ERA_RENAISSANCE', 'IMPROVEMENT_RO_OUTPOST_RENAISSANCE', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_RENAISSANCE', 'Ancient', 'RO_Renaissance'),
    ('ERA_INDUSTRIAL', 'IMPROVEMENT_RO_OUTPOST_INDUSTRIAL', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_INDUSTRIAL', 'Industrial', 'RO_Industrial'),
    ('ERA_MODERN', 'IMPROVEMENT_RO_OUTPOST_MODERN', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_MODERN', 'Industrial', 'RO_Modern'),
    ('ERA_POSTMODERN', 'IMPROVEMENT_RO_OUTPOST_POSTMODERN', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_POSTMODERN', 'Industrial', 'RO_Atomic'),
    ('ERA_FUTURE', 'IMPROVEMENT_RO_OUTPOST_FUTURE', 'ART_DEF_IMPROVEMENT_RO_OUTPOST_FUTURE', 'Industrial', 'RO_Information');

-- Copy every stock BNW improvement column except its assigned ID.
INSERT INTO Improvements (
    "Type", "Description", "Civilopedia", "Help", "ArtDefineTag",
    "WorldSoundscapeAudioScript", "ImprovementPillage", "ImprovementUpgrade", "SpecificCivRequired", "CivilizationType",
    "HillsMakesValid", "FreshWaterMakesValid", "RiverSideMakesValid", "NoFreshWater", "RequiresFlatlands",
    "RequiresFlatlandsOrFreshWater", "RequiresFeature", "RequiresImprovement", "RemovesResource", "PromptWhenComplete",
    "Coastal", "Water", "DestroyedWhenPillaged", "DisplacePillager", "BuildableOnResources",
    "BarbarianCamp", "Goody", "Permanent", "OutsideBorders", "InAdjacentFriendly",
    "IgnoreOwnership", "OnlyCityStateTerritory", "GraphicalOnly", "CreatedByGreatPerson", "NoTwoAdjacent",
    "AdjacentLuxury", "AllowsWalkWater", "CultureAdjacentSameType", "TilesPerGoody", "GoodyRange",
    "FeatureGrowth", "UpgradeTime", "RiverSideUpgradeMod", "CoastalLandUpgradeMod", "HillsUpgradeMod",
    "FreshWaterUpgradeMod", "DefenseModifier", "NearbyEnemyDamage", "PillageGold", "ResourceExtractionMod",
    "LuxuryCopiesSiphonedFromMinor", "GoldMaintenance", "CultureBombRadius", "RequiresXAdjacentLand", "PortraitIndex",
    "IconAtlas")
SELECT
    e.ImprovementType, b."Description", b."Civilopedia", b."Help", e.ArtDefineTag,
    b."WorldSoundscapeAudioScript", b."ImprovementPillage", b."ImprovementUpgrade", b."SpecificCivRequired", b."CivilizationType",
    b."HillsMakesValid", b."FreshWaterMakesValid", b."RiverSideMakesValid", b."NoFreshWater", b."RequiresFlatlands",
    b."RequiresFlatlandsOrFreshWater", b."RequiresFeature", b."RequiresImprovement", b."RemovesResource", b."PromptWhenComplete",
    b."Coastal", b."Water", b."DestroyedWhenPillaged", b."DisplacePillager", b."BuildableOnResources",
    b."BarbarianCamp", b."Goody", b."Permanent", b."OutsideBorders", b."InAdjacentFriendly",
    b."IgnoreOwnership", b."OnlyCityStateTerritory", 1, b."CreatedByGreatPerson", b."NoTwoAdjacent",
    b."AdjacentLuxury", b."AllowsWalkWater", b."CultureAdjacentSameType", b."TilesPerGoody", b."GoodyRange",
    b."FeatureGrowth", b."UpgradeTime", b."RiverSideUpgradeMod", b."CoastalLandUpgradeMod", b."HillsUpgradeMod",
    b."FreshWaterUpgradeMod", b."DefenseModifier", b."NearbyEnemyDamage", b."PillageGold", b."ResourceExtractionMod",
    b."LuxuryCopiesSiphonedFromMinor", b."GoldMaintenance", b."CultureBombRadius", b."RequiresXAdjacentLand", b."PortraitIndex",
    b."IconAtlas"
FROM Improvements b CROSS JOIN RO_OutpostEras e
WHERE b.Type = 'IMPROVEMENT_RT_RESOURCE_OUTPOST';

INSERT INTO Improvement_ResourceTypes
    (ImprovementType, ResourceType, ResourceMakesValid, ResourceTrade, DiscoveryRand, QuantityRequirement)
SELECT e.ImprovementType, r.ResourceType, r.ResourceMakesValid, r.ResourceTrade, r.DiscoveryRand, r.QuantityRequirement
FROM Improvement_ResourceTypes r CROSS JOIN RO_OutpostEras e
WHERE r.ImprovementType = 'IMPROVEMENT_RT_RESOURCE_OUTPOST';
INSERT INTO Improvement_ValidFeatures (ImprovementType, FeatureType)
SELECT e.ImprovementType, f.FeatureType
FROM Improvement_ValidFeatures f CROSS JOIN RO_OutpostEras e
WHERE f.ImprovementType = 'IMPROVEMENT_RT_RESOURCE_OUTPOST';

INSERT INTO ArtDefine_LandmarkTypes (Type, LandmarkType, FriendlyName)
SELECT ArtDefineTag, 'Improvement', 'Resource Outpost ' || ModelStem FROM RO_OutpostEras;
-- Any prevents territorial/world-era art selection from overriding our stage.
-- Native reviewed models retain their approved geometry/textures at scale 6.
-- FallbackEra remains compatibility metadata; it no longer selects stock art.
INSERT INTO ArtDefine_Landmarks
    (Era, State, Scale, ImprovementType, LayoutHandler, ResourceType, Model, TerrainContour, Tech)
SELECT 'Any', s.State, 6, e.ArtDefineTag, 'SNAPSHOT', 'ART_DEF_RESOURCE_ALL',
       e.ModelStem || s.Suffix || '.fxsxml', 0, NULL
FROM RO_OutpostEras e CROSS JOIN (
    SELECT 'Constructed' AS State, '' AS Suffix
    UNION ALL SELECT 'UnderConstruction', '_UnderConstruction'
    UNION ALL SELECT 'Pillaged', '_Pillaged'
) s;
INSERT INTO ArtDefine_StrategicView (StrategicViewType, TileType, Asset)
SELECT ArtDefineTag, 'Improvement', 'RO_OutpostStrategic.dds' FROM RO_OutpostEras;
