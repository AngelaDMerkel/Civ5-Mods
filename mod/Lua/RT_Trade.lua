-- Mac-compatible replacement trade. Active caravans are saved route entities;
-- no capturable native proxy unit is spawned for a protected caravan.
RT_Trade = {};
local T, M, R, E = RT_Trade, RT_TradeMap, RT_TradeRules, RT_TradeEconomy;
local I = GameInfoTypes;
local saved = Modding.OpenSaveData();
local KEY = "RealisticTerrain.Trade.v2";
local record = saved:GetValue(KEY);
T.state = record and RT_Serialize.Decode(record) or { agreements = {}, offers = {}, routes = {},
    nextID = 1, guards = {}, roadBuilders = {}, paid = {}, cash = {}, science = {},
    processed = {}, projects = {}, aiLast = {}, history = {} };
local state = T.state;
local maintenance = {};
local function save() saved:SetValue(KEY, RT_Serialize.Encode(state)); end
T.Save = save;
local function pair(a, b) return math.min(a, b) .. ":" .. math.max(a, b); end
local function plot(id) return Map.GetPlotByIndex(id); end
local function city(id) local p = plot(id); return p and p:GetPlotCity(); end
local function notify(owner, message, p)
    local player = Players[owner];
    if player and player:IsHuman() then player:AddNotification(NotificationTypes.NOTIFICATION_GENERIC,
        message, "Trade and logistics", p and p:GetX() or -1, p and p:GetY() or -1); end
end
local function sameSide(a, b)
    local x, y = Players[a], Players[b];
    return x and y and x:IsAlive() and y:IsAlive() and not Teams[x:GetTeam()]:IsAtWar(y:GetTeam());
end
function T.HasAgreement(a, b)
    return a == b or (sameSide(a, b) and state.agreements[pair(a, b)] == true);
end
function T.Willing(a, b)
    return sameSide(a, b) and Teams[Players[a]:GetTeam()]:IsHasMet(Players[b]:GetTeam())
        and not Players[a]:IsDenouncedPlayer(b) and not Players[b]:IsDenouncedPlayer(a);
end
function T.Offer(a, b)
    if a == b or not T.Willing(a, b) then return false, "Trade agreement declined"; end
    local key = pair(a, b);
    if Players[b]:IsHuman() and state.offers[key] ~= b then
        state.offers[key] = a; save(); return true, "Trade agreement offered";
    end
    state.agreements[key], state.offers[key] = true, nil;
    notify(a, "Trade agreement signed with " .. Players[b]:GetCivilizationShortDescription());
    notify(b, "Trade agreement signed with " .. Players[a]:GetCivilizationShortDescription());
    save(); return true, "Trade agreement signed";
end
function T.Revoke(a, b)
    state.agreements[pair(a, b)], state.offers[pair(a, b)] = nil, nil;
    -- Agreements grant commercial passage only; they never alter Open Borders.
    save(); T.ValidateRoutes();
end
function T.IsTradeUnit(unit)
    return unit and not unit:IsDelayedDeath() and (unit:GetUnitType() == I.UNIT_CARAVAN
        or unit:GetUnitType() == I.UNIT_CARGO_SHIP or T.IsRoadIndependent(unit:GetUnitType()));
end
function T.IsRoadIndependent(unitType)
    return I.UNIT_RT_MOTORIZED_CARAVAN ~= nil and unitType == I.UNIT_RT_MOTORIZED_CARAVAN;
end
function T.Capacity(owner)
    return Players[owner]:GetNumInternationalTradeRoutesAvailable();
end
function T.Used(owner)
    local n = 0; for _, route in pairs(state.routes) do if route.owner == owner then n = n + 1; end end; return n;
end
function T.MaintenanceFactor(owner)
    if owner < 0 then return 0; end
    if maintenance[owner] then return maintenance[owner]; end
    local raw = 0;
    for id = 0, Map.GetNumPlots() - 1 do
        local p = plot(id); local payer = p:GetOwner();
        if payer < 0 then payer = state.roadBuilders[id] or -1; end
        if payer == owner and p:GetRouteType() >= 0 and not p:GetPlotCity() then
            raw = raw + GameInfo.Routes[p:GetRouteType()].GoldMaintenance;
        end
        if p:GetOwner() == owner and p:GetImprovementType() >= 0 then
            raw = raw + GameInfo.Improvements[p:GetImprovementType()].GoldMaintenance;
        end
    end
    maintenance[owner] = raw > 0 and math.min(1, Players[owner]:GetImprovementGoldMaintenance() / raw) or 0;
    return maintenance[owner];
