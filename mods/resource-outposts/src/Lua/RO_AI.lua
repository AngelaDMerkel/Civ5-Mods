-- Bounded, revealed-land expeditions. Persistent reservations coordinate with
-- trade logistics; all construction/production uses ordinary units and costs.
RO_AI = {};
local A, O, I = RO_AI, RO_Outposts, GameInfoTypes;
A.MAX_DISTANCE, A.MAX_WORKERS = 12, 2;
A.STALL_TURNS, A.RETRY_TURNS = 5, 5;
function A.DamagePercent(u) return 100 * u:GetDamage() / math.max(1, u:GetMaxHitPoints()); end
local function distance(a, b) return Map.PlotDistance(a:GetX(), a:GetY(), b:GetX(), b:GetY()); end
local function identity(u) return u:GetGameTurnCreated() .. ":" .. u:GetOriginalOwner() .. ":" .. u:GetUnitType(); end
local function roster(owner)
    local ai = O.state.ai[owner];
    if not ai then ai = { workers = {}, guards = {}, lastProduction = -100 }; O.state.ai[owner] = ai; end
    ai.escorts, ai.recovering = ai.escorts or {}, ai.recovering or {};
    ai.cooldowns = ai.cooldowns or {};
    return ai;
end
function A.Reserved(u)
    local ai = O.state.ai[u:GetOwner()];
    if not ai then return false; end
    local job = ai.workers[u:GetID()] or ai.guards[u:GetID()] or (ai.escorts or {})[u:GetID()] or (ai.recovering or {})[u:GetID()];
    return job ~= nil and job.identity == identity(u);
end
local function assignment(u, plot, role)
    local path = role and A.Path(u:GetPlot(), plot, u:GetOwner(), role == "workers");
    return { target = plot:GetPlotIndex(), identity = identity(u), lastProgress = Game.GetGameTurn(),
        bestDistance = path and #path - 1 or nil,
        bestWork = role == "workers" and plot:GetBuildProgress(O.IsOutpost(plot) and I.BUILD_REPAIR or O.build) or 0 };
end

local function hostile(plot, team)
    if not plot:IsVisible(team, false) then return false; end
    for i = 0, plot:GetNumUnits() - 1 do
        local u = plot:GetUnit(i);
        if O.IsTroop(u) and Teams[team]:IsAtWar(u:GetTeam()) then return true; end
    end
    return false;
end
function A.Safe(plot, owner)
    local team = Players[owner]:GetTeam();
    if hostile(plot, team) then return false; end
    for d = 0, 5 do
        local p = Map.PlotDirection(plot:GetX(), plot:GetY(), d);
        if p and hostile(p, team) then return false; end
    end
    return true;
end

