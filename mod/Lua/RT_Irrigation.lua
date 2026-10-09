-- Water flows only through intact, same-owner irrigated farms. Both the wet and
-- dry variants are network nodes; only real terrain sources seed the flood fill.
RT_Irrigation = {};
local F, I = RT_Irrigation, GameInfoTypes;
local wet, dry = I.IMPROVEMENT_RT_IRRIGATED_FARM, I.IMPROVEMENT_RT_DRY_FARM;
assert(wet and dry and I.BUILDING_RT_IRRIGATION_WORKS, "Realistic Terrain: irrigation data missing.");
local refreshing = false;

function F.IsFarm(plot)
    return plot and (plot:GetImprovementType() == wet or plot:GetImprovementType() == dry) or false;
end

function F.Source(plot)
    if plot:IsRiver() then return true; end
    for d = 0, 5 do
        local p = Map.PlotDirection(plot:GetX(), plot:GetY(), d);
        if p and (p:IsMountain() or p:IsLake() or p:GetFeatureType() == I.FEATURE_OASIS) then return true; end
    end
    return false;
end

local function carries(plot, owner)
    return F.IsFarm(plot) and plot:GetOwner() == owner and not plot:IsImprovementPillaged()
        and not plot:IsWater() and not plot:IsMountain() and not plot:GetPlotCity();
end

-- Read-only live query, also used for prospective construction. Never trust the
-- wet artwork/state as proof of a source: it may have been severed this turn.
function F.Connected(plot, owner)
    if not plot or owner < 0 or plot:GetOwner() ~= owner then return false; end
    if F.IsFarm(plot) and not carries(plot, owner) then return false; end
    local queue, head, seen = { plot }, 1, { [plot:GetPlotIndex()] = true };
    while head <= #queue do
        local p = queue[head]; head = head + 1;
        if F.Source(p) then return true; end
        for d = 0, 5 do
            local n = Map.PlotDirection(p:GetX(), p:GetY(), d);
            if n and not seen[n:GetPlotIndex()] and carries(n, owner) then
                seen[n:GetPlotIndex()] = true; queue[#queue + 1] = n;
            end
        end
    end
    return false;
end

function F.Site(plot, owner)
    if not plot or plot:GetOwner() ~= owner or plot:IsWater() or plot:IsMountain()
        or plot:IsHills() or plot:GetPlotCity() or plot:GetTerrainType() ~= I.TERRAIN_DESERT then return false; end
    local feature = plot:GetFeatureType();
    if feature >= 0 and feature ~= I.FEATURE_FLOOD_PLAINS then return false; end
    local resource = plot:GetResourceType(Players[owner]:GetTeam());
    if resource >= 0 and resource ~= I.RESOURCE_WHEAT then return false; end
    local improvement = plot:GetImprovementType();
    return improvement < 0 or improvement == I.IMPROVEMENT_FARM;
end

function F.BuildStatus(plot, owner)
    if not F.Site(plot, owner) then return false, "TXT_KEY_RT_IRRIGATION_PLOT"; end
    local city = plot:GetWorkingCity();
    if not city or city:GetOwner() ~= owner or city:GetNumBuilding(I.BUILDING_RT_IRRIGATION_WORKS) < 1 then
        return false, "TXT_KEY_RT_IRRIGATION_BUILDING";
    end
    if not F.Connected(plot, owner) then return false, "TXT_KEY_RT_IRRIGATION_WATER"; end
    return true, "TXT_KEY_RT_IRRIGATION_READY";
end

-- One multi-source traversal, O(map + farm edges), independent of visibility.
-- PlayerDoTurn is a fallback only: stock BNW processes city food before that
-- hook. Turn-boundary events also reconcile changes before the next owner acts.
function F.Refresh()
    if refreshing then return; end
    refreshing = true;
    local farms, queue, supplied, head = {}, {}, {}, 1;
    for id = 0, Map.GetNumPlots() - 1 do
        local p = Map.GetPlotByIndex(id);
        if F.IsFarm(p) then
            farms[#farms + 1] = p;
            local owner = p:GetOwner();
            if owner >= 0 and carries(p, owner) and F.Source(p) then
                supplied[id] = true; queue[#queue + 1] = p;
            end
        end
    end
    while head <= #queue do
        local p = queue[head]; head = head + 1;
        for d = 0, 5 do
            local n = Map.PlotDirection(p:GetX(), p:GetY(), d);
            if n and not supplied[n:GetPlotIndex()] and carries(n, p:GetOwner()) then
                supplied[n:GetPlotIndex()] = true; queue[#queue + 1] = n;
            end
        end
    end
    for _, p in ipairs(farms) do
        local target = supplied[p:GetPlotIndex()] and wet or dry;
        -- SetImprovementType repairs a pillaged improvement as a side effect.
        -- Leave pillaged nodes alone (native yields already zero) until repaired.
        if not p:IsImprovementPillaged() and p:GetImprovementType() ~= target then
            p:SetImprovementType(target, p:GetOwner());
        end
    end
    refreshing = false;
end

function F.Inspect(plot)
    if not F.IsFarm(plot) then return nil; end
    if plot:IsImprovementPillaged() then return "TXT_KEY_RT_IRRIGATION_PILLAGED"; end
    return F.Connected(plot, plot:GetOwner()) and "TXT_KEY_RT_IRRIGATION_CONNECTED" or "TXT_KEY_RT_IRRIGATION_DISCONNECTED";
end

function F.Initialize()
    Events.AIProcessingStartedForPlayer.Add(F.Refresh);
    Events.AIProcessingEndedForPlayer.Add(F.Refresh);
    Events.ActivePlayerTurnEnd.Add(F.Refresh);
    Events.SerialEventImprovementCreated.Add(F.Refresh);
    Events.SerialEventImprovementDestroyed.Add(F.Refresh);
    GameEvents.PlayerDoTurn.Add(F.Refresh);
    GameEvents.BuildFinished.Add(F.Refresh);
    GameEvents.CityCaptureComplete.Add(F.Refresh);
    GameEvents.CityBoughtPlot.Add(F.Refresh);
    Events.LoadScreenClose.Add(F.Refresh);
    F.Refresh();
end
