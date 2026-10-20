-- Real road connectivity, independent of the game's city trade/harbor network.
-- No persistent connection cache: pillage, occupation and city capture must take
-- effect at the next check even if the engine emits no dedicated route event.
RT_Supply = {};
local S = RT_Supply;
local saved = Modding.OpenSaveData();
local stationID = GameInfoTypes.IMPROVEMENT_RT_RELIEF_STATION;
local roadID, railID = GameInfoTypes.ROUTE_ROAD, GameInfoTypes.ROUTE_RAILROAD;
local PREFIX = "RealisticTerrain.v1.ReliefBuilder.";
assert(stationID and roadID and railID, "Realistic Terrain: relief station/route data missing.");

local function key(plot) return plot:GetX() .. "." .. plot:GetY(); end

function S.Owner(plot)
    -- Territorial ownership takes precedence over the original builder.
    local owner = plot:GetOwner();
    if owner >= 0 then return owner; end
    return tonumber(saved.GetValue(PREFIX .. key(plot))) or -1;
end

function S.OnBuildFinished(playerID, x, y, improvement)
    local plot = Map.GetPlot(x, y);
    if not plot then return; end
    if improvement == stationID and plot:GetImprovementType() == stationID then
        saved.SetValue(PREFIX .. key(plot), playerID);
    elseif plot:GetImprovementType() ~= stationID then
        saved.SetValue(PREFIX .. key(plot), -1);
    end
    -- Road construction and repairs on the station preserve its original builder.
end

local function occupiedByEnemy(plot, team)
    for i = 0, plot:GetNumUnits() - 1 do
        local unit = plot:GetUnit(i);
        if unit and not unit:IsDelayedDeath() and Teams[team]:IsAtWar(unit:GetTeam()) then return true; end
    end
    return false;
end

local function usable(plot, playerID, team)
    if plot:IsWater() or plot:IsMountain() then return false; end
    local owner = plot:GetOwner();
    -- Trade agreements can extend supply through a partner's territory.
    if owner >= 0 and owner ~= playerID and not (S.CanTransit and S.CanTransit(playerID, owner)) then return false; end
    if occupiedByEnemy(plot, team) then return false; end
    local city = plot:GetPlotCity();
    if city then return true; end -- only an owner's city terminates the search
    local route = plot:GetRouteType();
    return (route == roadID or route == railID) and not plot:IsRoutePillaged();
end

function S.Connected(station, playerID)
    if station:GetImprovementType() ~= stationID or station:IsImprovementPillaged()
        or S.Owner(station) ~= playerID then return false; end
    local player = Players[playerID];
    if not player or not player:IsAlive() then return false; end
    local team = player:GetTeam();
    if not usable(station, playerID, team) then return false; end
    -- Breadth-first search supports branched routes and avoids looping forever.
    local queue, head, seen = { station }, 1, { [key(station)] = true };
    while head <= #queue do
        local plot = queue[head]; head = head + 1;
        local city = plot:GetPlotCity();
        if city and city:GetOwner() == playerID then return true; end
        for direction = 0, 5 do
            local nextPlot = Map.PlotDirection(plot:GetX(), plot:GetY(), direction);
            if nextPlot then
                local id = key(nextPlot);
                if not seen[id] then
                    seen[id] = true;
                    if usable(nextPlot, playerID, team) then queue[#queue + 1] = nextPlot; end
                end
            end
        end
    end
    return false;
end

-- Nearby includes the current tile and its six neighbors. Only land units use it.
function S.Find(unit, nearby)
    local found = false;
    for _, plot in ipairs(nearby) do
        if plot:GetImprovementType() == stationID and S.Owner(plot) == unit:GetOwner() then
            found = true;
            if S.Connected(plot, unit:GetOwner()) then return true, true; end
        end
    end
    return false, found;
end