end
local function options(from, to, domain, ctx, unitType)
    return { origin = from:GetOwner(), international = from:GetOwner() ~= to:GetOwner(),
        destinationAgreement = T.HasAgreement(from:GetOwner(), to:GetOwner()),
        baseRange = Players[from:GetOwner()]:GetTradeRouteRange(domain, from),
        agreements = ctx.agreements, land = domain == DomainTypes.DOMAIN_LAND,
        roadIndependent = domain == DomainTypes.DOMAIN_LAND and T.IsRoadIndependent(unitType),
        logistics = Teams[ctx.team]:GetTeamTechs():HasTech(I.TECH_RT_CARAVAN_LOGISTICS) };
end
function T.Quote(from, to, domain, kind, existingPath, context, unitType)
    local owner = from:GetOwner(); local ctx = context or M.Context(owner);
    if from == to then return { valid = false, reason = "Choose a different city" }; end
    if domain == DomainTypes.DOMAIN_SEA and (not M.Coastal(from:Plot()) or not M.Coastal(to:Plot())) then
        return { valid = false, reason = "Sea routes require two coastal cities" };
    end
    if not existingPath then
        for _, route in pairs(state.routes) do
            if route.owner == owner and route.from == from:Plot():GetPlotIndex()
                and route.to == to:Plot():GetPlotIndex() and route.kind == kind then
                return { valid = false, reason = "That route is already operating" };
            end
        end
    end
    if owner ~= to:GetOwner() and not T.HasAgreement(owner, to:GetOwner()) then
        return { valid = false, reason = "Trade agreement required" };
    end
    if owner == to:GetOwner() then
        if kind ~= "food" and kind ~= "production" then return { valid = false, reason = "Choose food or production for domestic trade" }; end
        local building = kind == "food" and I.BUILDING_GRANARY or I.BUILDING_WORKSHOP;
        if from:GetNumBuilding(building) == 0 then return { valid = false, reason = kind == "food" and "Origin needs a Granary" or "Origin needs a Workshop" }; end
    elseif kind ~= "international" then return { valid = false, reason = "Domestic cargo cannot be sent internationally" }; end
    local opts = options(from, to, domain, ctx, unitType);
    local path = existingPath or M.Path(from, to, domain, ctx, false, opts.roadIndependent);
    if not path then return { valid = false, reason = "No permitted path: check roads, agreements, range and exploration" }; end
    local facts = M.Facts(path, ctx, domain == DomainTypes.DOMAIN_LAND);
    local quote = R.Inspect(facts, opts);
    if not existingPath and domain == DomainTypes.DOMAIN_LAND
        and ((not quote.valid and quote.reason == "Beyond trade range")
            or (quote.valid and opts.roadIndependent and not quote.hasStation and kind == "international")) then
        -- A supplied stop can improve motorized gold even when extra range is
        -- unnecessary. Prefer it only when its complete route pays better.
        opts.requireStation = quote.valid;
        local relayPath = M.RelayPath(from, to, ctx, opts);
        if relayPath then
            local relayFacts = M.Facts(relayPath, ctx, true);
            local relayQuote = R.Inspect(relayFacts, opts);
            if relayQuote.valid and (not quote.valid or relayQuote.efficiency > quote.efficiency) then
                path, facts, quote = relayPath, relayFacts, relayQuote;
            end
        end
    end
    quote.path, quote.context, quote.facts = path, ctx, facts;
    if not quote.valid then return quote; end
    quote.efficientDistance = Map.PlotDistance(from:GetX(), from:GetY(), to:GetX(), to:GetY());
    quote.assetIDs, quote.assets = {}, {};
    if domain == DomainTypes.DOMAIN_LAND then quote.assetIDs, quote.assets = M.Assets(path, ctx, quote.usedStations); end
    quote.nativeGold100, quote.science100 = {}, {};
    if kind == "international" then
        for _, member in ipairs({owner, to:GetOwner()}) do
            local p, origin = Players[member], member == owner;
            quote.nativeGold100[member] = math.max(0, p:GetInternationalTradeRouteTotal(from, to, domain, origin));
            quote.science100[member] = math.max(0, p:GetInternationalTradeRouteScience(from, to, domain, origin));
        end
    end
    return quote;
