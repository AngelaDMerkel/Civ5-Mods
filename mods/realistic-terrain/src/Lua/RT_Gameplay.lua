-- Civ V adapter. Runs for every alive player, including AI and city-states.
-- Uses gameplay events only for mutations; UI events only refresh the panel.
RT_Gameplay = {};
local G, R, C = RT_Gameplay, RT_Rules, RT_Config;
local saved = Modding.OpenSaveData();
local cache = {};
local PREFIX = "RealisticTerrain.v1.Player.";
local ids = {};
local names = { "TERRAIN_DESERT", "TERRAIN_TUNDRA", "TERRAIN_SNOW", "FEATURE_JUNGLE",
    "FEATURE_FOREST", "FEATURE_OASIS", "FEATURE_FLOOD_PLAINS", "UNITCOMBAT_RECON",
    "PROMOTION_MEDIC", "PROMOTION_MEDIC_II", "PROMOTION_RT_STRAINED", "PROMOTION_RT_EXHAUSTED",
    "TECH_ENGINEERING", "TECH_BIOLOGY", "TECH_PENICILIN" };
for _, name in ipairs(names) do ids[name] = GameInfoTypes[name]; end
assert(ids.PROMOTION_RT_STRAINED and ids.PROMOTION_RT_EXHAUSTED,
    "Realistic Terrain: database promotions missing. Check Database.log and restart through Mods.");

local function loadPlayer(playerID)
    if cache[playerID] then return cache[playerID]; end
    local states = {};
    local raw = saved.GetValue(PREFIX .. playerID);
    if type(raw) == "string" then
        for id, value in string.gmatch(raw, "(%d+):([^;]+)") do
            local state = R.Decode(value);
            if state then states[tonumber(id)] = state; end
        end
    end
    cache[playerID] = states;
    return states;
end

