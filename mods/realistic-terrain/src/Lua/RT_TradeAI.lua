-- Deliberate logistics for AI players. All construction uses paid production or
-- real worker missions; no free roads, stations, trade units or garrisons.
RT_TradeAI = {};
local A, T, M, I = RT_TradeAI, RT_Trade, RT_TradeMap, GameInfoTypes;
local function distance(a, b) return Map.PlotDistance(a:GetX(), a:GetY(), b:GetX(), b:GetY()); end
local function queue(player, order, item)
    for c in player:Cities() do
        local valid = order == OrderTypes.ORDER_TRAIN and c:CanTrain(item)
            or order == OrderTypes.ORDER_CONSTRUCT and c:CanConstruct(item);
        if valid then c:PushOrder(order, item, -1, false, false, true); return true; end
    end
    return false;
end
local function idle(unit)
    return unit:GetMoves() > 0 and not unit:IsDelayedDeath() and not unit:IsEmbarked()
        and not (RT_OutpostBridge and RT_OutpostBridge.Reserved(unit))
        and not (RT_ConstructionOrders and RT_ConstructionOrders.IsOrdered(unit));
end
function A.LandUnitForRoute(from, to)
    -- Keep the cheaper Caravan useful. Pay for a motorized convoy only when
    -- it opens this route or improves its commercial infrastructure efficiency.
    if Teams[Players[from:GetOwner()]:GetTeam()]:GetTeamTechs():HasTech(I.TECH_COMBUSTION) then
        local ordinary = T.Quote(from, to, DomainTypes.DOMAIN_LAND, "international", nil, nil, I.UNIT_CARAVAN);
        local motorized = T.Quote(from, to, DomainTypes.DOMAIN_LAND, "international", nil, nil, I.UNIT_RT_MOTORIZED_CARAVAN);
        if motorized.valid and (not ordinary.valid or motorized.efficiency > ordinary.efficiency) then
            return I.UNIT_RT_MOTORIZED_CARAVAN;
        end
    end
    return I.UNIT_CARAVAN;
