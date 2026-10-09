-- Optional later-game land trader. The ordinary Caravan remains trainable;
-- there is no upgrade-chain replacement or obsolescence change.
-- Reuse the Caravan's native art/flag for this alpha;
-- native trade missions remain disabled, as for both original trade units.
INSERT INTO UnitClasses (Type, Description, DefaultUnit)
VALUES ('UNITCLASS_RT_MOTORIZED_CARAVAN', 'TXT_KEY_RT_MOTORIZED_CARAVAN', 'UNIT_RT_MOTORIZED_CARAVAN');

INSERT INTO Units
    (Type, Description, Civilopedia, Strategy, Help, Class, Cost, Moves,
     Immobile, BaseSightRange, Domain, CivilianAttackPriority, DefaultUnitAI,
     MilitarySupport, MilitaryProduction, Mechanized, PrereqTech, HurryCostModifier,
     AdvancedStartCost, MinAreaSize, NukeDamageLevel, Trade, XPValueDefense,
     NoMaintenance, UnitArtInfo, UnitArtInfoEraVariation, ShowInPedia, MoveRate,
     UnitFlagIconOffset, PortraitIndex, IconAtlas, UnitFlagAtlas)
SELECT 'UNIT_RT_MOTORIZED_CARAVAN', 'TXT_KEY_RT_MOTORIZED_CARAVAN',
       'TXT_KEY_RT_MOTORIZED_CARAVAN_PEDIA', 'TXT_KEY_RT_MOTORIZED_CARAVAN_STRATEGY',
       'TXT_KEY_RT_MOTORIZED_CARAVAN_HELP', 'UNITCLASS_RT_MOTORIZED_CARAVAN', 150, 2,
       0, BaseSightRange, Domain, CivilianAttackPriority, DefaultUnitAI,
       MilitarySupport, MilitaryProduction, Mechanized, 'TECH_COMBUSTION', HurryCostModifier,
       AdvancedStartCost, MinAreaSize, NukeDamageLevel, 0, XPValueDefense,
       NoMaintenance, UnitArtInfo, UnitArtInfoEraVariation, ShowInPedia, MoveRate,
       UnitFlagIconOffset, PortraitIndex, IconAtlas, UnitFlagAtlas
FROM Units WHERE Type = 'UNIT_CARAVAN';

INSERT INTO Unit_FreePromotions (UnitType, PromotionType)
SELECT 'UNIT_RT_MOTORIZED_CARAVAN', PromotionType FROM Unit_FreePromotions
WHERE UnitType = 'UNIT_CARAVAN';
INSERT INTO Unit_FreePromotions (UnitType, PromotionType)
SELECT 'UNIT_RT_MOTORIZED_CARAVAN', 'PROMOTION_IGNORE_TERRAIN_COST'
WHERE NOT EXISTS (SELECT 1 FROM Unit_FreePromotions
    WHERE UnitType = 'UNIT_RT_MOTORIZED_CARAVAN' AND PromotionType = 'PROMOTION_IGNORE_TERRAIN_COST');
INSERT INTO Unit_Flavors (UnitType, FlavorType, Flavor)
SELECT 'UNIT_RT_MOTORIZED_CARAVAN', FlavorType, Flavor FROM Unit_Flavors WHERE UnitType = 'UNIT_CARAVAN';
INSERT INTO Unit_AITypes (UnitType, UnitAIType)
SELECT 'UNIT_RT_MOTORIZED_CARAVAN', UnitAIType FROM Unit_AITypes WHERE UnitType = 'UNIT_CARAVAN';
