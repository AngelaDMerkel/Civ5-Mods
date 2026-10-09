-- All trade is handled by the Lua replacement. Keeping native trade enabled
-- would let native AI/UI bypass agreements and infrastructure restrictions.
UPDATE Units SET Trade = 0, Immobile = 0, Moves = 2,
    Help = 'TXT_KEY_RT_CARAVAN_HELP'
WHERE Type = 'UNIT_CARAVAN';
UPDATE Units SET Trade = 0, Immobile = 0, Moves = 4,
    Help = 'TXT_KEY_RT_CARGO_HELP'
WHERE Type = 'UNIT_CARGO_SHIP';

INSERT INTO Technologies
    (Type, Description, Civilopedia, Help, Quote, Cost, Era, GridX, GridY,
     PortraitIndex, IconAtlas, Trade, GoodyTech)
SELECT 'TECH_RT_CARAVAN_LOGISTICS', 'TXT_KEY_RT_LOGISTICS', 'TXT_KEY_RT_LOGISTICS_PEDIA',
       'TXT_KEY_RT_LOGISTICS_HELP', 'TXT_KEY_RT_LOGISTICS_QUOTE', 275, 'ERA_MEDIEVAL', 5, 10,
       PortraitIndex, IconAtlas, 1, 0
FROM Technologies WHERE Type = 'TECH_ENGINEERING';
INSERT INTO Technology_PrereqTechs (TechType, PrereqTech)
VALUES ('TECH_RT_CARAVAN_LOGISTICS', 'TECH_ENGINEERING');
INSERT INTO Technology_Flavors (TechType, FlavorType, Flavor)
VALUES ('TECH_RT_CARAVAN_LOGISTICS', 'FLAVOR_I_LAND_TRADE_ROUTE', 20),
       ('TECH_RT_CARAVAN_LOGISTICS', 'FLAVOR_GOLD', 10);
