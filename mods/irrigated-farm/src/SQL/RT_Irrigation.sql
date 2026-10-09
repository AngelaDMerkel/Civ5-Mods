-- Custom worker orders enforce the local building and live water-network gates.
-- No Unit_Builds row: stock BNW cannot veto a native build by these conditions.
INSERT INTO BuildingClasses (Type, DefaultBuilding, Description)
VALUES ('BUILDINGCLASS_RT_IRRIGATION_WORKS', 'BUILDING_RT_IRRIGATION_WORKS', 'TXT_KEY_RT_IRRIGATION_WORKS');

INSERT INTO Buildings
    (Type, BuildingClass, Description, Civilopedia, Strategy, Help, Cost,
     GoldMaintenance, PrereqTech, ArtDefineTag, PortraitIndex, IconAtlas)
SELECT 'BUILDING_RT_IRRIGATION_WORKS', 'BUILDINGCLASS_RT_IRRIGATION_WORKS',
       'TXT_KEY_RT_IRRIGATION_WORKS', 'TXT_KEY_RT_IRRIGATION_WORKS_PEDIA',
       'TXT_KEY_RT_IRRIGATION_WORKS_STRATEGY', 'TXT_KEY_RT_IRRIGATION_WORKS_HELP',
       100, 1, 'TECH_ENGINEERING', ArtDefineTag, PortraitIndex, IconAtlas
FROM Buildings WHERE Type = 'BUILDING_AQUEDUCT';

INSERT INTO Building_Flavors (BuildingType, FlavorType, Flavor)
VALUES ('BUILDING_RT_IRRIGATION_WORKS', 'FLAVOR_GROWTH', 20);

-- Two native improvement states make yields visible to city assignment and
-- save/reload without persistent extra-yield deltas or artificial freshwater.
INSERT INTO Improvements
    (Type, Description, Civilopedia, Help, ArtDefineTag, RequiresFlatlands,
     DestroyedWhenPillaged, PillageGold, PortraitIndex, IconAtlas)
SELECT 'IMPROVEMENT_RT_IRRIGATED_FARM', 'TXT_KEY_RT_IRRIGATED_FARM',
       'TXT_KEY_RT_IRRIGATED_FARM_PEDIA', 'TXT_KEY_RT_IRRIGATED_FARM_HELP',
       ArtDefineTag, 1, 0, PillageGold, PortraitIndex, IconAtlas
FROM Improvements WHERE Type = 'IMPROVEMENT_FARM';
INSERT INTO Improvements
    (Type, Description, Civilopedia, Help, ArtDefineTag, RequiresFlatlands,
     DestroyedWhenPillaged, PillageGold, PortraitIndex, IconAtlas)
SELECT 'IMPROVEMENT_RT_DRY_FARM', 'TXT_KEY_RT_DRY_FARM', Civilopedia, Help,
       ArtDefineTag, RequiresFlatlands, DestroyedWhenPillaged, PillageGold, PortraitIndex, IconAtlas
FROM Improvements WHERE Type = 'IMPROVEMENT_RT_IRRIGATED_FARM';

INSERT INTO Improvement_ValidTerrains (ImprovementType, TerrainType)
SELECT Type, 'TERRAIN_DESERT' FROM Improvements
WHERE Type IN ('IMPROVEMENT_RT_IRRIGATED_FARM', 'IMPROVEMENT_RT_DRY_FARM');
INSERT INTO Improvement_Yields (ImprovementType, YieldType, Yield) VALUES
('IMPROVEMENT_RT_IRRIGATED_FARM', 'YIELD_FOOD', 3),
('IMPROVEMENT_RT_DRY_FARM', 'YIELD_FOOD', 1);

-- Preserve ordinary farm resource access and fresh/dry technology progression.
INSERT INTO Improvement_ResourceTypes
    (ImprovementType, ResourceType, ResourceMakesValid, ResourceTrade)
SELECT Type, 'RESOURCE_WHEAT', 1, 1 FROM Improvements
WHERE Type IN ('IMPROVEMENT_RT_IRRIGATED_FARM', 'IMPROVEMENT_RT_DRY_FARM');
INSERT INTO Improvement_TechFreshWaterYieldChanges (ImprovementType, TechType, YieldType, Yield)
SELECT i.Type, f.TechType, f.YieldType, f.Yield FROM Improvements i
CROSS JOIN Improvement_TechFreshWaterYieldChanges f
WHERE i.Type IN ('IMPROVEMENT_RT_IRRIGATED_FARM', 'IMPROVEMENT_RT_DRY_FARM') AND f.ImprovementType = 'IMPROVEMENT_FARM';
INSERT INTO Improvement_TechNoFreshWaterYieldChanges (ImprovementType, TechType, YieldType, Yield)
SELECT i.Type, f.TechType, f.YieldType, f.Yield FROM Improvements i
CROSS JOIN Improvement_TechNoFreshWaterYieldChanges f
WHERE i.Type IN ('IMPROVEMENT_RT_IRRIGATED_FARM', 'IMPROVEMENT_RT_DRY_FARM') AND f.ImprovementType = 'IMPROVEMENT_FARM';
INSERT INTO Improvement_TechYieldChanges (ImprovementType, TechType, YieldType, Yield)
SELECT i.Type, f.TechType, f.YieldType, f.Yield FROM Improvements i
CROSS JOIN Improvement_TechYieldChanges f
WHERE i.Type IN ('IMPROVEMENT_RT_IRRIGATED_FARM', 'IMPROVEMENT_RT_DRY_FARM') AND f.ImprovementType = 'IMPROVEMENT_FARM';

INSERT INTO Builds
    (Type, Description, Help, Time, PrereqTech, ImprovementType,
     EntityEvent, IconIndex, IconAtlas, OrderPriority)
SELECT 'BUILD_RT_IRRIGATED_FARM', 'TXT_KEY_RT_BUILD_IRRIGATED_FARM',
       'TXT_KEY_RT_IRRIGATED_FARM_HELP', Time, 'TECH_ENGINEERING',
       'IMPROVEMENT_RT_DRY_FARM', EntityEvent, IconIndex, IconAtlas, OrderPriority
FROM Builds WHERE Type = 'BUILD_FARM';
