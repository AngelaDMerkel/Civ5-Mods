-- Status promotions are assigned by Lua, never selected with experience.
-- They are mutually exclusive. CombatPercent affects both attack and defense.
INSERT INTO UnitPromotions
    (Type, Description, Help, CannotBeChosen, LostWithUpgrade, CombatPercent,
     PortraitIndex, IconAtlas, PediaType, PediaEntry)
VALUES
    ('PROMOTION_RT_STRAINED', 'TXT_KEY_RT_STRAINED', 'TXT_KEY_RT_STRAINED_HELP',
     1, 0, -10, 26, 'PROMOTION_ATLAS', 'PEDIA_ATTRIBUTES', 'TXT_KEY_RT_STRAINED'),
    ('PROMOTION_RT_EXHAUSTED', 'TXT_KEY_RT_EXHAUSTED', 'TXT_KEY_RT_EXHAUSTED_HELP',
     1, 0, -20, 26, 'PROMOTION_ATLAS', 'PEDIA_ATTRIBUTES', 'TXT_KEY_RT_EXHAUSTED');
