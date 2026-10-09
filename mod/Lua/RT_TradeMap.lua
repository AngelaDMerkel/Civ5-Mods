-- Map adapter for the replacement trade engine. No native route-path guesses.
RT_TradeMap = {};
local M = RT_TradeMap;
local I = GameInfoTypes;
local function pid(plot) return plot:GetPlotIndex(); end
function M.Neighbors(id)
    local p, result = Map.GetPlotByIndex(id), {};
    for direction = 0, 5 do
        local q = Map.PlotDirection(p:GetX(), p:GetY(), direction);
        if q then result[#result + 1] = pid(q); end
    end
    return result;
end
function M.Road(p)
    return p:GetPlotCity() ~= nil or ((p:GetRouteType() == I.ROUTE_ROAD or p:GetRouteType() == I.ROUTE_RAILROAD)
        and not p:IsRoutePillaged());
end
function M.Coastal(p)
    for _, id in ipairs(M.Neighbors(pid(p))) do if Map.GetPlotByIndex(id):IsWater() then return true; end end
    return false;
end
function M.Context(owner)
    local context = { owner = owner, team = Players[owner]:GetTeam(), agreements = {}, stations = {}, patrol = {} };
    for other = 0, GameDefines.MAX_CIV_PLAYERS - 1 do context.agreements[other] = RT_Trade.HasAgreement(owner, other); end
    return context;
end
function M.Station(p, ctx)
    local id = pid(p);
    if ctx.stations[id] ~= nil then return ctx.stations[id]; end
    local owner = RT_Supply.Owner(p);
    local ok = p:GetImprovementType() == I.IMPROVEMENT_RT_RELIEF_STATION
        and not p:IsImprovementPillaged() and owner >= 0
        and RT_TradeRules.Access(owner, ctx.owner, ctx.agreements) and RT_Supply.Connected(p, owner);
    ctx.stations[id] = ok;
    return ok;
end
function M.Hazard(p)
    if p:GetFeatureType() == I.FEATURE_JUNGLE then return "jungle"; end
    if p:GetTerrainType() == I.TERRAIN_DESERT then return "heat"; end
    if p:GetTerrainType() == I.TERRAIN_TUNDRA or p:GetTerrainType() == I.TERRAIN_SNOW then return "cold"; end
end
function M.Relief(p, ctx)
    if p:GetPlotCity() then return true; end
    if p:GetOwner() == ctx.owner then return true; end
    local hazard = M.Hazard(p);
    if not hazard then return true; end
    if hazard == "heat" and (p:IsRiver() or p:GetFeatureType() == I.FEATURE_FLOOD_PLAINS) then return true; end
    local near = M.Neighbors(pid(p)); near[#near + 1] = pid(p);
    for _, id in ipairs(near) do
        local q = Map.GetPlotByIndex(id);
        if M.Station(q, ctx) then return true, id; end
        if hazard == "heat" and (q:IsLake() or q:GetFeatureType() == I.FEATURE_OASIS)
            and RT_TradeRules.Access(q:GetOwner(), ctx.owner, ctx.agreements) then return true; end
    end
    return false;
end
function M.Facts(path, ctx, land)
    local result = {};
    for index, id in ipairs(path) do
        local p = Map.GetPlotByIndex(id);
        local road = M.Road(p);
        local relief, reliefStation = M.Relief(p, ctx);
        result[#result + 1] = { id = id, owner = p:GetOwner(), road = road, city = p:GetPlotCity() ~= nil,
            hazard = land and M.Hazard(p), relief = land and relief, reliefStation = land and reliefStation,
            station = land and M.Station(p, ctx),
            stepCost = land and index > 1 and road and M.Road(Map.GetPlotByIndex(path[index - 1])) and 50 or 100 };
    end
    return result;
end
function M.Leg(start, goal, domain, ctx, planning, maxCost, blocked, roadIndependent)
    local land = domain == DomainTypes.DOMAIN_LAND;
    local techs = Teams[ctx.team]:GetTeamTechs();
    local logistics = techs:HasTech(I.TECH_RT_CARAVAN_LOGISTICS);
    return RT_TradeRules.Path(start, goal, M.Neighbors, function(id)
        local p = Map.GetPlotByIndex(id);
        if blocked and blocked[id] then return false; end
        if not p:IsRevealed(ctx.team, false) or p:IsMountain() or p:GetFeatureType() == I.FEATURE_ICE then return false; end
        if not RT_TradeRules.Access(p:GetOwner(), ctx.owner, ctx.agreements) then return false; end
        if land then
            return not p:IsWater() and (planning or logistics or roadIndependent or p:GetOwner() >= 0 or M.Road(p));
        end
        if not p:IsWater() then return id == start or id == goal; end
        return p:GetTerrainType() ~= I.TERRAIN_OCEAN or techs:HasTech(I.TECH_ASTRONOMY);
    end, function(a, b)
        return land and (planning or (M.Road(Map.GetPlotByIndex(a)) and M.Road(Map.GetPlotByIndex(b)))) and 50 or 100;
    end, maxCost);
end
function M.Path(from, to, domain, ctx, planning, roadIndependent)
    local maxRange = Players[ctx.owner]:GetTradeRouteRange(domain, from) + (domain == DomainTypes.DOMAIN_LAND and 10 or 0);
    return M.Leg(pid(from:Plot()), pid(to:Plot()), domain, ctx, planning, maxRange * 100 + 99, nil, roadIndependent);
end
function M.RelayPath(from, to, ctx, options)
    -- The shortest direct path can miss a useful relay. Search paths through up
    -- to two reachable stations, without allowing loops to manufacture range.
    local stations, goal = {}, pid(to:Plot());
    for id = 0, Map.GetNumPlots() - 1 do
        local p = Map.GetPlotByIndex(id);
        if p:GetImprovementType() == I.IMPROVEMENT_RT_RELIEF_STATION and p:IsRevealed(ctx.team, false)
            and M.Station(p, ctx) then stations[#stations + 1] = id; end
    end
    table.sort(stations, function(a, b)
        local x, y, z = Map.GetPlotByIndex(a), Map.GetPlotByIndex(b), Map.GetPlotByIndex(goal);
        local da = Map.PlotDistance(x:GetX(), x:GetY(), z:GetX(), z:GetY());
        local db = Map.PlotDistance(y:GetX(), y:GetY(), z:GetX(), z:GetY());
        return da < db or (da == db and a < b);
    end);
    local function join(prefix, leg)
        local result = {}; for _, id in ipairs(prefix) do result[#result + 1] = id; end
        for i = 2, #leg do result[#result + 1] = leg[i]; end; return result;
    end
    local function visit(prefix)
        local status = RT_TradeRules.Inspect(M.Facts(prefix, ctx, true), options);
        if not status.valid then return nil; end
        local blocked = {}; for i = 1, #prefix - 1 do blocked[prefix[i]] = true; end
        local start, budget = prefix[#prefix], status.range - status.cost + 99;
        local final = M.Leg(start, goal, DomainTypes.DOMAIN_LAND, ctx, false, budget, blocked, options.roadIndependent);
        if final then
            local path = join(prefix, final);
            local inspected = RT_TradeRules.Inspect(M.Facts(path, ctx, true), options);
            if inspected.valid and (not options.requireStation or inspected.hasStation) then return path; end
        end
        if status.relays >= 2 then return nil; end
        for _, station in ipairs(stations) do
            if station ~= start and not blocked[station] then
                local leg = M.Leg(start, station, DomainTypes.DOMAIN_LAND, ctx, false, budget, blocked, options.roadIndependent);
                if leg then
                    local extended = join(prefix, leg);
                    local nextStatus = RT_TradeRules.Inspect(M.Facts(extended, ctx, true), options);
                    if nextStatus.valid and nextStatus.relays > status.relays then
                        local result = visit(extended); if result then return result; end
                    end
                end
            end
        end
    end
    return visit({pid(from:Plot())});
end
function M.Patrol(ctx)
    if ctx.patrolReady then return ctx.patrol; end
    ctx.patrolReady = true;
    local trade = RT_Trade;
    for stationID, guard in pairs(trade.state.guards) do
        local player = Players[guard.owner];
        local unit = player and player:GetUnitByID(guard.unit);
        local station = Map.GetPlotByIndex(stationID);
        if unit and not unit:IsDelayedDeath() and unit:IsCombatUnit() and not unit:IsEmbarked()
            and unit:GetGameTurnCreated() == guard.birth and unit:GetPlot() == station
            and guard.since < Game.GetGameTurn() and M.Station(station, ctx)
            and RT_TradeRules.Access(guard.owner, ctx.owner, ctx.agreements) then
            local queue, head, seen = { stationID }, 1, { [stationID] = true };
            while head <= #queue do
                local id = queue[head]; head = head + 1;
                ctx.patrol[id] = ctx.patrol[id] or {}; ctx.patrol[id][stationID] = guard;
                local p = Map.GetPlotByIndex(id);
                -- A patrol ends at the next station/city on every road branch.
                if id == stationID or (not p:GetPlotCity() and p:GetImprovementType() ~= I.IMPROVEMENT_RT_RELIEF_STATION) then
                    for _, nextID in ipairs(M.Neighbors(id)) do
                        local q = Map.GetPlotByIndex(nextID);
                        if not seen[nextID] and not q:IsWater() and M.Road(q)
                            and RT_TradeRules.Access(q:GetOwner(), ctx.owner, ctx.agreements) then
                            seen[nextID] = true; queue[#queue + 1] = nextID;
                        end
                    end
                end
            end
        end
    end
    return ctx.patrol;
end

function M.Assets(path, ctx, usedStations)
    local ids, assets = {}, {};
    local function add(id, owner, kind, cost, capital)
        if owner < 0 or assets[id] then return; end
        assets[id] = { owner = owner, kind = kind, upkeep100 = cost, standardCapital100 = capital };
        ids[#ids + 1] = id;
    end
    M.Patrol(ctx);
    for _, tile in ipairs(path) do
        local p = Map.GetPlotByIndex(tile);
        local owner = p:GetOwner();
        if owner < 0 then owner = RT_Trade.state.roadBuilders[tile] or -1; end
        if M.Road(p) and not p:GetPlotCity() then
            local rail = p:GetRouteType() == I.ROUTE_RAILROAD;
            local raw = GameInfo.Routes[p:GetRouteType()].GoldMaintenance;
            add("road:" .. tile, owner, rail and "railroad" or "road",
                math.floor(raw * 100 * RT_Trade.MaintenanceFactor(owner)), rail and 1800 or 1200);
        end
        for stationID, guard in pairs(ctx.patrol[tile] or {}) do
            local player = Players[guard.owner];
            -- Civ V exposes empire unit upkeep, not an exact per-unit bill.
            local perUnit = math.floor(player:CalculateUnitCost() * 100 / math.max(1, player:GetNumUnits()));
            add("guard:" .. guard.owner .. ":" .. guard.unit, guard.owner, "garrison", perUnit, 0);
            add("station:" .. stationID, RT_Supply.Owner(Map.GetPlotByIndex(stationID)), "caravansary", 0, 4000);
        end
    end
    for id in pairs(usedStations or {}) do
        add("station:" .. id, RT_Supply.Owner(Map.GetPlotByIndex(id)), "caravansary", 0, 4000);
    end
    table.sort(ids); return ids, assets;
end
