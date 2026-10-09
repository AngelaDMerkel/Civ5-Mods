-- Mock only the Civ V API boundary; execute the production adapter unchanged.
local count = 0;
local function eq(actual, expected, message)
    count = count + 1;
    assert(actual == expected, (message or "assertion") .. ": expected " .. tostring(expected) .. ", got " .. tostring(actual));
end
local turn, savedValues = 0, {};
Game = { GetGameTurn = function() return turn; end, GetActivePlayer = function() return 0; end };
GameDefines = { MAX_HIT_POINTS = 100, MAX_CIV_PLAYERS = 4 };
DomainTypes = { DOMAIN_LAND = 0 };
NotificationTypes = { NOTIFICATION_GENERIC = 1 };
Locale = { ConvertTextKey = function(key, ...) return key; end };
Modding = { OpenSaveData = function() return {
    GetValue = function(self, k) return savedValues[k]; end,
    SetValue = function(self, k, v) savedValues[k] = v; end,
}; end };
GameEvents = setmetatable({}, { __index = function(t, k)
    local callbacks = {};
    local event = { Add = function(f) callbacks[#callbacks + 1] = f; end,
        Fire = function(...) for _, f in ipairs(callbacks) do f(...); end end };
    setmetatable(event, { __call = function(_, ...) event.Fire(...); end });
    rawset(t, k, event); return event;
end });
GameInfoTypes = {};
for i, name in ipairs({ "TERRAIN_DESERT", "TERRAIN_TUNDRA", "TERRAIN_SNOW", "FEATURE_JUNGLE",
    "FEATURE_FOREST", "FEATURE_OASIS", "FEATURE_FLOOD_PLAINS", "UNITCOMBAT_RECON", "PROMOTION_MEDIC",
    "PROMOTION_MEDIC_II", "PROMOTION_RT_STRAINED", "PROMOTION_RT_EXHAUSTED", "TECH_ENGINEERING",
    "TECH_BIOLOGY", "TECH_PENICILIN", "IMPROVEMENT_RT_RELIEF_STATION", "ROUTE_ROAD", "ROUTE_RAILROAD",
    "BUILD_RT_RELIEF_STATION", "BUILDING_CARAVANSARY", "IMPROVEMENT_RT_IRRIGATED_FARM", "IMPROVEMENT_RT_DRY_FARM", "BUILDING_RT_IRRIGATION_WORKS", "BUILD_RT_IRRIGATED_FARM", "IMPROVEMENT_FARM", "RESOURCE_WHEAT" }) do GameInfoTypes[name] = i; end
local I = GameInfoTypes;
GameInfo = {
    Unit_Builds = function() return function() return nil; end; end,
    Units = { [1] = { Type = "UNIT_WARRIOR", GoodyHutUpgradeUnitClass = "UNITCLASS_SPEARMAN" },
              [2] = { Type = "UNIT_SPEARMAN" } },
    UnitClasses = { [1] = { Type = "UNITCLASS_WARRIOR" }, [2] = { Type = "UNITCLASS_SPEARMAN" } },
    Unit_ClassUpgrades = function(query)
        local done = false;
        return function()
            if not done and query.UnitType == "UNIT_WARRIOR" then
                done = true; return { UnitClassType = "UNITCLASS_SPEARMAN" };
            end
        end;
    end,
};
Teams = {};
for id = 0, 3 do
    local team = { techs = {}, wars = {}, open = {} };
    Teams[id] = team;
    function team:GetTeamTechs()
        return { HasTech = function(_, tech) return self.techs[tech] or false; end };
    end
    function team:IsAtWar(other) return self.wars[other] or false; end
    function team:IsAllowsOpenBordersToTeam(other) return self.open[other] or false; end
end
Players = {};
for id = 0, 3 do
    local player = { id = id, units = {}, notices = {}, barbarian = id == 3, team = id };
    Players[id] = player;
    function player:IsAlive() return true; end
    function player:IsBarbarian() return self.barbarian; end
    function player:IsHuman() return self.id == 0; end
    function player:GetTeam() return self.team; end
    function player:GetUnitByID(id) return self.units[id]; end
    function player:AddNotification(...) self.notices[#self.notices + 1] = {...}; end
    function player:Units()
        local keys = {}; for id in pairs(self.units) do keys[#keys + 1] = id; end; table.sort(keys);
        local n = 0;
        return function() n = n + 1; return self.units[keys[n]]; end;
    end
end
local plots = {};
local function plot(x, terrain, feature, owner)
    local p = { x = x, y = 0, terrain = terrain or -1, feature = feature or -1,
        owner = owner or -1, units = {}, adjacent = {} };
    function p:GetPlotIndex() return self.x; end
    function p:GetX() return self.x; end; function p:GetY() return self.y; end
    function p:GetOwner() return self.owner; end
    function p:GetTerrainType() return self.terrain; end
    function p:GetFeatureType() return self.feature; end
    function p:IsRiver() return self.river or false; end
    function p:IsLake() return self.lake or false; end
    function p:IsWater() return self.water or self.lake or false; end
    function p:GetNumUnits() return #self.units; end
    function p:GetUnit(i) return self.units[i + 1]; end
    function p:GetImprovementType() return self.improvement or -1; end
    function p:IsImprovementPillaged() return self.improvementPillaged or false; end
    function p:GetRouteType() return self.route or -1; end
    function p:IsRoutePillaged() return self.routePillaged or false; end
    function p:IsMountain() return self.mountain or false; end
    function p:IsHills() return false; end
    function p:GetResourceType() return -1; end
    function p:GetWorkingCity() return self.city; end
    function p:GetPlotCity() return self.city; end
    plots[x] = p; return p;
end
Map = { GetNumPlots = function() return 0; end, PlotDirection = function(x, y, direction) return plots[x].adjacent[direction + 1]; end,
    GetPlot = function(x, y) return plots[x]; end };
local function move(u, p)
    if u.plot then for i, v in ipairs(u.plot.units) do if u == v then table.remove(u.plot.units, i); break; end end end
    u.plot = p; p.units[#p.units + 1] = u;
end
local function unit(id, owner, p)
    local u = { id = id, owner = owner or 0, promotions = {}, damage = 0, birth = turn,
        unitType = 1, combat = true, domain = 0, combatType = -1 };
    function u:GetOwner() return self.owner; end
    function u:GetTeam() return Players[self.owner]:GetTeam(); end
    function u:GetID() return self.id; end
    function u:GetPlot() return self.plot; end
    function u:GetX() return self.plot.x; end; function u:GetY() return self.plot.y; end
    function u:GetGameTurnCreated() return self.birth; end
    function u:GetOriginalOwner() return self.originalOwner or self.owner; end
    function u:GetUnitType() return self.unitType; end
    function u:GetBuildType() return -1; end
    function u:GetUnitClassType() return self.unitType; end
    function u:GetUnitCombatType() return self.combatType; end
    function u:GetDomainType() return self.domain; end
    function u:IsCombatUnit() return self.combat; end
    function u:IsDelayedDeath() return self.dead or false; end
    function u:IsEmbarked() return self.embarked or false; end
    function u:IsHasPromotion(p) return self.promotions[p] or false; end
    function u:SetHasPromotion(p, value) self.promotions[p] = value; end
    function u:GetDamage() return self.damage; end
    function u:ChangeDamage(value) self.damage = self.damage + value; end
    function u:GetName() return "Test unit"; end
    Players[u.owner].units[id] = u; move(u, p); return u;
end
local function kill(u)
    Players[u.owner].units[u.id] = nil; u.dead = true;
    for i, v in ipairs(u.plot.units) do if v == u then table.remove(u.plot.units, i); break; end end
end
local desert = plot(0, I.TERRAIN_DESERT);
local home = plot(1, I.TERRAIN_DESERT, nil, 0);
local oasis = plot(2, I.TERRAIN_DESERT, I.FEATURE_OASIS);
local jungle = plot(3, nil, I.FEATURE_JUNGLE);
local tundra = plot(4, I.TERRAIN_TUNDRA, I.FEATURE_FOREST);
local snow = plot(5, I.TERRAIN_SNOW);
local lake = plot(6); lake.lake = true;
local coast = plot(7); coast.water = true;
local land = plot(8);
local soldier = unit(0, 0, desert);
local ai = unit(0, 1, desert);
local scout = unit(1, 0, desert); scout.combatType = I.UNITCOMBAT_RECON;
local civilian = unit(2, 0, desert); civilian.combat = false;
local barbarian = unit(0, 3, desert);
local snowUnit = unit(3, 0, snow);
local forestUnit = unit(4, 0, tundra);
dofile(TEST_ROOT .. "/mods/realistic-terrain/src/Lua/RT_Supply.lua");
dofile(TEST_ROOT .. "/mods/realistic-terrain/src/Lua/RT_Gameplay.lua");
local G = RT_Gameplay;
G.Initialize();
local function advance(player) turn = turn + 1; G.OnPlayerDoTurn(player or 0); end
local function inspect(u) return G.Inspect(u); end
local function relocated(u, p) move(u, p); G.OnUnitSetXY(u.owner, u.id); end
eq(G.Eligible(civilian), false, "civilian exempt");
eq(G.Eligible(barbarian), false, "barbarian exempt");
eq(inspect(soldier).state.heat, 0, "initial state");
G.OnPlayerDoTurn(0); eq(inspect(soldier).state.heat, 0, "no creation-turn tick");
for i = 1, 5 do advance(); G.OnPlayerDoTurn(1); end
eq(inspect(soldier).state.heat, 5); eq(inspect(soldier).stage, 2);
eq(soldier.damage, 5); eq(ai.damage, 5, "AI parity");
eq(soldier:IsHasPromotion(I.PROMOTION_RT_EXHAUSTED), true);
eq(soldier:IsHasPromotion(I.PROMOTION_RT_STRAINED), false, "mutually exclusive status");
eq(inspect(scout).stage, 1, "scout bonus");
eq(inspect(snowUnit).stage, 2, "snow progression");
eq(inspect(forestUnit).state.cold, 2.5, "forest half rate");
local notices = #Players[0].notices;
G.OnPlayerDoTurn(0); eq(soldier.damage, 5, "duplicate tick damage guard");
eq(#Players[0].notices, notices, "notifications only on change");

-- Reload the Lua context while keeping the game's saved data.
dofile(TEST_ROOT .. "/mods/realistic-terrain/src/Lua/RT_Gameplay.lua"); G = RT_Gameplay;
G.Initialize(); G.OnPlayerDoTurn(0);
eq(inspect(soldier).state.heat, 5, "reload preserves exposure");
eq(soldier.damage, 5, "reload cannot repeat damage");
relocated(soldier, home); eq(inspect(soldier).state.heat, 0, "home immediate reset");
eq(soldier.damage, 5, "home does not heal HP");
eq(soldier:IsHasPromotion(I.PROMOTION_RT_EXHAUSTED), false);
relocated(soldier, desert); advance(); eq(inspect(soldier).state.heat, 1);

-- Passing water is not a refill; the player must stay for the turn check.
desert.adjacent = { oasis };
G.OnUnitSetXY(0, soldier.id); eq(inspect(soldier).state.heat, 1, "water not instant");
advance(); eq(inspect(soldier).state.heat, 0, "oasis relief overnight");
local enemy = unit(20, 1, oasis); Teams[0].wars[1] = true;
eq(inspect(soldier).env.water, false, "enemy blocks oasis");
kill(enemy); eq(inspect(soldier).env.water, true);
oasis.owner = 2; eq(inspect(soldier).env.water, false, "closed borders block access");
Teams[2].open[0] = true; eq(inspect(soldier).env.water, true, "open borders permit water access");
desert.adjacent = { lake }; eq(inspect(soldier).env.water, true, "lake relief");
desert.adjacent = { coast }; eq(inspect(soldier).env.water, false, "saltwater not relief");
desert.river = true; eq(inspect(soldier).env.water, true, "river relief");
desert.river = false; desert.feature = I.FEATURE_FLOOD_PLAINS;
eq(inspect(soldier).env.water, true, "floodplains relief");
desert.feature = -1; desert.adjacent = {};
for i = 1, 5 do advance(); end
eq(inspect(soldier).stage, 2);
local heat = inspect(soldier).state.heat;
soldier.embarked = true; relocated(soldier, coast);
local damage = soldier.damage;
advance(); eq(inspect(soldier).state.heat, heat, "embarking retains counters");
eq(soldier.damage, damage); eq(soldier:IsHasPromotion(I.PROMOTION_RT_EXHAUSTED), false);
soldier.embarked = false; relocated(soldier, desert);
eq(soldier:IsHasPromotion(I.PROMOTION_RT_EXHAUSTED), true, "disembarking restores status");
soldier.damage = 74; advance(); eq(soldier.damage, 75, "25 HP floor");
soldier.damage = 90; advance(); eq(soldier.damage, 90, "no environmental healing");

-- Medicine applies to jungle, never to heat or cold.
local j = unit(30, 0, jungle); G.OnUnitSetXY(0, j.id);
local medic = unit(31, 0, land); medic.promotions[I.PROMOTION_MEDIC] = true;
jungle.adjacent = { land };
eq(inspect(j).grace.jungle, 6, "adjacent medic");
medic.embarked = true; eq(inspect(j).grace.jungle, 4, "embarked medic cannot help");
medic.embarked = false;
Teams[0].techs[I.TECH_BIOLOGY] = true; Teams[0].techs[I.TECH_PENICILIN] = true;
eq(inspect(j).grace.jungle, 9, "medical tech stacking");
Teams[0].techs[I.TECH_ENGINEERING] = true;
eq(inspect(snowUnit).grace.cold, 2, "engineering supports winter");
advance(); eq(inspect(snowUnit).grace.cold, 2, "cold support is not compounded every turn");

-- Borders are owner-relative, including AI and team territory.
Teams[0].wars[1] = false;
relocated(ai, home); eq(inspect(ai).env.safe, false, "foreign borders not safe");
Players[2].team = 0; oasis.owner = 2; relocated(soldier, oasis);
eq(inspect(soldier).state.heat, 0, "team supply");
relocated(soldier, desert); advance();
desert.owner = 0; G.RefreshUnit(soldier, false);
eq(inspect(soldier).state.heat, 0, "stationary unit gains protection after border change");
desert.owner = -1;

-- Upgrade outside home territory (e.g. ancient ruins) keeps exposure.
local old = unit(40, 0, desert); G.OnUnitSetXY(0, old.id);
for i = 1, 3 do advance(); end
local oldHeat = inspect(old).state.heat;
kill(old);
local upgraded = unit(41, 0, desert); upgraded.unitType = 2; upgraded.birth = old.birth;
G.OnUnitSetXY(0, upgraded.id);
eq(inspect(upgraded).state.heat, oldHeat, "upgrade transfer");
eq(inspect(upgraded).stage, 1);
-- Fresh units with recycled IDs do not inherit a dead soldier's record.
kill(upgraded); turn = turn + 1;
local replacement = unit(41, 0, desert); G.OnUnitSetXY(0, replacement.id);
eq(inspect(replacement).state.heat, 0, "recycled IDs start clean");
-- Normal upgrades at home are supplied and keep combat damage.
relocated(replacement, home); replacement.damage = 18; kill(replacement);
local homeUpgrade = unit(42, 0, home); homeUpgrade.unitType = 2;
homeUpgrade.birth = replacement.birth; homeUpgrade.damage = replacement.damage;
G.OnUnitSetXY(0, homeUpgrade.id);
eq(inspect(homeUpgrade).state.heat, 0); eq(homeUpgrade.damage, 18);
G.OnPlayerDoTurn(0);
eq(string.find(savedValues["RealisticTerrain.v1.Player.0"], "40:", 1, true), nil, "dead records removed");

-- UI refreshes must never cause gameplay ticks or change health.
local before = savedValues["RealisticTerrain.v1.Player.0"];
for i = 1, 20 do G.Inspect(homeUpgrade); end
eq(savedValues["RealisticTerrain.v1.Player.0"], before, "read-only UI");
eq(homeUpgrade.damage, 18);
print("Game adapter: " .. count .. " assertions passed");

-- Relief Stations: test the actual graph search and its exposure integration.
local function link(a, b)
    a.adjacent[#a.adjacent + 1] = b; b.adjacent[#b.adjacent + 1] = a;
end
local approach = plot(100, I.TERRAIN_DESERT);
local station = plot(101, I.TERRAIN_DESERT);
local road1, road2, cityPlot = plot(102), plot(103), plot(104, nil, nil, 0);
local detour, deadEnd = plot(105), plot(106);
station.improvement = I.IMPROVEMENT_RT_RELIEF_STATION;
station.route, road1.route, road2.route = I.ROUTE_ROAD, I.ROUTE_ROAD, I.ROUTE_ROAD;
cityPlot.city = { GetOwner = function() return cityPlot.owner; end };
link(approach, station); link(station, road1); link(road1, road2); link(road2, cityPlot);
local S = RT_Supply;
eq(S.Connected(station, 0), false, "unknown neutral station not shared");
S.OnBuildFinished(0, 101, 0, I.IMPROVEMENT_RT_RELIEF_STATION);
eq(S.Owner(station), 0, "neutral builder recorded");
eq(S.Connected(station, 0), true, "neutral roads lead to own city");
eq(S.Connected(station, 1), false, "other players cannot use builder's station");
station.route = nil; eq(S.Connected(station, 0), false, "station itself needs a road");
station.route = I.ROUTE_ROAD;
road1.route = nil; eq(S.Connected(station, 0), false, "one-tile road gap");
road1.route = I.ROUTE_RAILROAD; eq(S.Connected(station, 0), true, "mixed road and railroad");
road1.routePillaged = true; eq(S.Connected(station, 0), false, "pillaged road blocks");
road1.routePillaged = false;
station.routePillaged = true; eq(S.Connected(station, 0), false, "pillaged station road blocks");
station.routePillaged = false;
station.improvementPillaged = true; eq(S.Connected(station, 0), false, "pillaged station blocks");
station.improvementPillaged = false;
road1.water = true; eq(S.Connected(station, 0), false, "no harbor or water shortcut");
road1.water = false; road1.mountain = true; eq(S.Connected(station, 0), false, "impassable route cannot supply");
road1.mountain = false;
road1.owner = 1; eq(S.Connected(station, 0), false, "foreign road cannot supply");
road1.owner = 2; eq(S.Connected(station, 0), false, "teammate road is not player's road");
road1.owner = 0; eq(S.Connected(station, 0), true, "own road works");
road1.owner = -1;
cityPlot.owner = 1; eq(S.Connected(station, 0), false, "enemy city not an endpoint");
cityPlot.owner = 2; eq(S.Connected(station, 0), false, "teammate city not an endpoint");
cityPlot.owner = 0;
Teams[0].wars[1] = true;
local blocker = unit(70, 1, road1);
eq(S.Connected(station, 0), false, "enemy occupies supply road");
move(blocker, station); eq(S.Connected(station, 0), false, "enemy occupies station");
move(blocker, cityPlot); eq(S.Connected(station, 0), false, "enemy blocks endpoint");
kill(blocker);
eq(S.Connected(station, 0), true, "blockade lifted without stale cache");
station.owner = 1; eq(S.Connected(station, 0), false, "station territorial capture stops original supply");
station.owner = 0; eq(S.Connected(station, 0), true);
station.owner = -1;
S.OnBuildFinished(1, 101, 0, -1); eq(S.Owner(station), 0, "road repair preserves neutral builder");
dofile(TEST_ROOT .. "/mods/realistic-terrain/src/Lua/RT_Supply.lua"); S = RT_Supply;
eq(S.Owner(station), 0, "builder survives reload");
eq(S.Connected(station, 0), true, "connection survives reload");
-- A branch bypasses a broken road; a loop without a city terminates normally.
link(station, detour); link(detour, road2); detour.route = I.ROUTE_ROAD;
road1.routePillaged = true; eq(S.Connected(station, 0), true, "alternate route");
cityPlot.city = nil; link(detour, deadEnd); link(deadEnd, station); deadEnd.route = I.ROUTE_ROAD;
eq(S.Connected(station, 0), false, "cyclic road network without city");
cityPlot.city = { GetOwner = function() return cityPlot.owner; end };
road1.routePillaged = false; detour.route = nil; deadEnd.route = nil;
-- No connection: an adjacent exhausted unit continues suffering normally.
road2.route = nil;
local expedition = unit(60, 0, approach); G.OnUnitSetXY(0, expedition.id);
for i = 1, 5 do advance(); end
eq(inspect(expedition).stage, 2, "disconnected station gives no relief");
eq(expedition.damage, 5);
eq(inspect(expedition).env.reliefNearby, true);
eq(inspect(expedition).env.relief, false);
-- Connect the final segment; preview cannot itself mutate exposure or promotions.
road2.route = I.ROUTE_ROAD;
local oldDamage, oldExposure = expedition.damage, inspect(expedition).state.heat;
eq(inspect(expedition).env.relief, true, "adjacent station in range");
eq(inspect(expedition).stage, 2, "penalty remains until the overnight check");
eq(inspect(expedition).nextStage, 0, "forecast includes relief");
G.OnPlayerDoTurn(0);
eq(inspect(expedition).state.heat, oldExposure, "duplicate callback cannot grant early station relief");
G.RefreshUnit(expedition, false);
eq(inspect(expedition).state.heat, oldExposure, "movement refresh not a free resupply");
advance();
eq(inspect(expedition).state.heat, 0, "connected station clears heat");
eq(inspect(expedition).stage, 0); eq(expedition.damage, oldDamage, "resupply prevents damage without healing");
eq(expedition:IsHasPromotion(I.PROMOTION_RT_EXHAUSTED), false, "combat penalty actually removed");
eq(expedition:IsHasPromotion(I.PROMOTION_RT_STRAINED), false);
G.OnPlayerDoTurn(0); eq(expedition.damage, oldDamage, "repeat turn remains safe");
road2.routePillaged = true; advance();
eq(inspect(expedition).state.heat, 1, "cut route resumes fresh exposure");
road2.routePillaged = false; advance(); eq(inspect(expedition).state.heat, 0, "repair restores relief");
-- A station also resets accumulated cold and jungle exposure, not just heat.
local away = plot(110, nil, I.FEATURE_JUNGLE);
relocated(expedition, away); advance(); advance();
away.feature = -1; away.terrain = I.TERRAIN_TUNDRA; advance(); advance();
eq(inspect(expedition).state.jungle, 2); eq(inspect(expedition).state.cold, 2);
relocated(expedition, station); advance();
eq(inspect(expedition).state.jungle, 0, "station clears jungle");
eq(inspect(expedition).state.cold, 0, "station clears cold");
-- Two tiles away is out of range even along the same road.
relocated(expedition, road2); eq(inspect(expedition).env.relief, false, "radius is one tile");
relocated(expedition, approach); expedition.embarked = true;
eq(inspect(expedition).env.relief, nil, "embarked units cannot resupply from land");
expedition.embarked = false;
-- AI stations use exactly the same ownership and connectivity rules.
station.owner = 1; cityPlot.owner = 1;
local aiExpedition = unit(80, 1, approach); G.OnUnitSetXY(1, aiExpedition.id);
eq(inspect(aiExpedition).env.relief, true, "AI relief station parity");
eq(inspect(expedition).env.relief, false, "captured station benefits its new owner only");
station.owner = -1; cityPlot.owner = 0;
station.improvement = -1; S.OnBuildFinished(0, 101, 0, -1);
eq(S.Owner(station), -1, "replacement removes stale builder");
eq(S.Connected(station, 0), false, "removed station cannot supply");
print("Game adapter + supply: " .. count .. " assertions passed");

-- Run the real UI bootstrap and its event handlers with lightweight controls.
-- A worker selection exercises the real construction panel and click callback.
I.UNIT_WORKER = 99;
GameInfo.Unit_Builds = function()
    local done = false;
    return function() if not done then done = true; return { UnitType = "UNIT_WORKER" }; end end;
end;
GameInfo.Builds = { [I.BUILD_RT_RELIEF_STATION] = { Type = "BUILD_RT_RELIEF_STATION", PrereqTech = "TECH_ENGINEERING" } };
GameInfo.Builds[I.BUILD_RT_IRRIGATED_FARM] = { Type = "BUILD_RT_IRRIGATED_FARM", PrereqTech = "TECH_ENGINEERING" };
GameInfo.BuildFeatures = function() return function() return nil; end; end;
local builder = unit(91, 0, land); builder.combat = false; builder.unitType = 99;
builder.moves = 120;
function builder:IsAutomated() return false; end
function builder:IsBusy() return false; end
function builder:GetBuildType() return -1; end
function builder:GetMoves() return self.moves; end
function builder:WorkRate() return self.moves > 0 and 100 or 0; end
function builder:FinishMoves() self.moves = 0; end
local hasMinistry = false;
Players[0].CountNumBuildings = function() return hasMinistry and 1 or 0; end;
Players[0].IsTurnActive = function() return true; end;
Teams[0].techs[I.TECH_ENGINEERING] = true;
land.progress = 0;
function land:CanBuild() return true; end
function land:GetBuildProgress() return self.progress; end
function land:GetBuildTime() return 300; end
function land:ChangeBuildProgress(_, work) self.progress = self.progress + work; return false; end
Controls = {};
for _, name in ipairs({ "ExposurePanel", "ExposureTitle", "ExposureStatus", "ConstructionPanel", "ConstructionButton", "ConstructionButtonLabel", "ConstructionProgress", "IrrigationButton", "IrrigationButtonLabel", "IrrigationProgress", "OutpostButton", "OutpostButtonLabel", "OutpostProgress", "OutpostPanel", "OutpostStatus" }) do
    local control = {};
    function control:SetHide(value) self.hidden = value; end
    function control:SetText(value) self.text = value; end
    function control:SetToolTipString(value) self.tooltip = value; end
    function control:SetOffsetVal(x, y) self.x, self.y = x, y; end
    function control:SetDisabled(value) self.disabled = value; end
    function control:RegisterCallback(event, callback) self.callback = callback; end
    Controls[name] = control;
end
Events = setmetatable({}, getmetatable(GameEvents));
LuaEvents = setmetatable({}, getmetatable(GameEvents));
local selected = soldier;
UI = { GetHeadSelectedUnit = function() return selected; end };
Mouse = { eLClick = 1 };
-- The trade and outpost adapters have their own complete test worlds.
include = function(name) if name ~= "RT_TradeBootstrap" then dofile(RT_LUA(name)); end end;
dofile(TEST_ROOT .. "/mods/realistic-terrain/src/UI/RT_Environment.lua");
eq(Controls.ExposurePanel.hidden, false, "selected land unit shows panel");
eq(Controls.ConstructionPanel.hidden, true, "military selection hides construction");
eq(type(Controls.ExposureStatus.text), "string");
eq(type(Controls.ExposureStatus.tooltip), "string");
selected = civilian; Events.UnitSelectionChanged.Fire();
eq(Controls.ExposurePanel.hidden, true, "civilian hides panel");
selected = ai; Events.UnitSelectionChanged.Fire();
eq(Controls.ExposurePanel.hidden, true, "enemy selection hides private information");
selected = nil; Events.UnitSelectionCleared.Fire();
eq(Controls.ExposurePanel.hidden, true, "cleared selection hides panel");
selected = soldier; Events.UnitSelectionChanged.Fire();
Events.SerialEventEnterCityScreen.Fire(); eq(Controls.ExposurePanel.hidden, true);
Events.SerialEventExitCityScreen.Fire(); eq(Controls.ExposurePanel.hidden, false);
before = savedValues["RealisticTerrain.v1.Player.0"];
Events.SerialEventUnitInfoDirty.Fire();
eq(savedValues["RealisticTerrain.v1.Player.0"], before, "UI dirty event is read-only");
selected = builder; Events.UnitSelectionChanged.Fire();
eq(Controls.ConstructionPanel.hidden, false, "worker shows construction panel");
eq(Controls.ExposurePanel.hidden, true, "worker hides military exposure panel");
eq(Controls.ConstructionButton.disabled, true, "Ministry locks worker button");
Controls.ConstructionButton.callback(); eq(land.progress, 0, "stale click cannot bypass gate");
hasMinistry = true; GameEvents.CityConstructed.Fire();
eq(Controls.ConstructionButton.disabled, false, "completed Ministry unlocks button");
Events.SerialEventUnitInfoDirty.Fire(); eq(land.progress, 0, "UI refresh never contributes work");
Controls.ConstructionButton.callback();
eq(land.progress, 100, "UI click reaches real construction adapter");
eq(builder.moves, 0, "UI click consumes movement");
eq(Controls.ConstructionButton.disabled, false, "cancel remains available after work");
eq(Controls.ConstructionButtonLabel.text, "TXT_KEY_RT_BUILD_CANCEL", "button exposes cancellation");
Events.SerialEventEnterCityScreen.Fire(); eq(Controls.ConstructionPanel.hidden, true, "city view hides worker panel");
Events.SerialEventExitCityScreen.Fire(); eq(Controls.ConstructionPanel.hidden, false, "exiting city restores worker panel");
RT_ConstructionOrders.Cancel(builder);
turn = turn + 1; builder.moves = 120; land.progress = 0;
land.owner, land.terrain, land.feature, land.river, land.adjacent = 0, I.TERRAIN_DESERT, -1, true, {};
local works = false;
land.GetWorkingCity = function() return { GetOwner = function() return 0; end,
    GetNumBuilding = function() return works and 1 or 0; end }; end;
Events.SerialEventUnitInfoDirty.Fire();
eq(Controls.IrrigationButton.disabled, true, "local works locks irrigation button");
Controls.IrrigationButton.callback(); eq(land.progress, 0, "stale irrigation click cannot bypass works");
works = true; Events.SerialEventUnitInfoDirty.Fire();
eq(Controls.IrrigationButton.disabled, false, "works and source unlock irrigation button");
Controls.IrrigationButton.callback();
eq(land.progress, 100, "irrigation button starts actual construction");
eq(RT_ConstructionOrders.IsOrdered(builder, "irrigation"), true, "UI preserves irrigation order kind");
eq(Controls.IrrigationButtonLabel.text, "TXT_KEY_RT_BUILD_CANCEL", "irrigation button offers cancel");
Events.SerialEventUnitInfoDirty.Fire(); eq(land.progress, 100, "irrigation UI refresh adds no work");
Controls.IrrigationButton.callback(); eq(RT_ConstructionOrders.IsOrdered(builder), false, "UI cancels irrigation after movement spent");
selected = nil; Events.UnitSelectionCleared.Fire();
eq(Controls.ConstructionPanel.hidden, true, "clearing selection hides worker panel");
-- RT alone queries an empty bridge; an optional service adds tile-only shelter.
G = RT_Gameplay;
local remote = plot(200, I.TERRAIN_DESERT);
local defender = unit(200, 0, remote); G.OnUnitSetXY(0, defender.id);
for _ = 1, 5 do advance(); end
eq(inspect(defender).env.outpostShelter, false, "RT alone has no outpost shelter");
eq(inspect(defender).stage, 2);
local intact = true;
LuaEvents.RO_Query.Add(function(q)
    if q.kind == "shelter" then q.value = intact and q.owner == 0 and q.plot == 200; end
end);
eq(remote:GetRouteType(), -1, "test outpost has no road");
eq(inspect(defender).env.outpostShelter, true);
eq(inspect(defender).stage, 2, "query does not instantly erase exposure");
local priorDamage = defender.damage;
advance(); eq(inspect(defender).state.heat, 0, "shelter clears exposure at next owner turn");
eq(defender.damage, priorDamage, "shelter prevents exposure damage without healing");
eq(defender:IsHasPromotion(I.PROMOTION_RT_EXHAUSTED), false);
intact = false; advance(); eq(inspect(defender).state.heat, 1, "pillage restarts exposure");
intact = true; relocated(defender, desert); advance();
eq(inspect(defender).env.outpostShelter, false, "moving away loses shelter");
eq(inspect(defender).state.heat, 2);
print("Game adapter + UI + optional shelter: " .. count .. " assertions passed");