end
local function raidTraffic(owner, troops)
    local team = Players[owner]:GetTeam();
    local targets = {};
    for _, route in pairs(T.state.routes) do
        local target = Map.GetPlotByIndex(route.path[route.position]);
        if route.domain == DomainTypes.DOMAIN_LAND and Teams[team]:IsAtWar(Players[route.owner]:GetTeam())
            and target:IsVisible(team, false) then
            local patrol = M.Patrol(M.Context(route.owner))[target:GetPlotIndex()];
            if patrol then
                target = nil;
                for stationID, guard in pairs(patrol) do
                    local station = Map.GetPlotByIndex(stationID);
                    if Teams[team]:IsAtWar(Players[guard.owner]:GetTeam()) and station:IsVisible(team, false) then target = station; break; end
                end
            end
            if target then targets[#targets + 1] = target; end
        end
    end
    for _, troop in ipairs(troops) do
        if idle(troop) and not troop:GetPlot():GetPlotCity()
            and troop:GetPlot():GetImprovementType() ~= I.IMPROVEMENT_RT_RELIEF_STATION then
            local best, dist;
            for _, target in ipairs(targets) do
                local d = distance(troop:GetPlot(), target);
                if d <= 8 and (not dist or d < dist) then best, dist = target, d; end
            end
            if best then troop:PushMission(MissionTypes.MISSION_MOVE_TO, best:GetX(), best:GetY()); end
        end
    end
end
function A.OnTurn(owner)
    -- Ensure companion reservations exist regardless of UI-context load order.
    if LuaEvents then LuaEvents.RO_RunAI(owner); end
    local p, turn = Players[owner], Game.GetGameTurn();
    local state = T.state;
    -- Peace and absence of denunciations are required for new AI agreements.
    for other = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
        local q = Players[other];
        if q and other ~= owner and q:IsAlive() and not q:IsBarbarian() then
            if T.Willing(owner, other) and not T.HasAgreement(owner, other) then T.Offer(owner, other); end
        end
    end
    local workers, traders, guards = {}, {}, {};
    for u in p:Units() do
        if RT_Construction.IsWorker(u) then
            if not (RT_OutpostBridge and RT_OutpostBridge.Reserved(u)) then workers[#workers + 1] = u; end
        elseif T.IsTradeUnit(u) then traders[#traders + 1] = u;
        elseif u:IsCombatUnit() and u:GetDomainType() == DomainTypes.DOMAIN_LAND
            and not (RT_OutpostBridge and RT_OutpostBridge.Reserved(u)) then guards[#guards + 1] = u; end
    end
    -- Launch existing units on the best currently permitted commercial route.
    for _, u in ipairs(traders) do
        local from = u:GetPlot():GetPlotCity();
        if idle(u) and from and from:GetOwner() == owner and T.Used(owner) < T.Capacity(owner) then
            local best, bestScore;
            for other = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
                local q = Players[other];
                if other ~= owner and q and q:IsAlive() and T.HasAgreement(owner, other) then
                    for to in q:Cities() do
                        if to:Plot():IsRevealed(p:GetTeam(), false) then
                            local quote = T.Quote(from, to, u:GetDomainType(), "international", nil, nil, u:GetUnitType());
                            if quote.valid then
                                local settlement = T.Settlement(quote);
                                local row = settlement.routes.preview;
                                local score = row and (row.payments100[owner] or 0) or 0;
                                if not bestScore or score > bestScore then best, bestScore = to, score; end
                            end
                        end
                    end
                end
            end
            if best then T.Launch(u, best:Plot():GetPlotIndex(), "international"); end
        elseif idle(u) and not from then
            local capital = p:GetCapitalCity();
            if capital then u:PushMission(MissionTypes.MISSION_MOVE_TO, capital:GetX(), capital:GetY()); end
        end
    end
    -- Find one achievable cooperative corridor. Roads are planned at their
    -- eventual weighted distance, so a 30-tile road can be built before launch.
    local path, bestLength, seaOpportunity;
    local landType = I.UNIT_CARAVAN;
    local ctx = M.Context(owner);
    for from in p:Cities() do
        for other = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
            local q = Players[other];
            if other ~= owner and q and q:IsAlive() and T.HasAgreement(owner, other) then
                for to in q:Cities() do
                    if to:Plot():IsRevealed(p:GetTeam(), false) and distance(from, to) <= 40 then
                        local proposed = M.Path(from, to, DomainTypes.DOMAIN_LAND, ctx, true);
                        if proposed and (not bestLength or #proposed < bestLength) then
                            path, bestLength = proposed, #proposed;
                            landType = A.LandUnitForRoute(from, to);
                        end
                        if not seaOpportunity then seaOpportunity = T.Quote(from, to, DomainTypes.DOMAIN_SEA, "international").valid; end
                    end
                end
            end
        end
    end
    state.projects[owner] = path or {};
    local tradeType = not path and seaOpportunity and I.UNIT_CARGO_SHIP or landType;
    local tradeClass = tradeType == I.UNIT_CARGO_SHIP and I.UNITCLASS_CARGO_SHIP
        or (landType == I.UNIT_RT_MOTORIZED_CARAVAN and I.UNITCLASS_RT_MOTORIZED_CARAVAN or I.UNITCLASS_CARAVAN);
    local waiting = 0;
    for _, u in ipairs(traders) do
        if T.IsTradeUnit(u) and ((tradeType == I.UNIT_CARGO_SHIP) == (u:GetDomainType() == DomainTypes.DOMAIN_SEA)) then
            waiting = waiting + 1;
        end
    end
    local making = p:GetUnitClassMaking(tradeClass);
    if tradeType ~= I.UNIT_CARGO_SHIP then
        making = p:GetUnitClassMaking(I.UNITCLASS_CARAVAN) + p:GetUnitClassMaking(I.UNITCLASS_RT_MOTORIZED_CARAVAN);
    end
    -- Periodic production commitments avoid continuously replacing AI queues.
    if turn - (state.aiLast[owner] or -100) >= 8 then
        if path and p:CountNumBuildings(I.BUILDING_CARAVANSARY) == 0
            and p:GetBuildingClassMaking(I.BUILDINGCLASS_CARAVANSARY) == 0 then
            queue(p, OrderTypes.ORDER_CONSTRUCT, I.BUILDING_CARAVANSARY);
        elseif path and #workers == 0 then queue(p, OrderTypes.ORDER_TRAIN, I.UNIT_WORKER);
        elseif (path or seaOpportunity) and T.Used(owner) + waiting + making < T.Capacity(owner) then
            queue(p, OrderTypes.ORDER_TRAIN, tradeType); end
        state.aiLast[owner] = turn;
    end
    raidTraffic(owner, guards);
    if not path then return; end
    local jobs, stations = {}, {};
    for index, id in ipairs(path) do
        local q = Map.GetPlotByIndex(id);
        if q:GetOwner() == owner or q:GetOwner() < 0 then
            if not q:GetPlotCity() then
                if q:IsRoutePillaged() or q:IsImprovementPillaged() then jobs[#jobs + 1] = { plot = q, build = I.BUILD_REPAIR };
                elseif not M.Road(q) then jobs[#jobs + 1] = { plot = q, build = I.BUILD_ROAD };
                elseif q:GetImprovementType() == I.IMPROVEMENT_RT_RELIEF_STATION then stations[#stations + 1] = q;
                elseif Teams[p:GetTeam()]:GetTeamTechs():HasTech(I.TECH_ENGINEERING)
                    and (index % 8 == 0 or (M.Hazard(q) and index % 3 == 0)) and q:GetImprovementType() < 0
                    and q:CanBuild(I.BUILD_RT_RELIEF_STATION, owner, false, true) then
                    jobs[#jobs + 1] = { plot = q, station = true };
                end
            end
        end
    end
    local assigned = {};
    for _, u in ipairs(workers) do
        if idle(u) and not u:IsAutomated() and u:GetBuildType() == -1 then
            local best, dist;
            for index, job in ipairs(jobs) do
                if not assigned[index] and (not job.station or p:CountNumBuildings(I.BUILDING_CARAVANSARY) > 0) then
                    local d = distance(u:GetPlot(), job.plot);
                    if not dist or d < dist then best, dist = index, d; end
                end
            end
            if best then
                assigned[best] = true; local job = jobs[best];
                if u:GetPlot() == job.plot then
                    if job.station then RT_Construction.Work(u, true);
                    -- CvLuaUnit reads these flags with luaL_optint.
                    elseif u:CanBuild(job.plot, job.build, 0, 1) then u:PushMission(MissionTypes.MISSION_BUILD, job.build); end
                else u:PushMission(MissionTypes.MISSION_MOVE_TO, job.plot:GetX(), job.plot:GetY()); end
            end
        end
    end
    -- Only spare field troops are assigned, never city garrisons or embarked units.
    local used = {};
    for _, station in ipairs(stations) do
        local occupied = false;
        for i = 0, station:GetNumUnits() - 1 do
            local u = station:GetUnit(i); if u:GetOwner() == owner and u:IsCombatUnit() then occupied = true; u:FinishMoves(); end
        end
        if not occupied then
            local best, dist;
            for _, u in ipairs(guards) do
                if not used[u:GetID()] and idle(u) and not u:GetPlot():GetPlotCity()
                    and u:GetPlot():GetImprovementType() ~= I.IMPROVEMENT_RT_RELIEF_STATION then
                    local d = distance(u:GetPlot(), station);
                    if d <= 10 and (not dist or d < dist) then best, dist = u, d; end
                end
            end
            if best then used[best:GetID()] = true; best:PushMission(MissionTypes.MISSION_MOVE_TO, station:GetX(), station:GetY()); end
        end
    end
end
