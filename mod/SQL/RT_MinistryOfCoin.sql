-- Replace the existing city Caravansary in place. Keeping its engine identifiers
-- preserves its flavors and native origin-city trade modifiers. RT_Art.sql
-- supplies the selected custom portrait and wonder painting.
UPDATE BuildingClasses
SET Description = 'TXT_KEY_RT_MINISTRY_OF_COIN',
    MaxGlobalInstances = -1, MaxTeamInstances = -1, MaxPlayerInstances = 1,
    ExtraPlayerInstances = 0, NoLimit = 0
WHERE Type = 'BUILDINGCLASS_CARAVANSARY';

UPDATE Buildings
SET Description = 'TXT_KEY_RT_MINISTRY_OF_COIN',
    Civilopedia = 'TXT_KEY_RT_MINISTRY_OF_COIN_PEDIA',
    Strategy = 'TXT_KEY_RT_MINISTRY_OF_COIN_STRATEGY',
    Help = 'TXT_KEY_RT_MINISTRY_OF_COIN_HELP',
    Cost = 125, NumCityCostMod = 30, HurryCostModifier = -1,
    NeverCapture = 1, NukeImmune = 1, ConquestProb = 0
WHERE Type = 'BUILDING_CARAVANSARY';

-- Horseback Riding, no maintenance, +50% land range and +2 land-route gold
-- remain the original building's native values. No all-cities prerequisite.