end
function T.Settlement(extra)
    local routes, assets, contexts = {}, {}, {};
    for _, route in pairs(state.routes) do
        local from, to = city(route.from), city(route.to);
        if from and to and route.kind == "international" then
            contexts[route.owner] = contexts[route.owner] or M.Context(route.owner);
            local quote = T.Quote(from, to, route.domain, route.kind, route.path, contexts[route.owner], route.unitType);
            if quote.valid then
                routes[#routes + 1] = { id = tostring(route.id), active = true, authorized = true,
                    efficiency = quote.efficiency, nativeGold100 = quote.nativeGold100,
                    efficientDistance = quote.efficientDistance, assets = quote.assetIDs };
                for id, asset in pairs(quote.assets) do assets[id] = asset; end
            end
        end
    end
    if extra and extra.valid and next(extra.nativeGold100) then
        routes[#routes + 1] = { id = "preview", active = true, authorized = true,
            efficiency = extra.efficiency, nativeGold100 = extra.nativeGold100,
            efficientDistance = extra.efficientDistance, assets = extra.assetIDs };
        for id, asset in pairs(extra.assets) do assets[id] = asset; end
    end
    return E.Settle(routes, assets);
end
function T.Launch(unit, targetID, kind)
    if not T.IsTradeUnit(unit) then return false, "Select an idle Caravan, Motorized Caravan or Cargo Ship"; end
    local owner = unit:GetOwner(); local from, to = unit:GetPlot():GetPlotCity(), city(targetID);
    if not Players[owner]:IsTurnActive() then return false, "Wait for the owner's turn"; end
    if not from or from:GetOwner() ~= owner or not to or unit:GetMoves() <= 0 then return false, "Trade unit must be ready in one of your cities"; end
    if T.Used(owner) >= T.Capacity(owner) then return false, "All trade slots are occupied"; end
    for _, r in pairs(state.routes) do
        if r.owner == owner and r.from == from:Plot():GetPlotIndex() and r.to == targetID and r.kind == kind then
            return false, "That route is already operating";
        end
    end
    local quote = T.Quote(from, to, unit:GetDomainType(), kind, nil, nil, unit:GetUnitType());
    if not quote.valid then return false, quote.reason; end
    local id = state.nextID; state.nextID = id + 1;
    local speed = GameInfo.GameSpeeds[Game.GetGameSpeedType()];
    state.routes[id] = { id = id, owner = owner, recipient = to:GetOwner(), from = from:Plot():GetPlotIndex(), to = targetID,
        domain = unit:GetDomainType(), kind = kind, unitType = unit:GetUnitType(), path = quote.path,
        position = 1, direction = 1, started = Game.GetGameTurn(), lastMove = Game.GetGameTurn(),
        minimumTurns = speed.DealDuration, age = 0 };
    -- The invested trade unit is held by the route; it returns when the route
    -- finishes or is recalled. Destruction returns no unit.
    unit:Kill(false, -1); save();
    return true, "Route established";
