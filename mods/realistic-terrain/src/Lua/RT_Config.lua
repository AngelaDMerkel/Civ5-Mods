-- Gameplay tuning. Change before starting a new game, then rebuild the package.
RT_Config = {
    VERSION = 2,
    GRACE = { heat = 2, cold = 3, jungle = 4 },
    SNOW_GRACE = 1,
    STRAINED_TURNS = 2,
    DAMAGE_PER_TURN = 5,
    MIN_HP_PERCENT = 25,
    RECOVERY_PER_TURN = 2,
    SCOUT_BONUS = 2,
    MEDIC_JUNGLE_BONUS = 2,
    ENGINEERING_COLD_BONUS = 1,
    BIOLOGY_JUNGLE_BONUS = 1,
    PENICILLIN_JUNGLE_BONUS = 2,
    MAX_EXPOSURE = 30,
    FOREST_COLD_RATE = 0.5,
    NOTIFICATIONS = true,
    TEAM_TERRITORY_SAFE = true,
    -- V1 intentionally exempts civilians and barbarians. No hidden AI discount.
    UI_OFFSET_X = 0,
    UI_OFFSET_Y = 64,
};
