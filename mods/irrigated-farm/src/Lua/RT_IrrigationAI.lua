-- One spare worker per turn extends or repairs a nearby domestic network.
-- Outpost reservations and existing native/custom orders take precedence.
RT_IrrigationAI = {};
local A, F, I = RT_IrrigationAI, RT_Irrigation, GameInfoTypes;
local saved = Modding.OpenSaveData();
local function distance(a, b) return Map.PlotDistance(a:GetX(), a:GetY(), b:GetX(), b:GetY()); end

local function safe(plot, owner)
    local team = Players[owner]:GetTeam();
    local nearby = { plot };
    for d = 0, 5 do
        local n = Map.PlotDirection(plot:GetX(), plot:GetY(), d);
        if n then nearby[#nearby + 1] = n; end
    end
    for _, p in ipairs(nearby) do
        if p:IsVisible(team, false) then
            for j = 0, p:GetNumUnits() - 1 do
                local u = p:GetUnit(j);
                if u:IsCombatUnit() and Teams[team]:IsAtWar(u:GetTeam()) then return false; end
            end
        end
    end
    return true;
end

function A.Path(from, target, owner)
    local queue, head, parents = { from }, 1, { [from:GetPlotIndex()] = false };
    local team = Players[owner]:GetTeam();
    while head <= #queue and head <= 256 do
        local p = queue[head]; head = head + 1;
        if p == target then
            local path, id = {}, p:GetPlotIndex();
            while id do table.insert(path, 1, Map.GetPlotByIndex(id)); id = parents[id]; end
            return path;
        end
        for d = 0, 5 do
            local n = Map.PlotDirection(p:GetX(), p:GetY(), d);
            if n and parents[n:GetPlotIndex()] == nil and n:GetOwner() == owner
                and n:IsRevealed(team, false) and not n:IsWater() and not n:IsMountain()
                and not n:IsImpassable() and distance(from, n) <= 6 and safe(n, owner) then
                parents[n:GetPlotIndex()] = p:GetPlotIndex(); queue[#queue + 1] = n;
            end
        end
    end
end

function A.OnTurn(owner)
    local player = Players[owner];
    if not player or not player:IsAlive() or player:IsHuman() or player:IsBarbarian() then return; end
    local key = "RealisticTerrain.v2.IrrigationAI." .. owner;
    if saved.GetValue(key) == Game.GetGameTurn() then return; end
    saved.SetValue(key, Game.GetGameTurn());
    if not Teams[player:GetTeam()]:GetTeamTechs():HasTech(I.TECH_ENGINEERING) then return; end
    if LuaEvents then LuaEvents.RO_RunAI(owner); end
    local workers = {};
    for u in player:Units() do
        if RT_Construction.IsWorker(u) then workers[#workers + 1] = u; end
    end
    if #workers == 0 then return; end
    table.sort(workers, function(a, b) return a:GetID() < b:GetID(); end);
    local jobs, potential = {}, {};
    for id = 0, Map.GetNumPlots() - 1 do
        local p = Map.GetPlotByIndex(id);
        if p:GetOwner() == owner and p:IsRevealed(player:GetTeam(), false) and safe(p, owner) then
            if F.IsFarm(p) and p:IsImprovementPillaged() then jobs[#jobs + 1] = { plot = p, repair = true };
            elseif F.Site(p, owner) and F.Connected(p, owner) then
                local city = p:GetWorkingCity();
                if city and city:GetOwner() == owner then
                    if city:GetNumBuilding(I.BUILDING_RT_IRRIGATION_WORKS) > 0 then jobs[#jobs + 1] = { plot = p };
                    else potential[city:GetID()] = (potential[city:GetID()] or 0) + 1; end
                end
            end
        end
    end
    -- Append one useful building using normal production; never replace a queue.
    if player:GetBuildingClassMaking(I.BUILDINGCLASS_RT_IRRIGATION_WORKS) == 0
        and (player:CalculateGoldRate() >= 1 or player:GetGold() >= 100) then
        for city in player:Cities() do
            if (potential[city:GetID()] or 0) >= 1 and city:CanConstruct(I.BUILDING_RT_IRRIGATION_WORKS) then
                city:PushOrder(OrderTypes.ORDER_CONSTRUCT, I.BUILDING_RT_IRRIGATION_WORKS, -1, false, false, true);
                break;
            end
        end
    end
    local bestUnit, bestJob, bestPath, bestScore;
    for _, u in ipairs(workers) do
        if u:GetMoves() > 0 and not u:IsEmbarked() and not u:IsAutomated() and not u:IsBusy()
            and u:GetBuildType() == -1 and not RT_ConstructionOrders.IsOrdered(u)
            and not RT_ConstructionOrders.HasWorked(u)
            and not (RT_OutpostBridge and RT_OutpostBridge.Reserved(u)) then
            for _, job in ipairs(jobs) do
                local dist = distance(u:GetPlot(), job.plot);
                if dist <= 6 then
                    local score = (job.repair and 100 or 20) - dist;
                    if not bestScore or score > bestScore then
                        local path = A.Path(u:GetPlot(), job.plot, owner);
                        if path then bestUnit, bestJob, bestPath, bestScore = u, job, path, score; end
                    end
                end
            end
        end
    end
    if not bestUnit then return; end
    if #bestPath > 1 then
        if bestUnit:CanMoveThrough(bestPath[2]) then
            bestUnit:PushMission(MissionTypes.MISSION_MOVE_TO, bestPath[2]:GetX(), bestPath[2]:GetY());
            bestUnit:FinishMoves();
        end
    elseif bestJob.repair then
        if bestUnit:CanBuild(bestJob.plot, I.BUILD_REPAIR, false, true) then
            bestUnit:PushMission(MissionTypes.MISSION_BUILD, I.BUILD_REPAIR);
        end
    else RT_ConstructionOrders.Start(bestUnit, "irrigation", true); end
end

function A.Initialize() GameEvents.PlayerDoTurn.Add(A.OnTurn); end