end
function T.EndRoute(id, reason, destroyed)
    local route = state.routes[id]; if not route then return; end
    state.routes[id] = nil;
    if not destroyed then
        local home = city(route.from);
        if not home or home:GetOwner() ~= route.owner then home = Players[route.owner]:GetCapitalCity(); end
        if home then Players[route.owner]:InitUnit(route.unitType, home:GetX(), home:GetY()); end
    end
    state.history[#state.history + 1] = { owner = route.owner, turn = Game.GetGameTurn(), message = reason };
    while #state.history > 30 do table.remove(state.history, 1); end
    notify(route.owner, reason, plot(route.path[route.position])); save();
end
local function routeAuthorized(route)
    local from, to = city(route.from), city(route.to);
    if not from or not to or from:GetOwner() ~= route.owner or to:GetOwner() ~= route.recipient then return false; end
    if not T.HasAgreement(route.owner, route.recipient) then return false; end
    for _, id in ipairs(route.path) do
        local owner = plot(id):GetOwner();
        if owner >= 0 and not T.HasAgreement(route.owner, owner) then return false; end
    end
    return true;
end
function T.ValidateRoutes()
    for key in pairs(state.agreements) do
        local a, b = string.match(key, "^(%d+):(%d+)$");
        if a and not sameSide(tonumber(a), tonumber(b)) then state.agreements[key], state.offers[key] = nil, nil; end
    end
    local ended = {};
    for id, route in pairs(state.routes) do if not routeAuthorized(route) then ended[#ended + 1] = id; end end
    table.sort(ended); for _, id in ipairs(ended) do T.EndRoute(id, "Route recalled: city ownership or trade agreement changed", false); end
end
function T.Raid(route)
    local p = plot(route.path[route.position]);
    local team = Players[route.owner]:GetTeam();
    local raider;
    for i = 0, p:GetNumUnits() - 1 do
        local enemy = p:GetUnit(i);
        if enemy and not enemy:IsDelayedDeath() and enemy:IsCombatUnit() and not enemy:IsEmbarked()
            and Teams[team]:IsAtWar(enemy:GetTeam()) then
            raider = enemy; break;
        end
    end
    if not raider then return false; end
    local ctx = M.Context(route.owner);
    if route.domain == DomainTypes.DOMAIN_LAND and M.Patrol(ctx)[p:GetPlotIndex()] then return false; end
    Players[raider:GetOwner()]:ChangeGold(100);
    T.EndRoute(route.id, "Trade unit lost to a raid", true); return true;
end
function T.Advance(route)
    if route.lastMove == Game.GetGameTurn() then return; end
    route.lastMove = Game.GetGameTurn(); route.age = route.age + 1;
    if T.Raid(route) then return; end
    local from, to = city(route.from), city(route.to);
    if not from or not to then return; end
    local quote = T.Quote(from, to, route.domain, route.kind, route.path, nil, route.unitType);
    if not quote.valid and quote.reason == "Beyond trade range" then
        T.EndRoute(route.id, "Route recalled: loss of road or Caravansary range", false); return;
    end
    local moves = route.domain == DomainTypes.DOMAIN_LAND and 2 or 3;
    for _ = 1, moves do
        local nextIndex = route.position + route.direction;
        if nextIndex > #route.path then route.direction = -1; nextIndex = route.position - 1; end
        if nextIndex < 1 then
            if route.age >= route.minimumTurns then T.EndRoute(route.id, "Trade route completed; unit returned", false); return; end
            route.direction = 1; nextIndex = 2;
        end
        local p = plot(route.path[nextIndex]);
        if route.domain == DomainTypes.DOMAIN_LAND and p:GetOwner() < 0 and not M.Road(p)
            and not T.IsRoadIndependent(route.unitType)
            and not Teams[Players[route.owner]:GetTeam()]:GetTeamTechs():HasTech(I.TECH_RT_CARAVAN_LOGISTICS) then
            T.EndRoute(route.id, "Caravan lost entering roadless unclaimed territory before Caravan Logistics", true); return;
        end
        route.position = nextIndex;
        if T.Raid(route) then return; end
    end
end
function T.UpdateGuards(owner)
    local player = Players[owner];
    for id, old in pairs(state.guards) do
        if old.owner == owner then
            local u = player:GetUnitByID(old.unit);
            if not u or u:IsDelayedDeath() or u:GetPlot() ~= plot(id) or u:GetGameTurnCreated() ~= old.birth then state.guards[id] = nil; end
        end
    end
    for unit in player:Units() do
        if not unit:IsDelayedDeath() and unit:GetPlot() and unit:IsCombatUnit() and not unit:IsEmbarked() and unit:GetDomainType() == DomainTypes.DOMAIN_LAND then
            local p = unit:GetPlot(); local stationOwner = RT_Supply.Owner(p);
            if p:GetImprovementType() == I.IMPROVEMENT_RT_RELIEF_STATION and stationOwner >= 0 and T.HasAgreement(owner, stationOwner) then
                local id = p:GetPlotIndex(); local old = state.guards[id];
                if not old or old.unit ~= unit:GetID() or old.owner ~= owner or old.birth ~= unit:GetGameTurnCreated() then
                    state.guards[id] = { owner = owner, unit = unit:GetID(), birth = unit:GetGameTurnCreated(), since = Game.GetGameTurn() };
                end
            end
        end
    end
end
function T.Pay(owner)
    if state.paid[owner] == Game.GetGameTurn() then return; end
    state.paid[owner] = Game.GetGameTurn();
    local ledger = T.Settlement(); local account = ledger.players[owner];
    local cash = (state.cash[owner] or 0) + (account and account.payment100 or 0);
    local whole = math.floor(cash / 100); state.cash[owner] = cash - whole * 100;
    if whole > 0 then Players[owner]:ChangeGold(whole); end
    local science = state.science[owner] or 0;
    for _, route in pairs(state.routes) do
        local from, to = city(route.from), city(route.to);
        if from and to then
            local quote = T.Quote(from, to, route.domain, route.kind, route.path, nil, route.unitType);
            if quote.valid then
                science = science + (quote.science100[owner] or 0);
                if route.kind ~= "international" and route.owner == owner then
                    local yield = 3 + Players[owner]:GetCurrentEra();
                    if route.domain == DomainTypes.DOMAIN_SEA then yield = yield * 2; end
                    yield = math.max(1, math.floor(yield * quote.cargoEfficiency / 100));
                    if route.kind == "food" then to:ChangeFood(yield); else to:ChangeProduction(yield); end
                end
            end
        end
    end
    local research = Players[owner]:GetCurrentResearch();
    if research >= 0 and science >= 100 then
        local beakers = math.floor(science / 100); science = science - beakers * 100;
        Teams[Players[owner]:GetTeam()]:GetTeamTechs():ChangeResearchProgress(research, beakers, owner);
    end
    state.science[owner] = science; save();
end
function T.OnTurn(owner)
    local p = Players[owner]; if not p or not p:IsAlive() or p:IsBarbarian() then return; end
    maintenance = {}; T.ValidateRoutes(); T.UpdateGuards(owner);
    if state.processed[owner] ~= Game.GetGameTurn() then
        state.processed[owner] = Game.GetGameTurn();
        local ids = {}; for id, route in pairs(state.routes) do if route.owner == owner then ids[#ids + 1] = id; end end; table.sort(ids);
        for _, id in ipairs(ids) do if state.routes[id] then T.Advance(state.routes[id]); end end
        if not p:IsHuman() and RT_TradeAI then RT_TradeAI.OnTurn(owner); end
    end
    T.Pay(owner); save(); if T.OnChanged then T.OnChanged(); end
end
function T.OnUnitMoved(owner, unitID)
    local unit = Players[owner] and Players[owner]:GetUnitByID(unitID);
    if unit and (unit:IsDelayedDeath() or not unit:GetPlot()) then unit = nil; end
    local changed = false;
    for id, guard in pairs(state.guards) do
        if guard.owner == owner and guard.unit == unitID then
            local u = Players[owner]:GetUnitByID(unitID);
            if not u or u:GetPlot() ~= plot(id) then state.guards[id] = nil; changed = true; end
        end
    end
    if unit and unit:IsCombatUnit() and not Players[owner]:IsBarbarian() then T.UpdateGuards(owner); end
    local ids = {}; for id in pairs(state.routes) do ids[#ids + 1] = id; end; table.sort(ids);
    for _, id in ipairs(ids) do
        local route = state.routes[id];
        if route and (changed or (unit and unit:GetPlot():GetPlotIndex() == route.path[route.position])) then T.Raid(route); end
    end
    save();
end
function T.OnBuild(owner, x, y)
    local p = Map.GetPlot(x, y); local id = p:GetPlotIndex();
    if p:GetRouteType() < 0 then state.roadBuilders[id] = nil;
    elseif state.roadBuilders[id] == nil then state.roadBuilders[id] = owner; end
    maintenance = {}; save();
end
function T.Initialize()
    RT_Supply.CanTransit = T.HasAgreement;
    GameEvents.PlayerDoTurn.Add(T.OnTurn);
    GameEvents.UnitSetXY.Add(T.OnUnitMoved);
    GameEvents.BuildFinished.Add(T.OnBuild);
    GameEvents.CityCaptureComplete.Add(T.ValidateRoutes);
    Events.WarStateChanged.Add(function() T.ValidateRoutes(); save(); end);
    print("Realistic Terrain: replacement trade initialized (native trade disabled).");
end
