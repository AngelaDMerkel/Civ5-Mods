-- Stock BNW cannot veto a normal worker build by player building ownership.
-- A dedicated construction order checks the Ministry, then contributes one worker-turn
-- using the engine's persistent build progress and speed-adjusted build time.
-- No Unit_Builds assignment exists for this action, so native missions cannot
-- bypass the gate. Irrigated farms use the same persistent worker machinery.
RT_Construction = {};
local B = RT_Construction;
local buildID = GameInfoTypes.BUILD_RT_RELIEF_STATION;
local ministryID = GameInfoTypes.BUILDING_CARAVANSARY;
assert(buildID and ministryID, "Realistic Terrain: Caravansary construction data missing.");

local workers = {};
for row in GameInfo.Unit_Builds { BuildType = "BUILD_FORT" } do
    workers[GameInfoTypes[row.UnitType]] = true;
end

function B.IsWorker(unit)
    return unit and not unit:IsDelayedDeath() and workers[unit:GetUnitType()]
        and unit:GetDomainType() == DomainTypes.DOMAIN_LAND or false;
end

function B.Status(unit, scheduled, kind)
    kind = kind or "station";
    if kind ~= "station" and kind ~= "irrigation" then return false, "TXT_KEY_RT_BUILD_PLOT"; end
    if not B.IsWorker(unit) then return false, "TXT_KEY_RT_BUILD_WORKER"; end
    local playerID = unit:GetOwner();
    local player = Players[playerID];
    if (not scheduled and playerID ~= Game.GetActivePlayer()) or not player:IsTurnActive() then
        return false, "TXT_KEY_RT_BUILD_TURN";
    end
    if kind == "station" and player:CountNumBuildings(ministryID) < 1 then
        return false, "TXT_KEY_RT_BUILD_MINISTRY";
    end
    local techs = Teams[player:GetTeam()]:GetTeamTechs();
    local action = kind == "irrigation" and GameInfoTypes.BUILD_RT_IRRIGATED_FARM or buildID;
    local build = GameInfo.Builds[action];
    if not techs:HasTech(GameInfoTypes[build.PrereqTech]) then
        return false, "TXT_KEY_RT_BUILD_TECH";
    end
    local plot = unit:GetPlot();
    if kind == "irrigation" then
        local allowed, reason = RT_Irrigation.BuildStatus(plot, playerID);
        if not allowed then return false, reason; end
    end
    if not plot or unit:IsEmbarked() or plot:IsWater() or plot:IsMountain()
        or (plot:GetOwner() >= 0 and plot:GetOwner() ~= playerID)
        or not plot:CanBuild(action, playerID, false, true) then
        return false, "TXT_KEY_RT_BUILD_PLOT";
    end
    -- Honor feature work prerequisites even though these builds keep the feature.
    for row in GameInfo.BuildFeatures { BuildType = build.Type } do
        if row.PrereqTech and GameInfoTypes[row.FeatureType] == plot:GetFeatureType()
            and not techs:HasTech(GameInfoTypes[row.PrereqTech]) then
            return false, "TXT_KEY_RT_BUILD_FEATURE_TECH";
        end
    end
    if unit:IsAutomated() or unit:IsBusy() or unit:GetBuildType() ~= -1 then
        return false, "TXT_KEY_RT_BUILD_BUSY";
    end
    -- Do not contribute to a tile on which another worker is doing another job.
    for i = 0, plot:GetNumUnits() - 1 do
        local other = plot:GetUnit(i);
        if other and other ~= unit and other:GetBuildType() ~= -1 then
            return false, "TXT_KEY_RT_BUILD_BUSY";
        end
    end
    if unit:GetMoves() <= 0 or unit:WorkRate(false) <= 0 then
        return false, "TXT_KEY_RT_BUILD_MOVES";
    end
    return true, "TXT_KEY_RT_BUILD_WORK_HELP";
end

function B.Progress(unit, kind)
    local plot = unit:GetPlot();
    local action = kind == "irrigation" and GameInfoTypes.BUILD_RT_IRRIGATED_FARM or buildID;
    return plot:GetBuildProgress(action), plot:GetBuildTime(action, unit:GetOwner());
end

function B.Work(unit, scheduled, kind)
    local allowed = B.Status(unit, scheduled, kind);
    if not allowed then return false; end
    local plot, owner = unit:GetPlot(), unit:GetOwner();
    local rate = unit:WorkRate(false);
    -- WorkRate must be captured before consuming movement, as in CvUnit::build.
    -- Consume movement first to reject any reentrant UI callbacks on progress.
    unit:FinishMoves();
    local action = kind == "irrigation" and GameInfoTypes.BUILD_RT_IRRIGATED_FARM or buildID;
    local finished = plot:ChangeBuildProgress(action, rate, owner);
    if finished and kind == "irrigation" then RT_Irrigation.Refresh();
    elseif finished then
        -- BuildFinished is emitted by the native unit mission, which this UI
        -- action does not use. Record the neutral-land builder explicitly.
        RT_Supply.OnBuildFinished(owner, plot:GetX(), plot:GetY(), plot:GetImprovementType());
    end
    return true, finished;
end