local function flush(playerID)
    local states, keys, rows = loadPlayer(playerID), {}, {};
    for id in pairs(states) do keys[#keys + 1] = id; end
    table.sort(keys);
    for _, id in ipairs(keys) do rows[#rows + 1] = id .. ":" .. R.Encode(states[id]); end
    saved.SetValue(PREFIX .. playerID, table.concat(rows, ";"));
end

function G.Eligible(unit)
    if not unit or unit:IsDelayedDeath() then return false; end
    local player = Players[unit:GetOwner()];
    return player and not player:IsBarbarian() and
        unit:GetDomainType() == DomainTypes.DOMAIN_LAND and unit:IsCombatUnit();
end

local function home(unit, plot)
    local owner = plot:GetOwner();
    return owner == unit:GetOwner() or (C.TEAM_TERRITORY_SAFE and owner >= 0 and
        Players[owner] and Players[owner]:GetTeam() == unit:GetTeam());
end

local function nearby(plot)
    local result = { plot };
    for direction = 0, 5 do
        local other = Map.PlotDirection(plot:GetX(), plot:GetY(), direction);
        if other then result[#result + 1] = other; end
    end
    return result;
end

local function enemyOccupied(unit, plot)
    for i = 0, plot:GetNumUnits() - 1 do
        local other = plot:GetUnit(i);
        if other and Teams[unit:GetTeam()]:IsAtWar(other:GetTeam()) then return true; end
    end
    return false;
end

local function waterAccess(unit, plot, neighbors)
    -- A river touches this tile; mere proximity to a different river tile is insufficient.
    if plot:IsRiver() or plot:GetFeatureType() == ids.FEATURE_FLOOD_PLAINS then return true; end
    for _, source in ipairs(neighbors) do
        if source:IsLake() or source:GetFeatureType() == ids.FEATURE_OASIS then
            local owner = source:GetOwner();
            local accessible = owner < 0 or owner == unit:GetOwner();
            if owner >= 0 and Players[owner] then
                local team = Players[owner]:GetTeam();
                accessible = team == unit:GetTeam() or Teams[unit:GetTeam()]:IsAtWar(team)
                    or Teams[team]:IsAllowsOpenBordersToTeam(unit:GetTeam());
            end
            if accessible and not enemyOccupied(unit, source) then return true; end
        end
    end
    return false;
end

local function hasPromotion(unit, id)
    return id ~= nil and unit:IsHasPromotion(id);
end

local function medicSupport(unit, neighbors)
    for _, plot in ipairs(neighbors) do
        if not plot:IsWater() then
            for i = 0, plot:GetNumUnits() - 1 do
                local medic = plot:GetUnit(i);
                if medic and medic:GetTeam() == unit:GetTeam() and not medic:IsEmbarked()
                    and not medic:IsDelayedDeath() and
                    (hasPromotion(medic, ids.PROMOTION_MEDIC) or hasPromotion(medic, ids.PROMOTION_MEDIC_II)) then
                    return true;
                end
            end
        end
    end
    return false;
end

function G.Environment(unit, state)
    local plot = unit:GetPlot();
    local env = { home = home(unit, plot), paused = unit:IsEmbarked(), rate = 1 };
    local neighbors = nearby(plot);
    if not env.home and not env.paused then
        env.relief, env.reliefNearby = RT_Supply.Find(unit, neighbors);
    end
    env.outpostShelter = not env.paused and RT_OutpostBridge and RT_OutpostBridge.Shelter(unit) or false;
    env.safe = env.home or env.relief or env.outpostShelter;
    local terrain, feature = plot:GetTerrainType(), plot:GetFeatureType();
    env.water = waterAccess(unit, plot, neighbors);
    if feature == ids.FEATURE_JUNGLE then
        env.hazard = "jungle";
    elseif terrain == ids.TERRAIN_SNOW or terrain == ids.TERRAIN_TUNDRA then
        env.hazard = "cold";
        env.coldBase = terrain == ids.TERRAIN_SNOW and C.SNOW_GRACE or C.GRACE.cold;
        if terrain == ids.TERRAIN_TUNDRA and feature == ids.FEATURE_FOREST then
            env.rate = C.FOREST_COLD_RATE;
        end
    elseif terrain == ids.TERRAIN_DESERT and not env.water then
        env.hazard = "heat";
    end
    local grace = { heat = C.GRACE.heat, cold = env.coldBase or state.coldGrace,
        jungle = C.GRACE.jungle };
    if unit:GetUnitCombatType() == ids.UNITCOMBAT_RECON then
        for _, hazard in ipairs(R.HAZARDS) do grace[hazard] = grace[hazard] + C.SCOUT_BONUS; end
    end
    local techs = Teams[unit:GetTeam()]:GetTeamTechs();
    if ids.TECH_ENGINEERING and techs:HasTech(ids.TECH_ENGINEERING) then
        grace.cold = grace.cold + C.ENGINEERING_COLD_BONUS;
    end
    if ids.TECH_BIOLOGY and techs:HasTech(ids.TECH_BIOLOGY) then
        grace.jungle = grace.jungle + C.BIOLOGY_JUNGLE_BONUS;
    end
    if ids.TECH_PENICILIN and techs:HasTech(ids.TECH_PENICILIN) then
        grace.jungle = grace.jungle + C.PENICILLIN_JUNGLE_BONUS;
    end
    if medicSupport(unit, neighbors) then grace.jungle = grace.jungle + C.MEDIC_JUNGLE_BONUS; end
    return env, grace;
end

local function stamp(state, unit)
    state.birth, state.unitType, state.originalOwner = unit:GetGameTurnCreated(), unit:GetUnitType(), unit:GetOriginalOwner();
    state.x, state.y = unit:GetX(), unit:GetY();
end

local function canConvert(oldType, newUnit)
    local old = GameInfo.Units[oldType];
    local newClass = GameInfo.UnitClasses[newUnit:GetUnitClassType()];
    if not old or not newClass then return false; end
    if old.GoodyHutUpgradeUnitClass == newClass.Type then return true; end
    for upgrade in GameInfo.Unit_ClassUpgrades{ UnitType = old.Type } do
        if upgrade.UnitClassType == newClass.Type then return true; end
    end
    return false;
end

-- Stock Civ V has no universal UnitUpgraded gameplay event. Match an orphaned
-- predecessor only when birth turn, owner, tile, and upgrade path all agree.
local function getState(unit)
    local states = loadPlayer(unit:GetOwner());
    local id = unit:GetID();
    local state = states[id];
    if state and state.birth == unit:GetGameTurnCreated() and state.unitType == unit:GetUnitType()
        and state.originalOwner == unit:GetOriginalOwner() then return state; end
    local matchedID, matchedState, ambiguous;
    for oldID, old in pairs(states) do
        local predecessor = Players[unit:GetOwner()]:GetUnitByID(oldID);
        if (not predecessor or predecessor:IsDelayedDeath()) and old.birth == unit:GetGameTurnCreated()
            and old.originalOwner == unit:GetOriginalOwner() and old.x == unit:GetX() and old.y == unit:GetY()
            and canConvert(old.unitType, unit) then
            if matchedID then ambiguous = true; end
            matchedID, matchedState = oldID, old;
        end
    end
    if matchedID and not ambiguous then
        state = matchedState;
        states[matchedID] = nil;
    else
        state = R.NewState();
        state.lastTurn = Game.GetGameTurn(); -- newly created units get a complete turn
    end
    stamp(state, unit);
    states[id] = state;
    return state;
end

local function applyStatus(unit, stage)
    local strained, exhausted = stage == 1, stage == 2;
    if unit:IsHasPromotion(ids.PROMOTION_RT_STRAINED) ~= strained then
        unit:SetHasPromotion(ids.PROMOTION_RT_STRAINED, strained);
    end
    if unit:IsHasPromotion(ids.PROMOTION_RT_EXHAUSTED) ~= exhausted then
        unit:SetHasPromotion(ids.PROMOTION_RT_EXHAUSTED, exhausted);
    end
end

function G.StateLabel(stage)
    return Locale.ConvertTextKey(stage == 2 and "TXT_KEY_RT_EXHAUSTED_SHORT"
        or stage == 1 and "TXT_KEY_RT_STRAINED_SHORT" or "TXT_KEY_RT_READY");
end

local function notify(unit, previousStage, state)
    if C.NOTIFICATIONS and previousStage ~= state.stage and Players[unit:GetOwner()]:IsHuman() then
        Players[unit:GetOwner()]:AddNotification(NotificationTypes.NOTIFICATION_GENERIC,
            Locale.ConvertTextKey("TXT_KEY_RT_NOTIFY", unit:GetName(), G.StateLabel(state.stage)),
            Locale.ConvertTextKey("TXT_KEY_RT_NOTIFY_TITLE"), unit:GetX(), unit:GetY());
    end
end

-- Does not change counters; UI calls this to preview the next exposure check.
function G.Inspect(unit)
    if not G.Eligible(unit) then return nil; end
    local state = loadPlayer(unit:GetOwner())[unit:GetID()];
    if not state or state.birth ~= unit:GetGameTurnCreated() or state.unitType ~= unit:GetUnitType() then
        state = R.NewState();
    end
    local env, grace = G.Environment(unit, state);
    -- Show the applied status. Live support belongs in the next-turn forecast.
    local stage = (env.home or env.paused) and 0 or state.stage;
    local preview = R.Advance(state, env, grace, C, math.max(state.lastTurn, Game.GetGameTurn()) + 1);
    return { state = state, env = env, grace = grace, stage = stage, nextStage = preview.stage,
        damage = R.Damage(preview.stage, unit:GetDamage(), GameDefines.MAX_HIT_POINTS, C, env.paused or env.safe) };
end

function G.RefreshUnit(unit, announce)
    if not G.Eligible(unit) then
        if unit and not unit:IsDelayedDeath() then applyStatus(unit, 0); end
        return;
    end
    local state = getState(unit);
    local previousStage = state.stage;
    local env, grace = G.Environment(unit, state);
    -- Stations replenish after spending a turn in range; homeland is immediate.
    if env.home then R.Reset(state); end
    state.stage = R.Stage(state, grace, C);
    applyStatus(unit, env.paused and 0 or state.stage);
    stamp(state, unit);
    if announce then notify(unit, previousStage, state); end
end

function G.OnPlayerDoTurn(playerID)
    local player = Players[playerID];
    if not player or not player:IsAlive() then return; end
    local states, live = loadPlayer(playerID), {};
    local turn = Game.GetGameTurn();
    -- Resolve all conversions before pruning the old roster.
    for unit in player:Units() do
        if G.Eligible(unit) then getState(unit); end
    end
    for unit in player:Units() do
        if G.Eligible(unit) then
            local id = unit:GetID();
            live[id] = true;
            local previous = getState(unit);
            local env, grace = G.Environment(unit, previous);
            local state, advanced = R.Advance(previous, env, grace, C, turn);
            if env.home then R.Reset(state); end
            state.stage = R.Stage(state, grace, C);
            stamp(state, unit);
            states[id] = state;
            applyStatus(unit, env.paused and 0 or state.stage);
            if advanced then
                local damage = R.Damage(state.stage, unit:GetDamage(), GameDefines.MAX_HIT_POINTS,
                    C, env.paused or env.safe);
                if damage > 0 then unit:ChangeDamage(damage, -1); end
                notify(unit, previous.stage, state);
            end
        else
            G.RefreshUnit(unit, false);
        end
    end
    for id in pairs(states) do if not live[id] then states[id] = nil; end end
    flush(playerID);
    if G.OnChanged then G.OnChanged(); end
end

function G.OnUnitSetXY(playerID, unitID)
    local player = Players[playerID];
    local unit = player and player:GetUnitByID(unitID);
    if not unit or unit:IsDelayedDeath() then return; end
    G.RefreshUnit(unit, true); -- home protection is immediate, water relief is overnight
    flush(playerID);
    -- A moving medic can change support for stationary troops at either end of
    -- its move. Refresh teammates too; multiple medics still provide one bonus.
    if hasPromotion(unit, ids.PROMOTION_MEDIC) or hasPromotion(unit, ids.PROMOTION_MEDIC_II) then
        for otherID = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
            local other = Players[otherID];
            if other and other:IsAlive() and other:GetTeam() == unit:GetTeam() then
                for troop in other:Units() do G.RefreshUnit(troop, false); end
                flush(otherID);
            end
        end
    end
    if G.OnChanged then G.OnChanged(); end
end

function G.Initialize()
    for playerID = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
        local player = Players[playerID];
        if player and player:IsAlive() then
            for unit in player:Units() do G.RefreshUnit(unit, false); end
            flush(playerID);
        end
    end
    GameEvents.PlayerDoTurn.Add(G.OnPlayerDoTurn);
    GameEvents.UnitSetXY.Add(G.OnUnitSetXY);
    -- A city capture or tile purchase may put a stationary unit inside home borders.
    local function refreshAll()
        for playerID = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
            local player = Players[playerID];
            if player and player:IsAlive() then
                for unit in player:Units() do G.RefreshUnit(unit, false); end
                flush(playerID);
            end
        end
        if G.OnChanged then G.OnChanged(); end
    end
    GameEvents.CityCaptureComplete.Add(refreshAll);
    GameEvents.CityBoughtPlot.Add(refreshAll);
    GameEvents.PlayerCityFounded.Add(refreshAll);
    GameEvents.TeamTechResearched.Add(refreshAll);
    GameEvents.BuildFinished.Add(function(playerID, x, y, improvement)
        RT_Supply.OnBuildFinished(playerID, x, y, improvement);
        if G.OnChanged then G.OnChanged(); end
    end);
    print("Realistic Terrain v2 initialized (single-player, BNW).");
end
