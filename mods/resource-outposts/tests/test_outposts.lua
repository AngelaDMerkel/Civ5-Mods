-- Exercise the real outpost adapter, orders, AI and controls against a small
-- engine model. Native accounting is modeled separately from the Lua ledger.
local count = 0;
local function eq(a, b, why) count = count + 1; assert(a == b, (why or "check") .. ": " .. tostring(a) .. " ~= " .. tostring(b)); end
local function yes(a, why) eq(not not a, true, why); end
local function iterator(list) local n = 0; return function() n = n + 1; return list[n]; end; end
local function database(rows)
    local t = {}; for _, r in ipairs(rows) do if r.ID then t[r.ID] = r; end; if r.Type then t[r.Type] = r; end end
    return setmetatable(t, { __call = function(_, query)
        local matches = {}; for _, r in ipairs(rows) do
            local valid = true; for k, v in pairs(query or {}) do if r[k] ~= v then valid = false; end end
            if valid then matches[#matches + 1] = r; end
        end; return iterator(matches);
    end });
end
local turn, active, values, activated = 0, 0, {}, {};
Game = { GetGameTurn = function() return turn; end, GetActivePlayer = function() return active; end };
GameDefines = { MAX_CIV_PLAYERS = 3 };
DomainTypes = { DOMAIN_LAND = 0, DOMAIN_SEA = 1 };
MissionTypes = { MISSION_MOVE_TO = 1, MISSION_BUILD = 2, MISSION_FORTIFY = 3, MISSION_HEAL = 4 };
OrderTypes = { ORDER_TRAIN = 1 }; NotificationTypes = { NOTIFICATION_GENERIC = 1 };
Locale = { ConvertTextKey = function(key, ...) return key .. ":" .. table.concat({...}, ","); end };
GameInfoTypes = { TECH_ENGINEERING = 10, TECH_MINING = 11, TECH_BRONZE_WORKING = 12, TECH_CALENDAR = 13,
    TECH_ATOMIC_THEORY = 14, BUILD_RT_RESOURCE_OUTPOST = 20, BUILD_RT_RELIEF_STATION = 21,
    BUILD_REPAIR = 22, BUILD_MINE = 23, BUILD_PLANTATION = 24, BUILD_FORT = 25,
    IMPROVEMENT_RT_RESOURCE_OUTPOST = 30, IMPROVEMENT_RT_RELIEF_STATION = 31,
    IMPROVEMENT_MINE = 32, IMPROVEMENT_PLANTATION = 33, TERRAIN_DESERT = 80,
    UNIT_WORKER = 40, UNIT_WARRIOR = 41, UNIT_UNIQUE_WARRIOR = 42, UNITCLASS_WORKER = 50, UNITCLASS_WARRIOR = 51,
    BUILDING_CARAVANSARY = 60, FEATURE_FOREST = 70 };
local I = GameInfoTypes;
local eraRows = {};
for n, name in ipairs({ "ANCIENT", "CLASSICAL", "MEDIEVAL", "RENAISSANCE", "INDUSTRIAL", "MODERN", "POSTMODERN", "FUTURE" }) do
    I["ERA_" .. name], I["IMPROVEMENT_RO_OUTPOST_" .. name] = n - 1, 99 + n;
    eraRows[n] = { EraType = "ERA_" .. name, ImprovementType = "IMPROVEMENT_RO_OUTPOST_" .. name };
end
GameInfo = {
    RO_OutpostEras = database(eraRows),
    Leaders = { [0] = { Type = "LEADER_TEST" }, [1] = { Type = "LEADER_BONUS" } },
    Leader_Traits = database({ { LeaderType = "LEADER_BONUS", TraitType = "TRAIT_BONUS" } }),
    Traits = { TRAIT_BONUS = { Type = "TRAIT_BONUS" } },
    Trait_Terrains = database({ { TraitType = "TRAIT_BONUS", TerrainType = "TERRAIN_DESERT", StrategicResourceQuantityModifier = 100 } }),
    Trait_ResourceQuantityModifiers = database({ { TraitType = "TRAIT_BONUS", ResourceType = "RESOURCE_IRON", ResourceQuantityModifier = 100 } }),
    Policies = database({ { ID = 1, StrategicResourceMod = 200 } }),
    Buildings = database({ { ID = 61, ExtraLuxuries = 1 } }),
    Improvements = database({ { ID = 32, Type = "IMPROVEMENT_MINE", Description = "Mine" }, { ID = 33, Type = "IMPROVEMENT_PLANTATION", Description = "Plantation" } }),
    Resources = database({
        { ID = 1, Type = "RESOURCE_IRON", ResourceClassType = "RESOURCECLASS_RUSH", TechReveal = "TECH_BRONZE_WORKING", TechCityTrade = "TECH_BRONZE_WORKING", Description = "Iron" },
        { ID = 2, Type = "RESOURCE_SILK", ResourceClassType = "RESOURCECLASS_LUXURY", TechCityTrade = "TECH_CALENDAR", Description = "Silk" },
        { ID = 3, Type = "RESOURCE_WHEAT", ResourceClassType = "RESOURCECLASS_BONUS" },
        { ID = 4, Type = "RESOURCE_URANIUM", ResourceClassType = "RESOURCECLASS_MODERN", TechReveal = "TECH_ATOMIC_THEORY", TechCityTrade = "TECH_ATOMIC_THEORY" },
        { ID = 5, Type = "RESOURCE_ARTIFACTS", ResourceClassType = "RESOURCECLASS_RUSH" },
    }),
    Improvement_ResourceTypes = database({
        { ImprovementType = "IMPROVEMENT_MINE", ResourceType = "RESOURCE_IRON", ResourceTrade = true },
        { ImprovementType = "IMPROVEMENT_MINE", ResourceType = "RESOURCE_URANIUM", ResourceTrade = true },
        { ImprovementType = "IMPROVEMENT_PLANTATION", ResourceType = "RESOURCE_SILK", ResourceTrade = true },
    }),
    Builds = database({
        { ID = 20, Type = "BUILD_RT_RESOURCE_OUTPOST", ImprovementType = "IMPROVEMENT_RT_RESOURCE_OUTPOST", PrereqTech = "TECH_ENGINEERING" },
        { ID = 21, Type = "BUILD_RT_RELIEF_STATION", PrereqTech = "TECH_ENGINEERING" },
        { ID = 23, Type = "BUILD_MINE", ImprovementType = "IMPROVEMENT_MINE", PrereqTech = "TECH_MINING" },
        { ID = 24, Type = "BUILD_PLANTATION", ImprovementType = "IMPROVEMENT_PLANTATION", PrereqTech = "TECH_CALENDAR" },
    }),
    Unit_Builds = database({ { UnitType = "UNIT_WORKER", BuildType = "BUILD_FORT" } }),
    BuildFeatures = database({ { BuildType = "BUILD_RT_RESOURCE_OUTPOST", FeatureType = "FEATURE_FOREST", PrereqTech = "TECH_MINING" },
        { BuildType = "BUILD_MINE", FeatureType = "FEATURE_FOREST", PrereqTech = "TECH_MINING", Remove = true } }),
    Civilizations = { [0] = { Type = "CIV_TEST" } },
    Civilization_UnitClassOverrides = database({ { CivilizationType = "CIV_TEST", UnitClassType = "UNITCLASS_WARRIOR", UnitType = "UNIT_UNIQUE_WARRIOR" } }),
    UnitClasses = { UNITCLASS_WORKER = { DefaultUnit = "UNIT_WORKER" }, UNITCLASS_WARRIOR = { DefaultUnit = "UNIT_WARRIOR" } },
    Units = database({
        { ID = 40, Type = "UNIT_WORKER", Class = "UNITCLASS_WORKER", Domain = "DOMAIN_LAND", Combat = 0, RangedCombat = 0 },
        { ID = 41, Type = "UNIT_WARRIOR", Class = "UNITCLASS_WARRIOR", Domain = "DOMAIN_LAND", Combat = 8, RangedCombat = 0 },
        { ID = 42, Type = "UNIT_UNIQUE_WARRIOR", Class = "UNITCLASS_WARRIOR", Domain = "DOMAIN_LAND", Combat = 10, RangedCombat = 0 },
    }),
};
Modding = { GetActivatedMods = function() return activated; end, OpenSaveData = function() return {
    GetValue = function(key) assert(type(key) == "string", "SaveData.GetValue requires dot syntax"); return values[key]; end,
    SetValue = function(key, value) assert(type(key) == "string", "SaveData.SetValue requires dot syntax"); values[key] = value; end,
}; end };
local function events()
    return setmetatable({}, { __index = function(t, k)
        local callbacks = {}; local e = { Add = function(f) callbacks[#callbacks + 1] = f; end,
            Fire = function(...) for _, f in ipairs(callbacks) do f(...); end end };
        setmetatable(e, { __call = function(_, ...) e.Fire(...); end });
        rawset(t, k, e); return e;
    end });
end
GameEvents, Events, LuaEvents = events(), events(), events();
Teams, Players = {}, {};
local plots = {};
for id = 0, 2 do
    local team = { techs = {}, wars = {} }; Teams[id] = team;
    function team:GetTeamTechs() return { HasTech = function(_, tech) return self.techs[tech] or false; end }; end
    function team:IsAtWar(other) return self.wars[other] or false; end
    local player = { id = id }; Players[id] = player;
    function player:IsAlive() return not self.dead; end
    function player:IsHuman() return self.id == 0; end
    function player:IsBarbarian() return self.id == 2; end
    function player:IsTurnActive() return self.active ~= false; end
    function player:GetTeam() return self.id; end
    function player:GetCurrentEra() return self.era; end
    function player:GetCivilizationType() return 0; end
    function player:GetCivilizationShortDescription() return "Civ " .. self.id; end
    function player:GetUnitByID(id) return self.units[id]; end
    function player:Units() local list = {}; for _, u in pairs(self.units) do list[#list + 1] = u; end; return iterator(list); end
    function player:Cities() return iterator(self.cities); end
    function player:GetCapitalCity() return self.cities[1]; end
    function player:GetLeaderType() return self.leader; end
    function player:HasPolicy(id) return self.policies[id] or false; end
    function player:IsPolicyBlocked(id) return self.blockedPolicies[id] or false; end
    function player:GetResourceExport(id) return self.exports[id] or 0; end
    function player:GetNumResourceTotal(id, imports)
        local factor = id ~= 2 and self:HasPolicy(1) and not self:IsPolicyBlocked(1) and 2 or 1;
        return (self.resources[id] or 0) * factor - self:GetResourceExport(id) + (imports and self.imports[id] or 0);
    end
    function player:GetNumResourceAvailable(id) return self:GetNumResourceTotal(id, true) - (self.used[id] or 0); end
    function player:ChangeNumResourceTotal(id, delta)
        self.resources[id] = (self.resources[id] or 0) + delta; self.changes = self.changes + 1;
        if self.reenter then RO_Outposts.Reconcile(); end
    end
    function player:ChangeBaseBuildingGoldMaintenance(delta) self.maintenance = self.maintenance + delta; end
    function player:CalculateGoldRate() return self.income - self.maintenance; end
    function player:GetGold() return self.gold; end
    function player:CountNumBuildings() return 0; end
    function player:GetUnitClassMaking(id) return self.making[id] or 0; end
    function player:AddNotification(...) self.notices[#self.notices + 1] = {...}; end
end
local function tradesResource(improvement)
    return RO_Eras.IsType(improvement) or improvement == I.IMPROVEMENT_MINE or improvement == I.IMPROVEMENT_PLANTATION;
end
local function nativeTradeTech(p)
    local r = GameInfo.Resources[p.resource];
    return p.owner >= 0 and r and (not r.TechCityTrade or Teams[p.owner].techs[I[r.TechCityTrade]]);
end
for id = 0, 18 do
    local p = { id = id }; plots[id] = p;
    function p:GetPlotIndex() return self.id; end
    function p:GetX() return self.id; end
    function p:GetY() return 0; end
    function p:GetOwner() return self.owner; end
    function p:GetPlotCity() return self.city; end
    function p:GetWorkingCity() return self.workingCity or self.city; end
    function p:GetTerrainType() return self.terrain; end
    function p:IsWater() return self.water or false; end
    function p:IsMountain() return self.mountain or false; end
    function p:IsImpassable() return self.impassable or false; end
    function p:SetImprovementType(value, builder)
        if value == self.improvement then return; end
        -- Stock CvPlot order matters: reset pillage using the NEW improvement,
        -- connect its resource, then remove the OLD credit and city link.
        local had, has = tradesResource(self.improvement), tradesResource(value);
        local gift = builder ~= nil and builder >= 0 and builder ~= self.owner;
        self.improvement, self.upgrade = value, 0;
        self.setCalls = self.setCalls + 1;
        self:SetImprovementPillaged(false);
        if self.nativeAccounting and self.owner >= 0 then
            if has and (nativeTradeTech(self) or gift) then
                Players[self.owner]:ChangeNumResourceTotal(self.resource, self.nativeQuantity or self.quantity);
                self.linked = true;
            end
            if had and (nativeTradeTech(self) or self.gift) then
                Players[self.owner]:ChangeNumResourceTotal(self.resource, -(self.nativeQuantity or self.quantity));
                self.linked = false;
            end
        end
        self.gift = gift;
        if self.reenter then Events.SerialEventGameDataDirty.Fire(); end
    end
    function p:SetImprovementPillaged(value)
        if self.pillaged == value then return; end
        self.pillaged = value;
        if self.nativeAccounting and nativeTradeTech(self) and tradesResource(self.improvement) then
            Players[self.owner]:ChangeNumResourceTotal(self.resource, (value and -1 or 1) * (self.nativeQuantity or self.quantity));
            self.linked = not value;
        end
        if self.reenter then Events.SerialEventGameDataDirty.Fire(); end
    end
    function p:GetUpgradeProgress() return self.upgrade; end
    function p:SetUpgradeProgress(value) self.upgrade = value; end
    function p:GetImprovementType() return self.improvement; end
    function p:IsImprovementPillaged() return self.pillaged or false; end
    function p:GetFeatureType() return self.feature or -1; end
    function p:GetNumResource() return self.quantity; end
    function p:GetResourceType(team)
        local r = GameInfo.Resources[self.resource];
        if r and r.TechReveal and not Teams[team].techs[I[r.TechReveal]] then return -1; end
        return self.resource;
    end
    function p:GetNumUnits() return #self.units; end
    function p:GetUnit(i) return self.units[i + 1]; end
    function p:IsRevealed() return self.revealed; end
    function p:IsVisible() return self.visible; end
    function p:CanBuild() return not self.city and not self.impassable and not self.noBuild; end
    function p:GetBuildProgress(id) return self.progress[id] or 0; end
    function p:GetBuildTime() return self.total; end
    function p:ChangeBuildProgress(id, amount)
        self.progress[id] = (self.progress[id] or 0) + amount;
        if self.progress[id] >= self.total then
            self:SetImprovementType(I[GameInfo.Builds[id].ImprovementType] or I.IMPROVEMENT_RT_RELIEF_STATION);
            for feature in GameInfo.BuildFeatures { BuildType = GameInfo.Builds[id].Type } do
                if I[feature.FeatureType] == self.feature and feature.Remove then self.feature = -1; end
            end
            self.progress[id] = 0; return true;
        end; return false;
    end
end
Map = { GetNumPlots = function() return 19; end, GetPlotByIndex = function(id) return plots[id]; end,
    GetPlot = function(x) return plots[x]; end, PlotDistance = function(x, y, a, b) return math.abs(x-a); end,
    PlotDirection = function(x, y, d) if d == 0 then return plots[x-1]; elseif d == 1 then return plots[x+1]; end end };
local function relocate(u, p)
    if u.plot then for i, other in ipairs(u.plot.units) do if u == other then table.remove(u.plot.units, i); break; end end end
    u.plot = p; p.units[#p.units + 1] = u;
end
local function unit(id, owner, p, worker)
    local u = { id = id, owner = owner, birth = turn, kind = worker and I.UNIT_WORKER or I.UNIT_WARRIOR,
        moves = 120, damage = 0, rate = 100, build = -1, missions = {}, domain = DomainTypes.DOMAIN_LAND };
    function u:GetID() return self.id; end
    function u:GetOwner() return self.owner; end
    function u:GetOriginalOwner() return self.owner; end
    function u:GetGameTurnCreated() return self.birth; end
    function u:GetUnitType() return self.kind; end
    function u:GetTeam() return Players[self.owner]:GetTeam(); end
    function u:GetDomainType() return self.domain; end
    function u:IsCombatUnit() return self.kind ~= I.UNIT_WORKER; end
    function u:IsDelayedDeath() return self.dead or false; end
    function u:IsEmbarked() return self.embarked or false; end
    function u:IsAutomated() return self.automated or false; end
    function u:IsBusy() return self.busy or false; end
    function u:GetBuildType() return self.build; end
    function u:GetPlot() return self.plot; end
    function u:GetMoves() return self.moves; end
    function u:GetDamage() return self.damage; end
    function u:GetMaxHitPoints() return self.maxHP or 100; end
    function u:GetName() return GameInfo.Units[self.kind].Type; end
    function u:WorkRate() return self.moves > 0 and self.rate or 0; end
    function u:FinishMoves() self.moves = 0; end
    function u:CanFortify() return true; end
    function u:CanMoveThrough(p) return not p.water and not p.mountain and not self.cannotMove; end
    function u:CanBuild(p, build) return build == I.BUILD_REPAIR and p.pillaged; end
    function u:PushMission(mission, x, y)
        self.missions[#self.missions + 1] = { mission, x, y };
        if mission == MissionTypes.MISSION_MOVE_TO then
            if not self.stuck then relocate(self, plots[x]); GameEvents.UnitSetXY.Fire(self.owner, self.id); end
        elseif mission == MissionTypes.MISSION_BUILD then self.plot.pillaged = false; GameEvents.BuildFinished.Fire(self.owner, self.plot.id, 0, -1);
        elseif mission == MissionTypes.MISSION_FORTIFY then self.fortified = true;
        elseif mission == MissionTypes.MISSION_HEAL then self.healing = true; return; end
        self.moves = 0;
    end
    Players[owner].units[id] = u; relocate(u, p); return u;
end
local function city(owner, p)
    local c = { orders = {} };
    function c:Plot() return p; end
    function c:CanTrain() return true; end
    function c:GetNumBuilding(id) return self.buildings and self.buildings[id] or 0; end
    function c:PushOrder(order, item) self.orders[#self.orders + 1] = {order, item};
        Players[owner].making[I[GameInfo.Units[item].Class]] = 1;
    end
    p.city, p.owner = c, owner; table.insert(Players[owner].cities, c); return c;
end
local O, B, Orders, AI;
local function loadModules()
    for _, name in ipairs({ "RO_Serialize", "RO_Integration", "RO_Eras", "RO_Outposts", "RO_Orders", "RO_AI", "RO_Management" }) do
        dofile(TEST_ROOT .. "/mods/resource-outposts/src/Lua/" .. name .. ".lua");
    end
    O, B, Orders, AI = RO_Outposts, RO_Outposts, RO_Orders, RO_AI;
end
local function reset()
    turn, active, values, activated = 0, 0, {}, {};
    GameEvents, Events, LuaEvents = events(), events(), events();
    for id, player in pairs(Players) do
        player.dead, player.active, player.reenter = false, true, false;
        player.maintenance, player.gold, player.income = 0, 200, 30;
        player.era = 0;
        player.leader, player.policies, player.blockedPolicies, player.exports, player.imports = 0, {}, {}, {}, {};
        player.units, player.cities, player.resources, player.used, player.making, player.notices, player.changes = {}, {}, {}, {}, {}, {}, 0;
        Teams[id].wars, Teams[id].techs = {}, { [10]=true, [11]=true, [12]=true, [13]=true };
    end
    for _, p in pairs(plots) do
        p.owner, p.resource, p.quantity, p.improvement = -1, -1, 1, -1;
        p.city, p.water, p.mountain, p.impassable, p.pillaged, p.feature = nil, false, false, false, false, -1;
        p.units, p.progress, p.total, p.revealed, p.visible = {}, {}, 300, true, true;
        p.terrain, p.workingCity, p.nativeAccounting, p.reenter, p.noBuild = 80, nil, false, false, false;
        p.upgrade, p.setCalls, p.linked, p.gift, p.nativeQuantity = 0, 0, false, false, nil;
    end
    loadModules();
end
local function total(owner, resource) return Players[owner].resources[resource] or 0; end
local function build(owner, p, resource, quantity)
    p.resource, p.quantity, p.improvement = resource or 1, quantity or 6, I.IMPROVEMENT_RT_RESOURCE_OUTPOST;
    O.OnBuilt(owner, p.id, 0, p.improvement);
end
local function nextTurn(owner)
    turn = turn + 1;
    for _, player in pairs(Players) do for _, u in pairs(player.units) do u.moves = 120; end end
    GameEvents.PlayerDoTurn.Fire(owner);
end

reset();
local p, worker = plots[4], unit(1, 0, plots[4], true);
p.resource, p.quantity = 1, 6;
yes(O.Status(worker), "neutral iron valid without Ministry");
Teams[0].techs[10] = false; eq(O.Status(worker), false, "Engineering required"); Teams[0].techs[10] = true;
Teams[0].techs[12] = false; eq(O.Status(worker), false, "hidden resource rejected"); Teams[0].techs[12] = true;
Teams[0].techs[11] = false; eq(O.Status(worker), false, "normal mining tech required"); Teams[0].techs[11] = true;
for _, owner in ipairs({0,1}) do p.owner = owner; eq(O.Status(worker), false, "owned land rejected"); end; p.owner = -1;
for _, resource in ipairs({-1,3,4,5}) do p.resource = resource; eq(O.Status(worker), false, "invalid or hidden deposit"); end; p.resource = 1;
p.water = true; eq(O.Status(worker), false); p.water = false;
p.mountain = true; eq(O.Status(worker), false); p.mountain = false;
p.improvement = 99; eq(O.Status(worker), false, "no replacement of existing improvement"); p.improvement = -1;
worker.automated = true; eq(O.Work(worker), false); worker.automated = false;
worker.busy = true; eq(O.Work(worker), false); worker.busy = false;
worker.moves = 0; eq(O.Work(worker), false); worker.moves = 120;
worker.embarked = true; eq(O.Work(worker), false); worker.embarked = false;
active = 1; eq(O.Work(worker), false); active = 0;
yes(Orders.Start(worker, "outpost"), "start persistent outpost construction");
eq(p:GetBuildProgress(O.build), 100); eq(total(0, 1), 0, "unfinished structure has no resource");
Orders.Initialize(); O.Initialize();
nextTurn(0); eq(p:GetBuildProgress(O.build), 200, "automatic work");
worker.moves = 120; Orders.OnTurn(0); eq(p:GetBuildProgress(O.build), 200, "duplicate callback guard");
loadModules(); yes(Orders.IsOrdered(worker, "outpost"), "order kind survives reload");
Orders.OnTurn(0); eq(p:GetBuildProgress(O.build), 200, "reload cannot double work");
turn = 2; worker.moves = 120; Orders.OnTurn(0);
eq(p.improvement, RO_Eras.Target(0)); eq(O.Owner(p), 0); eq(p.owner, -1, "no cultural ownership");
eq(plots[3].owner, -1, "neighbors remain neutral"); eq(total(0, 1), 6, "whole deposit credited");
eq(Orders.IsOrdered(worker), false); eq(worker.moves, 0);
local changes = Players[0].changes;
O.Reconcile(); O.Reconcile(); loadModules(); O.Reconcile();
eq(total(0, 1), 6, "idempotent save reload"); eq(Players[0].changes, changes);
Players[0].used[1] = 4; Players[0]:ChangeNumResourceTotal(1, 3); O.Reconcile();
eq(total(0, 1), 9, "external resources preserved");
Players[0].reenter = true; p.pillaged = true; O.Reconcile();
eq(total(0, 1), 3, "pillage removes only outpost credit despite consumption");
p.pillaged = false; O.OnBuilt(1, p.id, 0, -1);
eq(O.Owner(p), 0, "foreign repair cannot take ownership"); eq(total(0, 1), 9);
Players[0].reenter = false;
build(0, plots[7], 1, 2); eq(total(0, 1), 11, "multiple deposits aggregate");
build(0, plots[8], 2, 1); eq(total(0, 2), 1, "luxury access");
p.improvement = -1; O.Reconcile(); eq(total(0, 1), 5, "destroyed deposit removed");
eq(O.state.sites[p.id], nil, "stale ownership pruned");
build(1, p); eq(total(1, 1), 6, "rebuild gets new owner");
-- Simulate the engine crediting an annexed ResourceTrade improvement, then
-- deliver the normal border event. Lua must withdraw only its old contribution.
p.owner = 0; Players[0]:ChangeNumResourceTotal(1, 6); O.Reconcile();
eq(total(1, 1), 0); eq(total(0, 1), 11, "annexation not double counted"); eq(O.Owner(p), 0);
p.owner = -1; Players[0]:ChangeNumResourceTotal(1, -6); O.Reconcile();
eq(total(0, 1), 11, "return to neutral retains last territorial owner");
Players[0].dead = true; O.Reconcile(); eq(total(0, 1), 3, "dead player's contribution withdrawn"); eq(total(0, 2), 0);

reset(); build(0, plots[4]);
local enemy = unit(2, 1, plots[4], false);
O.OnMoved(1, 2); eq(O.Owner(plots[4]), 0, "peaceful occupation does not capture");
Teams[0].wars[1], Teams[1].wars[0] = true, true;
O.OnMoved(1, 2); eq(O.Owner(plots[4]), 1, "wartime military capture");
eq(total(0, 1), 0); eq(total(1, 1), 6); eq(#Players[0].notices, 1);
O.OnMoved(1, 2); eq(#Players[0].notices, 1, "capture notification not repeated");
enemy.kind = I.UNIT_WORKER; build(0, plots[6]); relocate(enemy, plots[6]); O.OnMoved(1, 2);
eq(O.Owner(plots[6]), 0, "civilian cannot capture");
enemy.kind, enemy.embarked = I.UNIT_WARRIOR, true; O.OnMoved(1, 2); eq(O.Owner(plots[6]), 0, "embarked unit cannot capture");
relocate(enemy, plots[12]);
local barb = unit(3, 2, plots[6], false); Teams[0].wars[2] = true;
O.OnMoved(2, 3); eq(O.Owner(plots[6]), 0, "barbarian blockades but never owns claim"); eq(total(0, 1), 0);
relocate(barb, plots[13]); O.OnMoved(2, 3); eq(total(0, 1), 6, "departed blockade restores extraction");
plots[6].pillaged = true; enemy.embarked = false; relocate(enemy, plots[6]); O.OnMoved(1, 2);
eq(O.Owner(plots[6]), 1, "pillaged site transfers"); eq(total(1, 1), 6, "captured ruin supplies nothing");
plots[6].pillaged = false; O.OnBuilt(1, 6, 0, -1); eq(total(1, 1), 12);
Teams[1].techs[12] = false; O.Reconcile(); eq(total(1, 1), 0, "capture requires recipient's technology");
Teams[1].techs[12] = true; O.Reconcile(); eq(total(1, 1), 12);
O.Initialize(); plots[6].pillaged = true; Events.SerialEventGameDataDirty.Fire(); eq(total(1, 1), 6, "dirty event updates resource immediately");
plots[6].pillaged = false; GameEvents.PlayerDoTurn.Fire(0); eq(total(1, 1), 12, "unseen engine changes caught next turn");
print("Outpost construction, accounting and capture: " .. count .. " assertions passed");

-- AI world: a nearby surplus and a farther missing luxury. Leave one worker
-- for the homeland; protect the city garrison and existing Caravansary patrol.
reset(); Players[1].era = I.ERA_MODERN;
local capital = city(1, plots[0]);
local w1, w2 = unit(10, 1, plots[1], true), unit(11, 1, plots[0], true);
local guard = unit(12, 1, plots[1], false);
local cityGuard = unit(13, 1, plots[0], false);
plots[2].resource, plots[2].quantity = 1, 2;
plots[5].resource = 2; Players[1].resources[1] = 10;
plots[7].resource, plots[7].revealed = 1, false;
plots[9].resource = 4; -- unrevealed uranium even on revealed land
O.Initialize(); Orders.Initialize(); AI.Initialize();
AI.OnTurn(1);
eq(O.state.ai[1].workers[10].target, 5, "missing luxury preferred over nearby surplus");
eq(O.state.ai[1].workers[11], nil, "one worker stays home"); yes(AI.Reserved(w1), "trade logistics reservation");
eq(w1:GetPlot().id, 2, "worker uses revealed safe land step");
local moves = #w1.missions; AI.OnTurn(1); eq(#w1.missions, moves, "AI duplicate-turn guard");
for _ = 1, 8 do nextTurn(1); end
eq(plots[5].improvement, RO_Eras.Target(1), "AI completes real worker construction"); eq(total(1, 2), 1);
eq(#cityGuard.missions, 0, "city garrison never reassigned");
for _ = 1, 7 do nextTurn(1); end
eq(guard:GetPlot(), plots[5], "AI garrisons completed outpost"); yes(guard.fortified, "AI fortifies");
yes(AI.Reserved(guard), "guard remains reserved");
-- Simulated Lua reload preserves both native total and AI reservations.
loadModules(); O.Reconcile(); yes(AI.Reserved(guard)); eq(total(1, 2), 1);
plots[5].pillaged = true; O.Reconcile(); eq(total(1, 2), 0);
for _ = 1, 10 do turn = turn + 1; for u in Players[1]:Units() do u.moves = 120; end; Orders.OnTurn(1); AI.OnTurn(1); O.Reconcile(); end
eq(plots[5].pillaged, false, "AI repairs its outpost"); eq(total(1, 2), 1);
guard.birth = guard.birth + 99; eq(AI.Reserved(guard), false, "reused unit ID cannot inherit reservation");

reset(); capital = city(1, plots[0]);
local solo = unit(20, 1, plots[1], true); plots[3].resource = 1;
AI.OnTurn(1); eq(#solo.missions, 0, "sole homeland worker retained");
eq(capital.orders[1][2], I.UNIT_WORKER, "extra expedition worker commissioned through city production");
for _ = 1, 12 do turn = turn + 1; AI.OnTurn(1); end
eq(#capital.orders, 1, "pending worker is not queued twice");

reset(); capital = city(1, plots[0]); build(1, plots[3]);
AI.OnTurn(1); eq(capital.orders[1][2], I.UNIT_UNIQUE_WARRIOR, "defender production respects civilization override");
turn = 2; local trained = unit(25, 1, plots[0], false); trained.kind = I.UNIT_UNIQUE_WARRIOR;
AI.OnTurn(1); yes(AI.Reserved(trained), "newly commissioned defender may leave its production city");
eq(trained:GetPlot(), plots[1], "commissioned defender begins deployment");

reset(); capital = city(1, plots[0]);
w1, w2 = unit(30, 1, plots[1], true), unit(31, 1, plots[0], true);
plots[3].resource = 1; plots[2].water = true;
AI.OnTurn(1); eq(AI.Reserved(w1), false, "AI rejects unreachable island resources");
eq(#capital.orders, 0, "no production spent on unreachable resource");
plots[2].water, plots[2].owner = false, 0; turn = 1; AI.OnTurn(1);
eq(AI.Reserved(w1), false, "AI won't route workers through foreign borders");
plots[2].owner, plots[2].revealed = -1, false; turn = 2; AI.OnTurn(1);
eq(AI.Reserved(w1), false, "AI won't route through unexplored land");
plots[2].revealed = true;
local threat = unit(40, 0, plots[4], false); Teams[1].wars[0] = true;
turn = 3; AI.OnTurn(1); eq(#w1.missions, 0, "AI waits for an escort before approaching visible danger");
relocate(threat, plots[18]); turn = 4; AI.OnTurn(1); yes(AI.Reserved(w1), "expedition resumes when safe");
relocate(threat, plots[4]); turn = 5; AI.OnTurn(1); eq(w1.moves, 0, "new danger holds worker pending escort");

reset(); capital = city(1, plots[0]);
build(1, plots[2]); build(1, plots[3]); build(1, plots[4]);
w1, w2 = unit(35, 1, plots[1], true), unit(36, 1, plots[0], true); plots[6].resource = 2;
AI.OnTurn(1); eq(AI.Reserved(w1), false, "AI site cap prevents unlimited resource spam");
plots[3].pillaged = true; turn = 1; AI.OnTurn(1); yes(AI.Reserved(w1), "site cap still allows repairs");

reset(); capital = city(1, plots[0]); build(0, plots[3]);
guard = unit(50, 1, plots[1], false); Teams[0].wars[1], Teams[1].wars[0] = true, true;
O.Initialize(); AI.Initialize(); AI.OnTurn(1); nextTurn(1); nextTurn(1);
eq(O.Owner(plots[3]), 1, "AI captures undefended enemy outpost"); eq(total(0, 1), 0); eq(total(1, 1), 6);
yes(guard.fortified, "capturing AI holds captured installation");
-- Maintenance belongs to the native treasury, with a separate saved delta.
reset(); Players[0].maintenance = 7; build(0, plots[4]);
eq(Players[0].maintenance, 9, "preserve unrelated building maintenance");
O.Reconcile(); loadModules(); O.Reconcile();
eq(Players[0].maintenance, 9, "reload and repeat reconciliation cannot double upkeep");
eq(#Players[0].notices, 0, "completion and reload don't create loss notices");
plots[4].pillaged = true; O.Reconcile();
eq(Players[0].maintenance, 9, "pillaged sites still cost upkeep");
eq(#Players[0].notices, 1); yes(string.find(Players[0].notices[1][2], "Iron:,-6", 1, true), "notice includes exact loss");
O.Reconcile(); loadModules(); O.Reconcile(); eq(#Players[0].notices, 1, "no repeated loss after reload");
plots[4].pillaged = false; O.Reconcile();
yes(string.find(Players[0].notices[2][2], "Iron:,+6", 1, true), "repair notice includes restored quantity");
eq(O.Abandon(1, plots[4]), false, "can't abandon another player's claim");
Players[0].active = false; eq(O.Abandon(0, plots[4]), false, "can't abandon outside own turn");
Players[0].active = true; yes(O.Abandon(0, plots[4]));
eq(plots[4].improvement, -1); eq(total(0, 1), 0); eq(Players[0].maintenance, 7);
eq(#Players[0].notices, 3); yes(string.find(Players[0].notices[3][2], "ABANDONED"));
O.Reconcile(); eq(Players[0].maintenance, 7, "abandonment refund is not repeated");
build(0, plots[4]); Teams[0].wars[1], Teams[1].wars[0] = true, true;
enemy = unit(92, 1, plots[4], false); O.OnMoved(1, 92);
eq(Players[0].maintenance, 7, "capture releases former owner's upkeep"); eq(Players[1].maintenance, 2);
plots[4].owner = 0; Players[0]:ChangeNumResourceTotal(1, 6); O.Reconcile();
eq(Players[1].maintenance, 0); eq(Players[0].maintenance, 9, "annexation moves upkeep exactly once");
Players[0].dead = true; O.Reconcile(); eq(Players[0].maintenance, 7, "elimination removes outpost maintenance");

-- Budget grows beyond three with the economy and army; no roads in this world.
reset(); capital = city(1, plots[0]);
for n = 1, 8 do unit(100+n, 1, plots[1], false); end
eq(AI.Budget(1), 4, "income supports four posts, not a fixed three");
Players[1].income = 80; eq(AI.Budget(1), 5, "army constrains expansion");
Players[1].income, Players[1].gold = -5, 0; eq(AI.Budget(1), 0, "poor economy stops expansion");
Players[1].income, Players[1].gold = 80, 200;
build(1, plots[2]); build(1, plots[3]); build(1, plots[4]); plots[6].resource = 2;
w1, w2 = unit(120, 1, plots[1], true), unit(121, 1, plots[0], true);
AI.OnTurn(1); yes(AI.Reserved(w1), "fourth site expedition is permitted");

-- A guard replaces a wounded defender; recovery persists and excludes other jobs.
reset(); capital = city(1, plots[0]); build(1, plots[4]);
guard = unit(130, 1, plots[4], false); local replacement = unit(131, 1, plots[1], false);
AI.OnTurn(1); eq(O.state.ai[1].guards[130].target, 4);
guard.damage = 60; turn = 1; guard.moves = 120; AI.OnTurn(1);
yes(O.state.ai[1].recovering[130]); eq(O.state.ai[1].guards[130], nil);
eq(O.state.ai[1].guards[131].target, 4, "healthy guard immediately fills vacancy");
eq(guard:GetPlot(), plots[4], "wounded guard rests when the only home path is occupied");
yes(guard.healing, "blocked recovery uses native healing while awaiting a route");
loadModules(); yes(AI.Reserved(guard), "recovering guard reservation survives reload");
guard.damage = 24; turn = 2; AI.OnTurn(1); eq(O.state.ai[1].recovering[130], nil, "healed guard released");

-- Scarce strategic supplies receive first choice of scarce garrison manpower.
reset(); capital = city(1, plots[0]); build(1, plots[2], 2, 1); build(1, plots[5], 1, 6);
guard = unit(140, 1, plots[1], false); AI.OnTurn(1);
eq(O.state.ai[1].guards[140].target, 5, "scarce iron defended before closer luxury");

-- Escort rendezvous, protected work, and refusal to step onto an enemy's tile.
reset(); capital = city(1, plots[0]); plots[3].resource = 1;
w1, w2 = unit(150, 1, plots[1], true), unit(151, 1, plots[0], true);
guard = unit(152, 1, plots[2], false); threat = unit(153, 0, plots[4], false); Teams[1].wars[0] = true;
O.Initialize(); Orders.Initialize(); AI.Initialize(); AI.OnTurn(1);
eq(guard:GetPlot(), w1:GetPlot(), "escort rendezvous before worker moves");
eq(w1:GetPlot(), plots[1]); yes(AI.Reserved(guard));
nextTurn(1); eq(w1:GetPlot(), plots[2]); eq(guard:GetPlot(), plots[2]);
nextTurn(1); eq(w1:GetPlot(), plots[3]); eq(guard:GetPlot(), plots[3]);
yes(AI.CanWork(w1), "colocated escort permits work near visible threat");
guard.birth = guard.birth + 1; eq(AI.CanWork(w1), false, "recycled escort ID cannot authorize work"); guard.birth = guard.birth - 1;
guard.embarked = true; eq(AI.CanWork(w1), false, "embarked escort cannot protect work"); guard.embarked = false;
eq(AI.Path(plots[3], plots[5], 1, true), nil, "escort cannot path through enemy occupation");
nextTurn(1); eq(plots[3]:GetBuildProgress(O.build), 100);
guard.damage = 60; nextTurn(1);
eq(plots[3]:GetBuildProgress(O.build), 100, "wounded escort pauses automatic construction");
yes(O.state.ai[1].recovering[152]);

-- Stalled expeditions persist their progress and cooldown across reloads.
reset(); capital = city(1, plots[0]); plots[3].resource = 1;
w1, w2 = unit(170, 1, plots[1], true), unit(171, 1, plots[0], true); w1.stuck = true;
AI.OnTurn(1);
for n = 1, AI.STALL_TURNS - 1 do turn = n; w1.moves = 120; AI.OnTurn(1); end
yes(AI.Reserved(w1), "no premature timeout");
loadModules(); turn = AI.STALL_TURNS; w1.moves = 120; AI.OnTurn(1);
eq(AI.Reserved(w1), false, "stalled worker released across save reload");
eq(O.state.ai[1].cooldowns[3], turn + AI.RETRY_TURNS, "destination temporarily avoided");
loadModules(); w1.stuck = false; turn = turn + 1; w1.moves = 120; AI.OnTurn(1);
eq(AI.Reserved(w1), false, "cooldown persists across reload");
turn = AI.STALL_TURNS + AI.RETRY_TURNS; w1.moves = 120; AI.OnTurn(1);
yes(AI.Reserved(w1), "destination reconsidered after cooldown");

reset(); capital = city(1, plots[0]); plots[3].resource = 1;
w1, w2 = unit(172, 1, plots[1], true), unit(173, 1, plots[0], true);
guard = unit(174, 1, plots[1], false); guard.stuck = true;
threat = unit(175, 0, plots[4], false); Teams[1].wars[0] = true;
AI.OnTurn(1);
for n = 1, AI.STALL_TURNS do turn = n; w1.moves = 120; guard.moves = 120; AI.OnTurn(1); end
eq(AI.Reserved(w1), false, "stalled escort releases its worker");
eq(AI.Reserved(guard), false, "stalled escort reservation released");
yes(O.state.ai[1].cooldowns[3]); eq(Orders.IsOrdered(w1), false);

reset(); capital = city(1, plots[0]); build(1, plots[3]);
guard = unit(176, 1, plots[1], false); guard.stuck = true; AI.OnTurn(1);
for n = 1, AI.STALL_TURNS do turn = n; guard.moves = 120; AI.OnTurn(1); end
eq(AI.Reserved(guard), false, "stalled defender released");
yes(O.state.ai[1].cooldowns[3], "guard cannot instantly reclaim failed destination");

-- Work progress refreshes the timer, even on unusually slow builds.
reset(); capital = city(1, plots[0]); plots[3].resource = 1; plots[3].total = 2000;
w1, w2 = unit(177, 1, plots[3], true), unit(178, 1, plots[0], true);
Orders.Initialize(); AI.Initialize(); AI.OnTurn(1);
for _ = 1, 9 do nextTurn(1); end
yes(AI.Reserved(w1), "productive long construction never times out"); eq(plots[3]:GetBuildProgress(O.build), 1000);

-- Nearby safe healing uses percentage health and does not consume rest turns.
reset(); capital = city(1, plots[0]); local nearby = city(1, plots[8]);
guard = unit(180, 1, plots[6], false); guard.damage, guard.maxHP = 100, 200;
eq(AI.DamagePercent(guard), 50, "withdrawal thresholds scale to maximum HP");
eq(AI.RecoveryTarget(guard), plots[8], "nearby city beats distant capital");
plots[5].owner = 1; eq(AI.RecoveryTarget(guard), plots[5], "closer friendly healing tile selected");
local occupant = unit(181, 1, plots[5], false);
eq(AI.RecoveryTarget(guard), plots[8], "occupied military slot avoided");
plots[7].water = true; eq(AI.RecoveryTarget(guard), nil, "water and blocked transit cannot form a healing path");
plots[7].water = false; relocate(occupant, plots[9]);
build(1, plots[6]); guard.damage = 80; AI.OnTurn(1); yes(O.state.ai[1].guards[180]);
guard.damage = 100; turn = 1; guard.moves = 120; AI.OnTurn(1);
yes(O.state.ai[1].recovering[180]); eq(guard:GetPlot(), plots[5]);
turn = 2; guard.moves = 120; AI.OnTurn(1);
yes(guard.healing, "native heal mission issued"); eq(guard.moves, 120, "rest preserves full movement for native healing");
guard.damage = 50; turn = 3; AI.OnTurn(1); yes(O.state.ai[1].recovering[180], "25% damage still recovering");
guard.damage = 49; turn = 4; AI.OnTurn(1); eq(O.state.ai[1].recovering[180], nil, "release above 75% health");

-- Read-only abandonment quotes include imports, exports and quantity modifiers.
reset(); build(0, plots[4]); Players[0].used[1] = 4;
local M = RO_Management;
local quote = M.Preview(0, plots[4]);
eq(quote.loss, 6); eq(quote.before, 2); eq(quote.after, -4); yes(quote.shortage); eq(quote.baseUpkeep, 2);
local savedBefore = values["ResourceOutposts.v1.State"]; local mutations = Players[0].changes;
M.Preview(0, plots[4]); eq(values["ResourceOutposts.v1.State"], savedBefore); eq(Players[0].changes, mutations, "preview never mutates engine resources");
Players[0].imports[1] = 10; quote = M.Preview(0, plots[4]); eq(quote.after, 6); eq(quote.shortage, false, "imports prevent shortage");
Players[0].policies[1] = true; Players[0].exports[1] = 2;
quote = M.Preview(0, plots[4]); eq(quote.loss, 12, "strategic policy multiplier reflected"); eq(quote.before, 16); eq(quote.after, 4);
plots[4].pillaged = true; O.Reconcile(); quote = M.Preview(0, plots[4]); eq(quote.loss, 0, "pillaged site loses no additional resources");
reset(); build(0, plots[4], 2, 1); M = RO_Management;
quote = M.Preview(0, plots[4]); yes(quote.lastLuxury); eq(quote.after, 0);
Players[0].imports[2] = 1; eq(M.Preview(0, plots[4]).lastLuxury, false);
Players[0].imports[2] = 0; Players[0].exports[2] = 1;
eq(M.Preview(0, plots[4]).lastLuxury, false, "already exported luxury is not a new last-copy loss");

reset(); build(0, plots[4]); M = RO_Management; Players[0].leader = 1;
eq(M.Preview(0, plots[4]).loss, 6, "neutral outposts do not receive local trait multipliers");
plots[4].owner = 0; Players[0]:ChangeNumResourceTotal(1, 24); O.Reconcile();
eq(M.Preview(0, plots[4]).loss, 24, "annexed resource and terrain trait multipliers included");
reset(); local bazaarCity = city(0, plots[0]); bazaarCity.buildings = { [61] = 1 };
build(0, plots[4], 2, 1); plots[4].owner, plots[4].workingCity = 0, bazaarCity;
Players[0]:ChangeNumResourceTotal(2, 2); O.Reconcile(); M = RO_Management;
eq(M.Preview(0, plots[4]).loss, 2, "annexed city bonus luxury included");

-- Conversion follows ordinary build legality, resources and feature clearing.
reset(); build(0, plots[4]); p = plots[4]; M = RO_Management;
eq(M.Conversion(0, p), nil, "neutral claims cannot convert");
p.owner = 0; Players[0]:ChangeNumResourceTotal(1, 6); O.Reconcile(); p.nativeAccounting, p.reenter = true, true; O.Initialize();
eq(M.Conversion(0, p), I.BUILD_MINE); eq(M.Convert(1, p), false);
Players[0].active = false; eq(M.Convert(0, p), false); Players[0].active = true;
p.pillaged = true; eq(M.Conversion(0, p), nil, "conversion cannot give a free repair"); p.pillaged = false;
Teams[0].techs[11] = false; eq(M.Conversion(0, p), nil, "normal build technology required"); Teams[0].techs[11] = true;
p.noBuild = true; eq(M.Conversion(0, p), nil, "native build restrictions honored"); p.noBuild = false;
p.feature = I.FEATURE_FOREST;
local oldNotices = #Players[0].notices; yes(M.Convert(0, p));
eq(p.improvement, I.IMPROVEMENT_MINE); eq(p.feature, -1, "normal feature clearing applied");
eq(total(0, 1), 6, "conversion retains native resource access through callbacks");
eq(Players[0].maintenance, 0); eq(O.Owner(p), -1); eq(p.owner, 0, "conversion keeps cultural ownership");
eq(#Players[0].notices, oldNotices, "conversion does not send false resource loss notification");
eq(M.Convert(0, p), false, "cannot repeat conversion refund"); loadModules(); O.Reconcile();
eq(Players[0].maintenance, 0); eq(total(0, 1), 6, "converted save reload stable");

-- Separate UI context globals communicate only through the shared event bus.
reset(); build(0, plots[4]); guard = unit(160, 0, plots[4], false);
local terrainEnv = {};
for key, value in pairs(_G) do if not string.match(key, "^RO_") then terrainEnv[key] = value; end end
terrainEnv._G = terrainEnv;
local function terrainModule(name)
    local chunk = assert(loadfile(RT_LUA(name)));
    setfenv(chunk, terrainEnv); chunk();
end
terrainModule("RT_OutpostBridge"); local bridge = terrainEnv.RT_OutpostBridge;
eq(bridge.Shelter(guard), false, "query before other UI loads is harmless");
RO_Integration.Initialize();
eq(bridge.Shelter(guard), false, "RT installed but disabled adds no shelter");
activated = { { ID = string.upper(RO_Integration.RT_ID), Version = 2 } };
yes(bridge.Shelter(guard), "both mods shelter roadless outpost tile");
eq(terrainEnv.RO_Outposts, nil, "RT context has no RO globals");
eq(total(0, 1), 6); eq(Players[0].maintenance, 2, "integration adds no upkeep");
plots[4].pillaged = true; eq(bridge.Shelter(guard), false, "ruined outpost gives no shelter");
plots[4].pillaged = false; relocate(guard, plots[3]); eq(bridge.Shelter(guard), false, "no adjacent shelter aura");
local foreign = unit(161, 1, plots[4], false); eq(bridge.Shelter(foreign), false, "foreign troops not sheltered");
relocate(guard, plots[4]); yes(bridge.Shelter(guard));
-- Load actual second-mod orders after RO listeners: both directions cancel and guard work.
terrainEnv.RT_Construction = { IsWorker = O.IsWorker, Status = O.Status,
    Work = function(u) u:FinishMoves(); return true, false; end };
terrainModule("RT_ConstructionOrders"); bridge.Initialize();
local terrainOrders = terrainEnv.RT_ConstructionOrders;
p = plots[6]; p.resource = 1; worker = unit(162, 0, p, true);
yes(Orders.Start(worker)); yes(bridge.Reserved(worker), "ordered worker reserved across contexts");
worker.moves = 120; eq(terrainOrders.Start(worker), false, "RT cannot double-work RO's turn");
turn = 1; worker.moves = 120; yes(terrainOrders.Start(worker));
eq(Orders.IsOrdered(worker), false, "RT order cancels prior RO assignment");
worker.moves = 120; eq(Orders.Start(worker), false, "RO cannot double-work RT's turn");
turn = 2; worker.moves = 120; yes(Orders.Start(worker));
eq(terrainOrders.IsOrdered(worker), false, "RO order cancels prior RT assignment");
O.Reconcile(); eq(total(0, 1), 6, "no resource change from optional integration");
print("Outposts including upkeep, AI and isolated mod integration: " .. count .. " assertions passed");

-- Real UI handlers, with other modules already loaded or covered separately.
reset(); p = plots[4]; p.resource = 1; worker = unit(1, 0, p, true);
local function controls() return setmetatable({}, { __index = function(t, k)
    local c = {};
    function c:SetHide(v) self.hidden = v; end
    function c:SetText(v) self.text = v; end
    function c:SetToolTipString(v) self.tooltip = v; end
    function c:SetOffsetVal(x,y) self.offsetX, self.offsetY = x, y; end
    function c:SetDisabled(v) self.disabled = v; end
    function c:RegisterCallback(_, f) self.callback = f; end
    function c:CalculateSize() end
    function c:ReprocessAnchoring() end
    function c:CalculateInternalSize() end
    rawset(t, k, c); return c;
end }); end
Controls = controls();
local rows = {};
InstanceManager = { new = function() return {
    ResetInstances = function() rows = {}; end,
    GetInstance = function() local row = controls(); rows[#rows + 1] = row; return row; end,
}; end };
local selected = worker;
UI = { GetHeadSelectedUnit = function() return selected; end, LookAt = function() end }; Mouse = { eLClick = 1 };
include = function() end;
dofile(TEST_ROOT .. "/mods/resource-outposts/src/UI/RO_UI.lua");
eq(Controls.OutpostButton.disabled, false, "eligible worker sees enabled action");
eq(Controls.ConstructionPanel.offsetY, 64, "standalone build panel position");
activated = { { ID = RO_Integration.RT_ID } }; Events.SerialEventUnitInfoDirty.Fire();
eq(Controls.ConstructionPanel.offsetY, 254, "combined panel clears RT construction panel"); activated = {};
eq(rawget(Controls, "ConstructionButton"), nil, "standalone UI has no Ministry action");
eq(Controls.OutpostPanel.hidden, true, "unfinished tile has no claim status");
local progress = p:GetBuildProgress(O.build); Events.SerialEventUnitInfoDirty.Fire(); eq(p:GetBuildProgress(O.build), progress, "UI refresh is read-only");
Controls.OutpostButton.callback(); yes(Orders.IsOrdered(worker, "outpost"));
yes(string.find(Controls.OutpostButtonLabel.text, "CANCEL"), "cancel label shown");
Controls.OutpostButton.callback(); eq(Orders.IsOrdered(worker), false, "UI cancels order");
turn = 1; worker.moves = 120; Controls.OutpostButton.callback(); nextTurn(0);
eq(p.improvement, RO_Eras.Target(0), "UI-started order completes");
Events.SerialEventUnitInfoDirty.Fire(); eq(Controls.OutpostPanel.hidden, false, "claim status visible");
yes(string.find(Controls.OutpostStatus.text, "ACTIVE"), "extraction status");
Events.SerialEventEnterCityScreen.Fire(); eq(Controls.OutpostPanel.hidden, true); eq(Controls.ConstructionPanel.hidden, true);
Events.SerialEventExitCityScreen.Fire(); eq(Controls.OutpostPanel.hidden, false);
selected = nil; Events.UnitSelectionCleared.Fire(); eq(Controls.OutpostPanel.hidden, true);
Controls.Manage.callback(); eq(Controls.OverviewPanel.hidden, false); eq(#rows, 1);
rows[1].SiteManage.callback(); eq(Controls.OutpostPanel.hidden, false, "manage without selecting a garrison");
Controls.Abandon.callback(); eq(p.improvement, RO_Eras.Target(0), "first click asks confirmation");
Controls.Abandon.callback(); eq(p.improvement, -1, "second click abandons");
eq(Controls.Manage.disabled, true, "last site removed"); eq(Players[0].maintenance, 0);
-- Overview rows represent every owned site and dispatch the correct location.
build(0, plots[2], 1, 6); build(0, plots[7], 2, 1); build(1, plots[9]);
guard = unit(220, 0, plots[7], false); guard.damage = 20; plots[7].pillaged = true; O.Reconcile();
local located; UI.LookAt = function(plot) located = plot; end;
Events.SerialEventGameDataDirty.Fire(); eq(#rows, 2, "overview excludes foreign sites");
yes(string.find(rows[1].Title.text, "2,0,6,Iron", 1, true));
yes(string.find(rows[2].Detail.text, "PILLAGED", 1, true));
yes(string.find(rows[2].Detail.text, "UNIT_WARRIOR,80,100", 1, true));
yes(string.find(Controls.OverviewSummary.text, "2,4", 1, true), "overview totals base upkeep");
rows[2].Locate.callback(); eq(located, plots[7], "row callback locates its own site");
rows[1].SiteManage.callback(); eq(Controls.OverviewPanel.hidden, true); eq(Controls.Convert.disabled, true, "neutral conversion locked");
Players[0].used[1] = 4; Events.SerialEventUnitInfoDirty.Fire();
yes(string.find(Controls.Impact.text, "SHORTAGE", 1, true), "visible abandonment shortage warning");
Controls.Abandon.callback(); Players[0].used[1] = 5;
Controls.Abandon.callback(); eq(plots[2].improvement, RO_Eras.Target(0), "changed consequences require fresh confirmation");
Controls.Abandon.callback(); eq(plots[2].improvement, -1);
rows[1].SiteManage.callback(); plots[7].pillaged = false; O.Reconcile(); Events.SerialEventUnitInfoDirty.Fire();
yes(string.find(Controls.Impact.text, "LAST_LUXURY", 1, true), "visible last-copy warning");
plots[7].owner = 0; Players[0]:ChangeNumResourceTotal(2, 1); O.Reconcile(); Events.SerialEventUnitInfoDirty.Fire();
eq(Controls.Convert.disabled, false, "annexation unlocks conversion control");
Controls.Convert.callback(); eq(plots[7].improvement, RO_Eras.Target(0), "conversion confirmation is explicit");
yes(string.find(Controls.Impact.text, "CONVERT_PREVIEW", 1, true));
Controls.Convert.callback(); eq(plots[7].improvement, I.IMPROVEMENT_PLANTATION);
eq(Players[0].maintenance, 0); eq(#rows, 0, "converted installation leaves overview");
print("Outposts including UI: " .. count .. " assertions passed");

-- Claimant-era art: real Lua with the native setter's repair/resource/link order.
reset(); p = plots[4]; Players[0].era = I.ERA_FUTURE; Players[1].era = I.ERA_CLASSICAL;
build(1, p); eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_CLASSICAL, "completion uses inactive claimant, not active player's era");
O.Initialize(); p.revealed, p.visible = false, false;
for _, row in ipairs(eraRows) do
    Players[1].era = I[row.EraType]; GameEvents.TeamTechResearched.Fire(1, 10, 1);
    eq(p.improvement, I[row.ImprovementType], "technology event selects " .. row.EraType);
    eq(O.Owner(p), 1); eq(total(1, 1), 6); eq(Players[1].maintenance, 2);
end
eq(p.owner, -1, "art never claims cultural territory");
eq(p.revealed, false, "art does not reveal the claimant's plot");
Players[1].era = 10; O.Reconcile(); eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_FUTURE, "extra future eras retain latest supported art");
local swaps = p.setCalls; O.Reconcile(); O.Reconcile(); eq(p.setCalls, swaps, "unchanged era never invokes native setter");
Players[1].dead = true; Players[1].era = 0; O.Reconcile(); eq(p.setCalls, swaps, "dead claimant cannot change art");
eq(RO_Eras.Target(2), nil, "barbarians have no outpost art stage");

reset(); p = plots[4]; build(0, p); O.Initialize();
guard = unit(300, 0, p, false); guard.damage, guard.moves = 37, 60;
p.upgrade, p.duration, p.route, p.feature, p.progress[25] = 17, 12, 9, I.FEATURE_FOREST, 75;
Players[0].resources[1] = 15; Players[0].resources[2] = 3;
Players[0].policies[1], Players[0].exports[1], Players[0].imports[1], Players[0].used[1] = true, 2, 4, 5;
local available = Players[0]:GetNumResourceAvailable(1);
mutations, oldNotices = Players[0].changes, #Players[0].notices;
p.reenter = true; Players[0].era = I.ERA_MODERN;
GameEvents.PlayerDoTurn.Fire(1); -- fallback works even outside claimant's turn
eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_MODERN);
eq(Players[0].changes, mutations, "neutral visual swap never touches resource ledger");
eq(Players[0]:GetNumResourceAvailable(1), available, "policy/import/export/consumption unchanged");
eq(total(0, 2), 3); eq(O.state.credited[0][1], 6); eq(Players[0].maintenance, 2);
eq(#Players[0].notices, oldNotices, "no cosmetic supply notice");
eq(p.upgrade, 17); eq(p.duration, 12); eq(p.route, 9); eq(p.feature, I.FEATURE_FOREST); eq(p.progress[25], 75);
eq(guard:GetPlot(), p); eq(guard.damage, 37); eq(guard.moves, 60, "garrison untouched");
p.pillaged = true; O.Reconcile(); oldNotices = #Players[0].notices;
Players[0].era = I.ERA_POSTMODERN; Events.SerialEventGameDataDirty.Fire();
eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_POSTMODERN); yes(p.pillaged, "native setter cannot repair ruins during art swap");
eq(total(0, 1), 9); eq(#Players[0].notices, oldNotices, "temporary native repair does not notify or supply");

-- Capture changes the stage immediately, including a less advanced captor.
reset(); p = plots[4]; Players[0].era = I.ERA_FUTURE; Players[1].era = I.ERA_MEDIEVAL;
build(0, p); p.pillaged = true; O.Reconcile(); O.Initialize();
enemy = unit(301, 1, p, false); Teams[0].wars[1], Teams[1].wars[0] = true, true;
GameEvents.UnitSetXY.Fire(1, 301);
eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_MEDIEVAL); eq(O.Owner(p), 1); yes(p.pillaged);
eq(total(0, 1), 0); eq(total(1, 1), 0); eq(Players[0].maintenance, 0); eq(Players[1].maintenance, 2);
p.pillaged = false; O.OnBuilt(0, p.id, 0, -1);
eq(O.Owner(p), 1, "repair of a variant retains claimant"); eq(total(1, 1), 6);
eq(RO_Management.Preview(1, p).loss, 6, "management recognizes captured variant");

-- Territorial ownership supersedes the ledger; native bonuses and city links
-- must survive a swap even when the native credit differs from deposit quantity.
reset(); p = plots[4]; Players[1].era = I.ERA_POSTMODERN; build(0, p); O.Initialize();
p.owner, p.nativeAccounting, p.nativeQuantity, p.linked = 1, true, 24, true;
Players[1].resources[1], Players[1].resources[2] = 31, 5;
p.reenter, Players[1].reenter = true, true;
GameEvents.CityBoughtPlot.Fire(1, 0, p.id, 0);
eq(O.Owner(p), 1); eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_POSTMODERN);
eq(total(0, 1), 0); eq(total(1, 1), 31, "native trait/terrain credit unchanged after annexation swap");
yes(p.linked, "new variant retains active city resource link"); eq(total(1, 2), 5);
eq(Players[0].maintenance, 0); eq(Players[1].maintenance, 2);
p:SetImprovementPillaged(true); eq(total(1, 1), 7); O.Reconcile();
Players[1].era = I.ERA_FUTURE; GameEvents.TeamTechResearched.Fire(1, 10, 1);
yes(p.pillaged); eq(total(1, 1), 7, "owned ruin retains zero native credit"); eq(p.linked, false);
p:SetImprovementPillaged(false); O.OnBuilt(0, p.id, 0, -1);
eq(total(1, 1), 31); yes(p.linked); eq(O.Owner(p), 1);

-- Persisted variants and old canonical sites migrate from the same save keys.
reset(); p = plots[4]; build(0, p); swaps = p.setCalls;
Players[0].era = I.ERA_INDUSTRIAL; loadModules(); O.Initialize(); Events.LoadScreenClose.Fire();
eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_INDUSTRIAL); eq(p.setCalls, swaps + 1);
eq(total(0, 1), 6); eq(Players[0].maintenance, 2); eq(#Players[0].notices, 0);
p.improvement, p.gift = I.IMPROVEMENT_RT_RESOURCE_OUTPOST, true; -- old neutral save
loadModules(); O.Initialize();
eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_INDUSTRIAL); eq(p.gift, false);
eq(total(0, 1), 6, "legacy claim is not credited twice");

-- Old canonical/gifted annexed sites need a one-time tech safety gate. Native
-- removal otherwise subtracts a resource the territorial owner never received.
reset(); p = plots[4]; build(0, p); p.owner = 1; Teams[1].techs[12] = false;
O.Reconcile(); p.improvement, p.gift, p.nativeAccounting = I.IMPROVEMENT_RT_RESOURCE_OUTPOST, true, true;
Players[1].era = I.ERA_MODERN; Players[1].resources[1] = 7;
loadModules(); O.Initialize();
eq(p.improvement, I.IMPROVEMENT_RT_RESOURCE_OUTPOST, "unsafe legacy migration waits for resource technology");
eq(total(1, 1), 7); eq(Players[1].maintenance, 2);
Teams[1].techs[12] = true; Players[1]:ChangeNumResourceTotal(1, 6); p.linked = true;
GameEvents.TeamTechResearched.Fire(1, 12, 1);
eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_MODERN); eq(total(1, 1), 13); yes(p.linked); eq(p.gift, false);
Teams[1].techs[12] = false; Players[1].resources[1] = 7; p.linked = false;
Players[1].era = I.ERA_POSTMODERN; O.Reconcile();
eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_POSTMODERN, "normalized variant has no legacy tech gate"); eq(total(1, 1), 7);

-- Construction keeps one native build ID so an era change cannot erase work.
reset(); p = plots[4]; p.resource = 1; worker = unit(302, 0, p, true);
Orders.Initialize(); O.Initialize(); Orders.Start(worker);
Players[0].era = I.ERA_FUTURE; GameEvents.TeamTechResearched.Fire(0, 10, 1);
eq(p:GetBuildProgress(O.build), 100); eq(p.improvement, -1);
nextTurn(0); nextTurn(0); eq(p.improvement, I.IMPROVEMENT_RO_OUTPOST_FUTURE); eq(total(0, 1), 1);
yes(O.Abandon(0, p)); Players[0].era = 0; O.Reconcile();
eq(p.improvement, -1, "era sync never resurrects an abandoned site"); eq(total(0, 1), 0);
print("Outposts including claimant-era transitions: " .. count .. " assertions passed");