function A.Path(from, target, owner, escorted)
    local team = Players[owner]:GetTeam();
    local queue, head, parents = { from }, 1, { [from:GetPlotIndex()] = false };
    while head <= #queue and head <= 2048 do
        local p = queue[head]; head = head + 1;
        if p == target then
            local path, id = {}, p:GetPlotIndex();
            while id do table.insert(path, 1, Map.GetPlotByIndex(id)); id = parents[id]; end
            return path;
        end
        for d = 0, 5 do
            local n = Map.PlotDirection(p:GetX(), p:GetY(), d);
            if n and parents[n:GetPlotIndex()] == nil and n:IsRevealed(team, false)
                and not n:IsWater() and not n:IsMountain() and not n:IsImpassable()
                and (n:GetOwner() < 0 or n:GetOwner() == owner)
                and distance(from, n) <= A.MAX_DISTANCE * 2
                and (A.Safe(n, owner) or escorted and not hostile(n, team)) then
                parents[n:GetPlotIndex()] = p:GetPlotIndex(); queue[#queue + 1] = n;
            end
        end
    end
end
local function move(u, target, escorted)
    if u:GetMoves() <= 0 or u:IsBusy() then return; end
    local path = A.Path(u:GetPlot(), target, u:GetOwner()) or escorted and A.Path(u:GetPlot(), target, u:GetOwner(), true);
    -- Stock BNW exposes CanMoveThrough, not CanMoveInto; GeneratePath is NYI.
    -- The native mission still enforces destination stacking and movement cost.
    if path and path[2] and u:CanMoveThrough(path[2]) then
        u:PushMission(MissionTypes.MISSION_MOVE_TO, path[2]:GetX(), path[2]:GetY());
        u:FinishMoves();
    end
end

-- Search once from the wounded unit, not once per city. Friendly land heals
-- normally; prefer a city when equally close and avoid occupied stacking slots.
local function spaceFor(u, p)
    for i = 0, p:GetNumUnits() - 1 do
        local other = p:GetUnit(i);
        if other ~= u and not other:IsDelayedDeath() and other:GetDomainType() == DomainTypes.DOMAIN_LAND
            and other:IsCombatUnit() == u:IsCombatUnit() then return false; end
    end
    return true;
end
function A.RecoveryTarget(u)
    local owner, from = u:GetOwner(), u:GetPlot();
    local team = Players[owner]:GetTeam();
    local queue, head, seen = { { plot = from, steps = 0 } }, 1, { [from:GetPlotIndex()] = true };
    local best, steps, firstStep;
    while head <= #queue and head <= 2048 do
        local node = queue[head]; head = head + 1;
        local p = node.plot;
        if steps and node.steps > steps then break; end
        if p:GetOwner() == owner and spaceFor(u, p) and A.Safe(p, owner) then
            if not best or p:GetPlotCity() and not best:GetPlotCity()
                or ((not not p:GetPlotCity()) == (not not best:GetPlotCity()) and p:GetPlotIndex() < best:GetPlotIndex()) then
                best, steps, firstStep = p, node.steps, node.first;
            end
        end
        for d = 0, 5 do
            local n = Map.PlotDirection(p:GetX(), p:GetY(), d);
            if n and not seen[n:GetPlotIndex()] and n:IsRevealed(team, false)
                and not n:IsWater() and not n:IsMountain() and not n:IsImpassable()
                and (n:GetOwner() < 0 or n:GetOwner() == owner) and A.Safe(n, owner)
                and distance(from, n) <= A.MAX_DISTANCE * 2 and spaceFor(u, n) and u:CanMoveThrough(n) then
                seen[n:GetPlotIndex()] = true;
                queue[#queue + 1] = { plot = n, steps = node.steps + 1, first = node.first or n };
            end
        end
    end
    return best, firstStep;
end

local function recover(u)
    local target, step = A.RecoveryTarget(u);
    if target and target ~= u:GetPlot() then
        if step and u:GetMoves() > 0 and not u:IsBusy() then
            u:PushMission(MissionTypes.MISSION_MOVE_TO, step:GetX(), step:GetY()); u:FinishMoves();
        end
    elseif not u:IsBusy() and u:GetMoves() > 0 then
        -- Do not FinishMoves here: stock healing requires an unmoved unit.
        -- The heal activity keeps the unit resting without spending movement.
        u:PushMission(MissionTypes.MISSION_HEAL);
    end
end

local function cooling(ai, plot)
    return (ai.cooldowns[plot:GetPlotIndex()] or -1) > Game.GetGameTurn();
end

local function stalled(ai, role, u, plot, job)
    if role == "guards" and u:GetPlot() == plot then return false; end
    local path = A.Path(u:GetPlot(), plot, u:GetOwner(), role == "workers");
    local remaining = path and #path - 1 or distance(u:GetPlot(), plot);
    local work = role == "workers" and plot:GetBuildProgress(O.IsOutpost(plot) and I.BUILD_REPAIR or O.build) or 0;
    local escortGap;
    if role == "workers" then
        for id, escortJob in pairs(ai.escorts) do
            local escort = Players[u:GetOwner()]:GetUnitByID(id);
            if escortJob.worker == u:GetID() and O.IsTroop(escort) and identity(escort) == escortJob.identity then
                local approach = A.Path(escort:GetPlot(), u:GetPlot(), u:GetOwner(), true);
                escortGap = approach and #approach - 1 or distance(escort:GetPlot(), u:GetPlot());
            end
        end
    end
    if job.bestDistance == nil or remaining < job.bestDistance or work > (job.bestWork or 0)
        or escortGap and job.escortGap and escortGap < job.escortGap then job.lastProgress = Game.GetGameTurn(); end
    job.bestDistance = math.min(job.bestDistance or remaining, remaining);
    job.bestWork = math.max(job.bestWork or 0, work);
    job.escortGap = escortGap;
    return Game.GetGameTurn() - job.lastProgress >= A.STALL_TURNS;
end

function A.Budget(owner)
    local player, troops = Players[owner], 0;
    for u in player:Units() do if O.IsTroop(u) then troops = troops + 1; end end
    local beforeOutposts = player:CalculateGoldRate() + (O.state.maintenance[owner] or 0);
    local sustainable = math.floor(math.max(0, beforeOutposts + math.max(0, player:GetGold()) / 40) / (O.UPKEEP * 4));
    return math.min(sustainable, 1 + math.floor(troops / 2));
end

function A.Priority(plot, owner)
    local resource, quantity = O.Resource(plot, owner);
    if not resource then return 0; end
    local scarce = Players[owner]:GetNumResourceAvailable(resource, true) - (O.Owner(plot) == owner and quantity or 0) <= 0;
    local strategic = GameInfo.Resources[resource].ResourceClassType ~= "RESOURCECLASS_LUXURY";
    return (scarce and (strategic and 180 or 120) or 30) + math.min(quantity, 8);
end

function A.CanWork(unit)
    if A.DamagePercent(unit) >= 50 then return false; end
    if A.Safe(unit:GetPlot(), unit:GetOwner()) then return true; end
    local ai = roster(unit:GetOwner());
    for id, job in pairs(ai.escorts) do
        local escort = Players[unit:GetOwner()]:GetUnitByID(id);
        if job.worker == unit:GetID() and O.IsTroop(escort) and identity(escort) == job.identity
            and not escort:IsAutomated() and escort:GetPlot() == unit:GetPlot() and A.DamagePercent(escort) < 50 then return true; end
    end
    return false;
end

local function nearCity(plot, player)
    local best;
    for c in player:Cities() do
        local d = distance(plot, c:Plot());
        if not best or d < best then best = d; end
    end
    return best and best <= A.MAX_DISTANCE, best;
end
local function workerJob(plot, owner)
    if not plot then return false; end
    if O.IsOutpost(plot) then
        return O.Owner(plot) == owner and plot:IsImprovementPillaged()
            and (plot:GetOwner() < 0 or plot:GetOwner() == owner);
    end
    return O.CanConstruct(plot, owner);
end
local function ownSite(plot, owner)
    return plot and O.IsOutpost(plot) and O.Owner(plot) == owner;
end
local function capturable(plot, owner)
    if not plot or plot:GetOwner() >= 0 or not O.IsOutpost(plot) then return false; end
    local other = O.Owner(plot);
    return other >= 0 and other ~= owner and plot:IsVisible(Players[owner]:GetTeam(), false)
        and (not Players[other]:IsAlive() or Teams[Players[owner]:GetTeam()]:IsAtWar(Players[other]:GetTeam()));
end
local function available(u)
    return not u:IsDelayedDeath() and not u:IsEmbarked() and not u:IsAutomated() and not u:IsBusy()
        and u:GetBuildType() == -1 and not RO_Orders.IsOrdered(u)
        and not RO_Integration.OtherOrder(u, "reserved");
end

local function commission(player, ai, needWorker, needGuard)
    if not needWorker and not needGuard then return; end
    if player:CalculateGoldRate() < 0 and player:GetGold() < 50 then return; end
    if Game.GetGameTurn() - ai.lastProduction < 10 then return; end
    local unitType;
    -- Respect civilization replacements (e.g. unique worker/warrior classes).
    local overrides = {};
    for row in GameInfo.Civilization_UnitClassOverrides { CivilizationType = GameInfo.Civilizations[player:GetCivilizationType()].Type } do
        overrides[row.UnitClassType] = row.UnitType or false;
    end
    for city in player:Cities() do
        local best, strength = nil, -1;
        for row in GameInfo.Units() do
            local class = GameInfo.UnitClasses[row.Class];
            local expected = overrides[row.Class];
            if expected == nil then expected = class.DefaultUnit; end
            local worker = row.Class == "UNITCLASS_WORKER";
            if row.Type == expected and row.Domain == "DOMAIN_LAND"
                and ((needWorker and worker) or (not needWorker and needGuard and row.Combat > 0 and row.RangedCombat == 0))
                and player:GetUnitClassMaking(I[row.Class]) == 0 and city:CanTrain(row.ID) then
                local score = worker and 0 or row.Combat;
                if score > strength then best, strength = row.ID, score; end
            end
        end
        if best then unitType = best; city:PushOrder(OrderTypes.ORDER_TRAIN, unitType, -1, false, false, true); break; end
    end
    if unitType then
        ai.lastProduction = Game.GetGameTurn();
        if not needWorker then ai.guardCommissionTurn = Game.GetGameTurn(); ai.guardType = unitType; end
    end
end

function A.OnTurn(owner)
    local player = Players[owner];
    if not player or not player:IsAlive() or player:IsHuman() or player:IsBarbarian() then return; end
    local ai = roster(owner);
    if ai.turn == Game.GetGameTurn() then return; end
    ai.turn = Game.GetGameTurn();
    local budget = A.Budget(owner);
    local workers, troops = {}, {};
    for u in player:Units() do
        if RO_Outposts.IsWorker(u) then workers[#workers + 1] = u;
        elseif O.IsTroop(u) then troops[#troops + 1] = u; end
    end
    table.sort(workers, function(a, b) return a:GetID() < b:GetID(); end);
    table.sort(troops, function(a, b) return a:GetID() < b:GetID(); end);
    for target, untilTurn in pairs(ai.cooldowns) do
        if untilTurn <= Game.GetGameTurn() then ai.cooldowns[target] = nil; end
    end
    -- Keep recovering units reserved until health exceeds 75%.
    for id, job in pairs(ai.recovering) do
        local u = player:GetUnitByID(id);
        if not u or u:IsDelayedDeath() or identity(u) ~= job.identity or u:IsAutomated()
            or u:IsEmbarked() or A.DamagePercent(u) < 25 then ai.recovering[id] = nil;
        else recover(u); end
    end
    -- Revalidate every reservation; stale IDs, annexation, danger and replacement
    -- improvements must release units. Partial native build progress is retained.
    for _, role in ipairs({ "workers", "guards" }) do
        for id, job in pairs(ai[role]) do
            local u, plot = player:GetUnitByID(id), Map.GetPlotByIndex(job.target);
            local valid = u and not u:IsDelayedDeath() and identity(u) == job.identity and plot
                and not u:IsEmbarked() and not u:IsAutomated()
                and (role == "workers" and workerJob(plot, owner)
                    or role == "guards" and (ownSite(plot, owner) or capturable(plot, owner)))
                and (u:GetPlot() == plot or A.Path(u:GetPlot(), plot, owner, role == "workers") ~= nil);
            local timedOut = valid and stalled(ai, role, u, plot, job);
            if timedOut then ai.cooldowns[job.target] = Game.GetGameTurn() + A.RETRY_TURNS; end
            if not valid or timedOut or (u and A.DamagePercent(u) >= 50) then
                ai[role][id] = nil;
                if u and role == "workers" then RO_Orders.Cancel(u); end
                if u and not u:IsDelayedDeath() and not u:IsAutomated() and not u:IsEmbarked()
                    and A.DamagePercent(u) >= 50 and identity(u) == job.identity then
                    ai.recovering[id] = assignment(u, u:GetPlot());
                    recover(u);
                end
            end
        end
    end
    for id, job in pairs(ai.escorts) do
        local escort = player:GetUnitByID(id);
        if not O.IsTroop(escort) or escort:IsAutomated() or identity(escort) ~= job.identity or not ai.workers[job.worker] then ai.escorts[id] = nil;
        elseif A.DamagePercent(escort) >= 50 then ai.escorts[id] = nil; ai.recovering[id] = assignment(escort, escort:GetPlot()); recover(escort); end
    end
    local sites, jobs, captures, siteCount = {}, {}, {}, 0;
    for id = 0, Map.GetNumPlots() - 1 do
        local plot = Map.GetPlotByIndex(id);
        if ownSite(plot, owner) then
            siteCount = siteCount + 1; sites[#sites + 1] = plot;
            if not cooling(ai, plot) and workerJob(plot, owner) and not hostile(plot, player:GetTeam()) then jobs[#jobs + 1] = { plot = plot, score = 400 }; end
        elseif not cooling(ai, plot) and plot:IsRevealed(player:GetTeam(), false) and (capturable(plot, owner) or O.CanConstruct(plot, owner)) then
            local near, distanceToCity = nearCity(plot, player);
            if near and not hostile(plot, player:GetTeam()) then
                if capturable(plot, owner) then captures[#captures + 1] = plot;
                else
                    local resource = O.Resource(plot, owner);
                    local reachable = false;
                    for c in player:Cities() do
                        if distance(c:Plot(), plot) <= A.MAX_DISTANCE and A.Path(c:Plot(), plot, owner, true) then reachable = true; break; end
                    end
                    if reachable then jobs[#jobs + 1] = { plot = plot, score = A.Priority(plot, owner) - distanceToCity * 2 }; end
                end
            end
        end
    end
    table.sort(jobs, function(a, b) return a.score == b.score and a.plot:GetPlotIndex() < b.plot:GetPlotIndex() or a.score > b.score; end);
    local pendingCaptures = 0;
    for _, job in pairs(ai.guards) do
        if capturable(Map.GetPlotByIndex(job.target), owner) then pendingCaptures = pendingCaptures + 1; end
    end
    local used, assigned, builds = {}, 0, 0;
    for _, job in pairs(ai.workers) do
        used[job.target] = true; assigned = assigned + 1;
        if not ownSite(Map.GetPlotByIndex(job.target), owner) then builds = builds + 1; end
    end
    for _, job in ipairs(jobs) do
        local repair = ownSite(job.plot, owner);
        if not used[job.plot:GetPlotIndex()] and assigned < math.min(A.MAX_WORKERS, math.max(0, #workers - 1))
            and (repair or siteCount + builds + pendingCaptures < budget) then
            local best, length;
            for _, u in ipairs(workers) do
                if not A.Reserved(u) and available(u) and A.DamagePercent(u) < 50 then
                    local path = A.Path(u:GetPlot(), job.plot, owner, true);
                    if path and (not length or #path < length) then best, length = u, #path; end
                end
            end
            if best then
                ai.workers[best:GetID()] = assignment(best, job.plot, "workers");
                used[job.plot:GetPlotIndex()] = true; assigned = assigned + 1;
                if not repair then builds = builds + 1; end
            end
        end
    end
    local needsEscort = false;
    -- Escorts rendezvous with workers before traversing threatened tiles.
    for workerID, job in pairs(ai.workers) do
        local worker, plot = player:GetUnitByID(workerID), Map.GetPlotByIndex(job.target);
        local risk = not A.Safe(worker:GetPlot(), owner) or not A.Path(worker:GetPlot(), plot, owner);
        if risk then
            local escort;
            for id, e in pairs(ai.escorts) do if e.worker == workerID then escort = player:GetUnitByID(id); end end
            if not escort then
                for _, u in ipairs(troops) do
                    local commissioned = ai.guardCommissionTurn and u:GetGameTurnCreated() > ai.guardCommissionTurn and u:GetUnitType() == ai.guardType;
                    if not A.Reserved(u) and available(u) and A.DamagePercent(u) < 25 and (not u:GetPlot():GetPlotCity() or commissioned)
                        and u:GetPlot():GetImprovementType() ~= I.IMPROVEMENT_RT_RELIEF_STATION
                        and A.Path(u:GetPlot(), worker:GetPlot(), owner, true) then escort = u; break; end
                end
                if escort then
                    local e = assignment(escort, plot); e.worker = workerID; ai.escorts[escort:GetID()] = e;
                    job.lastProgress = Game.GetGameTurn(); job.escortGap = nil;
                    if ai.guardCommissionTurn and escort:GetGameTurnCreated() > ai.guardCommissionTurn and escort:GetUnitType() == ai.guardType then
                        ai.guardCommissionTurn, ai.guardType = nil, nil;
                    end
                else needsEscort = true; end
            end
        end
    end
    table.sort(sites, function(a,b)
        local pa, pb = A.Priority(a, owner), A.Priority(b, owner);
        return pa == pb and a:GetPlotIndex() < b:GetPlotIndex() or pa > pb;
    end);
    local guarded = {};
    for _, job in pairs(ai.guards) do guarded[job.target] = true; end
    local captureCount = 0;
    for _, job in pairs(ai.guards) do
        if capturable(Map.GetPlotByIndex(job.target), owner) then captureCount = captureCount + 1; end
    end
    for _, p in ipairs(captures) do
        if not guarded[p:GetPlotIndex()] and siteCount + builds + captureCount < budget then
            sites[#sites + 1] = p; captureCount = captureCount + 1;
        end
    end
    local needsGuard = needsEscort;
    for _, plot in ipairs(sites) do
        if not guarded[plot:GetPlotIndex()] and not cooling(ai, plot) then
            local best, length;
            for _, u in ipairs(troops) do
                local commissioned = ai.guardCommissionTurn and u:GetGameTurnCreated() > ai.guardCommissionTurn
                    and u:GetUnitType() == ai.guardType;
                if not A.Reserved(u) and available(u) and A.DamagePercent(u) < 50 and (not u:GetPlot():GetPlotCity() or commissioned)
                    and u:GetPlot():GetImprovementType() ~= I.IMPROVEMENT_RT_RELIEF_STATION then
                    local path = A.Path(u:GetPlot(), plot, owner);
                    if path and (not length or #path < length) then best, length = u, #path; end
                end
            end
            if best then
                ai.guards[best:GetID()] = assignment(best, plot, "guards");
                if ai.guardCommissionTurn and best:GetGameTurnCreated() > ai.guardCommissionTurn and best:GetUnitType() == ai.guardType then
                    ai.guardCommissionTurn, ai.guardType = nil, nil;
                end
            elseif ownSite(plot, owner) then needsGuard = true; end
        end
    end
    for id, job in pairs(ai.workers) do
        local u, plot = player:GetUnitByID(id), Map.GetPlotByIndex(job.target);
        local escort;
        for escortID, e in pairs(ai.escorts) do if e.worker == id then escort = player:GetUnitByID(escortID); end end
        if escort and escort:GetPlot() ~= u:GetPlot() then
            move(escort, u:GetPlot(), true); u:FinishMoves();
        elseif not escort and (not A.Safe(u:GetPlot(), owner) or not A.Path(u:GetPlot(), plot, owner)) then
            u:FinishMoves(); -- wait for protection, do not send a civilian alone
        elseif u:GetPlot() == plot then
            if O.IsOutpost(plot) then
                -- CvLuaUnit reads these optional flags as integers on stock BNW.
                if u:GetMoves() > 0 and u:CanBuild(plot, I.BUILD_REPAIR, 0, 1) then u:PushMission(MissionTypes.MISSION_BUILD, I.BUILD_REPAIR); end
            elseif not RO_Orders.IsOrdered(u, "outpost") then RO_Orders.Start(u, "outpost", true); end
            if escort then escort:FinishMoves(); end
        elseif escort then
            move(escort, plot, true);
            if escort:GetPlot() ~= u:GetPlot() and distance(escort:GetPlot(), u:GetPlot()) == 1 then move(u, escort:GetPlot(), true); end
        else move(u, plot); end
    end
    for id, job in pairs(ai.guards) do
        local u, plot = player:GetUnitByID(id), Map.GetPlotByIndex(job.target);
        if u:GetPlot() == plot then
            O.OnMoved(owner, id);
            if u:GetMoves() > 0 then
                if u:CanFortify(plot) then u:PushMission(MissionTypes.MISSION_FORTIFY); end
                u:FinishMoves();
            end
        else move(u, plot); end
    end
    local needWorker = #jobs > 0 and #workers < 2 and (siteCount < budget or jobs[1].score == 400);
    commission(player, ai, needWorker, needsGuard);
    O.Save();
end
function A.Initialize() GameEvents.PlayerDoTurn.Add(A.OnTurn); end
