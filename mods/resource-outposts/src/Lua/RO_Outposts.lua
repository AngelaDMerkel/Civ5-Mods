-- Single-deposit claims. Persist ONLY the contribution made by this module;
-- never derive it from a player's total (which includes trades and consumption).
RO_Outposts = {};
local O, I = RO_Outposts, GameInfoTypes;
O.improvement = I.IMPROVEMENT_RT_RESOURCE_OUTPOST;
O.build = I.BUILD_RT_RESOURCE_OUTPOST;
O.IsOutpost = RO_Eras.IsOutpost;
local saved = Modding.OpenSaveData();
local KEY = "ResourceOutposts.v1.State";
local record = saved.GetValue(KEY);
O.state = record and RO_Serialize.Decode(record) or { sites = {}, credited = {}, ai = {} };
local state, reconciling = O.state, false;
state.maintenance = state.maintenance or {};
O.UPKEEP = 2;
local function save() saved.SetValue(KEY, RO_Serialize.Encode(state)); end
O.Save = save;

local workers = {};
for row in GameInfo.Unit_Builds { BuildType = "BUILD_FORT" } do workers[I[row.UnitType]] = true; end
function O.IsWorker(unit)
    return unit and not unit:IsDelayedDeath() and workers[unit:GetUnitType()]
        and unit:GetDomainType() == DomainTypes.DOMAIN_LAND or false;
end

local extraction = {};
local normal = { IMPROVEMENT_MINE = true, IMPROVEMENT_QUARRY = true, IMPROVEMENT_PASTURE = true,
    IMPROVEMENT_CAMP = true, IMPROVEMENT_PLANTATION = true, IMPROVEMENT_WELL = true };
for row in GameInfo.Improvement_ResourceTypes() do
    if normal[row.ImprovementType] and (row.ResourceTrade == true or row.ResourceTrade == 1) then
        local list = extraction[row.ResourceType] or {}; extraction[row.ResourceType] = list;
        for build in GameInfo.Builds { ImprovementType = row.ImprovementType } do
            list[#list + 1] = build.PrereqTech or false;
        end
    end
end
local function hasTech(player, name)
    return not name or Teams[player:GetTeam()]:GetTeamTechs():HasTech(I[name]);
end

function O.Resource(plot, owner)
    local player = Players[owner];
    if not player or not player:IsAlive() or player:IsBarbarian() then return; end
    local id = plot:GetResourceType(player:GetTeam()); -- never inspect an unrevealed resource
    local resource = GameInfo.Resources[id];
    if not resource or not extraction[resource.Type]
        or (resource.ResourceClassType ~= "RESOURCECLASS_RUSH" and resource.ResourceClassType ~= "RESOURCECLASS_MODERN"
            and resource.ResourceClassType ~= "RESOURCECLASS_LUXURY") then return; end
    if not hasTech(player, resource.TechReveal) or not hasTech(player, resource.TechCityTrade) then return; end
    for _, tech in ipairs(extraction[resource.Type]) do
        if hasTech(player, tech) then return id, plot:GetNumResource(); end
    end
end

function O.Owner(plot)
    if not O.IsOutpost(plot) then return -1; end
    if plot:GetOwner() >= 0 then return plot:GetOwner(); end
    local site = state.sites[plot:GetPlotIndex()];
    return site and site.owner or -1;
end

local function landTroop(unit)
    return unit and not unit:IsDelayedDeath() and not unit:IsEmbarked()
        and unit:IsCombatUnit() and unit:GetDomainType() == DomainTypes.DOMAIN_LAND;
end
O.IsTroop = landTroop;

function O.Blockaded(plot, owner)
    local player = Players[owner];
    if not player then return true; end
    for i = 0, plot:GetNumUnits() - 1 do
        local u = plot:GetUnit(i);
        if landTroop(u) and Teams[player:GetTeam()]:IsAtWar(u:GetTeam()) then return true; end
    end
    return false;
end

function O.Inspect(plot)
    local owner = O.Owner(plot);
    if owner < 0 then return { owner = -1, amount = 0, mode = "removed", territory = -1 }; end
    local resource, quantity = O.Resource(plot, owner);
    local mode = plot:IsImprovementPillaged() and "pillaged" or O.Blockaded(plot, owner) and "blockaded"
        or not resource and "technology" or "active";
    return { owner = owner, amount = mode == "active" and quantity or 0, resource = resource or -1,
        mode = mode, territory = plot:GetOwner() };
end

local function notifyTransition(plot, previous, current, abandoned)
    if not previous then return; end -- initial completion/load is not a loss
    local reason;
    if abandoned then reason = "ABANDONED";
    elseif current.territory >= 0 and (previous.territory < 0 or previous.owner ~= current.owner) then reason = "ABSORBED";
    elseif current.owner >= 0 and current.owner ~= previous.owner then reason = "CAPTURED";
    elseif current.mode ~= previous.mode or current.amount ~= previous.amount or current.resource ~= previous.resource then reason = "SUPPLY_CHANGED"; end
    if not reason then return; end
    local recipients = { [previous.owner] = true }; if current.owner >= 0 then recipients[current.owner] = true; end
    for owner in pairs(recipients) do
        local player = Players[owner];
        if player and player:IsAlive() and player:IsHuman() then
            local resource = current.owner == owner and current.resource or previous.resource;
            if not resource or resource < 0 then resource = previous.resource; end
            local delta = (current.owner == owner and current.amount or 0) - (previous.owner == owner and previous.amount or 0);
            local resourceName = GameInfo.Resources[resource] and Locale.ConvertTextKey(GameInfo.Resources[resource].Description) or "";
            local body = Locale.ConvertTextKey("TXT_KEY_RO_CHANGE_BODY", Locale.ConvertTextKey("TXT_KEY_RO_" .. reason),
                resourceName, (delta > 0 and "+" or "") .. tostring(delta),
                Locale.ConvertTextKey("TXT_KEY_RO_STATUS_" .. string.upper(current.mode)));
            player:AddNotification(NotificationTypes.NOTIFICATION_GENERIC, body,
                Locale.ConvertTextKey("TXT_KEY_RT_RESOURCE_OUTPOST"), plot:GetX(), plot:GetY());
        end
    end
end

function O.Reconcile()
    if reconciling then return; end
    reconciling = true;
    local desired, maintenance = {}, {};
    for id, site in pairs(state.sites) do
        local plot = Map.GetPlotByIndex(id);
        if not O.IsOutpost(plot) then
            if plot and not site.converted then notifyTransition(plot, site.report, { owner = -1, amount = 0, mode = "removed", territory = -1 }, site.abandoned); end
            state.sites[id] = nil;
        else
            -- Annexed outposts follow native territorial ownership permanently.
            if plot:GetOwner() >= 0 then site.owner = plot:GetOwner(); end
            -- Keep the ledger guard active through native art swaps: dirty/build
            -- callbacks must not observe a temporary repair or bill the site twice.
            RO_Eras.Sync(plot, site.owner);
            local report = O.Inspect(plot);
            notifyTransition(plot, site.report, report);
            site.report = report;
            if Players[site.owner] and Players[site.owner]:IsAlive() and not Players[site.owner]:IsBarbarian() then
                maintenance[site.owner] = (maintenance[site.owner] or 0) + O.UPKEEP;
            end
            if plot:GetOwner() < 0 and not plot:IsImprovementPillaged() and not O.Blockaded(plot, site.owner) then
                local resource, quantity = O.Resource(plot, site.owner);
                if resource and quantity > 0 then
                    desired[site.owner] = desired[site.owner] or {};
                    desired[site.owner][resource] = (desired[site.owner][resource] or 0) + quantity;
                end
            end
        end
    end
    local owners = {};
    for owner in pairs(state.credited) do owners[owner] = true; end
    for owner in pairs(desired) do owners[owner] = true; end
    for owner in pairs(owners) do
        local old, new, resources = state.credited[owner] or {}, desired[owner] or {}, {};
        for resource in pairs(old) do resources[resource] = true; end
        for resource in pairs(new) do resources[resource] = true; end
        for resource in pairs(resources) do
            local delta = (new[resource] or 0) - (old[resource] or 0);
            if delta ~= 0 and Players[owner] then Players[owner]:ChangeNumResourceTotal(resource, delta); end
        end
    end
    state.credited = desired;
    local billed = {};
    for owner in pairs(state.maintenance) do billed[owner] = true; end
    for owner in pairs(maintenance) do billed[owner] = true; end
    for owner in pairs(billed) do
        local delta = (maintenance[owner] or 0) - (state.maintenance[owner] or 0);
        if delta ~= 0 and Players[owner] then Players[owner]:ChangeBaseBuildingGoldMaintenance(delta); end
    end
    state.maintenance = maintenance;
    save();
    reconciling = false;
end

function O.OnBuilt(owner, x, y, improvement)
    local plot = Map.GetPlot(x, y);
    if not plot then return; end
    -- A road or repair must never change a surviving neutral site's owner.
    if RO_Eras.IsType(improvement) and O.IsOutpost(plot)
        and not state.sites[plot:GetPlotIndex()] then
        state.sites[plot:GetPlotIndex()] = { owner = owner };
    end
    O.Reconcile();
end

function O.OnMoved(owner, unitID)
    local player = Players[owner];
    local unit = player and player:GetUnitByID(unitID);
    local plot = unit and unit:GetPlot();
    if O.IsOutpost(plot) and plot:GetOwner() < 0
        and landTroop(unit) and not player:IsBarbarian() then
        local site = state.sites[plot:GetPlotIndex()];
        if site and site.owner ~= owner and (not Players[site.owner]:IsAlive()
            or Teams[player:GetTeam()]:IsAtWar(Players[site.owner]:GetTeam())) then
            site.owner = owner;
        end
    end
    O.Reconcile();
end

function O.CanConstruct(plot, owner)
    local player = Players[owner];
    if not player or not hasTech(player, "TECH_ENGINEERING") then return false, "TXT_KEY_RO_BUILD_TECH"; end
    if not plot or plot:IsWater() or plot:IsMountain() or plot:GetPlotCity() or plot:GetOwner() >= 0
        or plot:GetImprovementType() >= 0 then return false, "TXT_KEY_RT_OUTPOST_SITE"; end
    if not O.Resource(plot, owner) then return false, "TXT_KEY_RT_OUTPOST_RESOURCE"; end
    if not plot:CanBuild(O.build, owner, false, true) then return false, "TXT_KEY_RT_OUTPOST_SITE"; end
    for row in GameInfo.BuildFeatures { BuildType = "BUILD_RT_RESOURCE_OUTPOST" } do
        if I[row.FeatureType] == plot:GetFeatureType() and not hasTech(player, row.PrereqTech) then
            return false, "TXT_KEY_RO_BUILD_FEATURE_TECH";
        end
    end
    return true, "TXT_KEY_RO_BUILD_WORK_HELP";
end

function O.Status(unit, scheduled)
    if not RO_Outposts.IsWorker(unit) then return false, "TXT_KEY_RO_BUILD_WORKER"; end
    local owner = unit:GetOwner();
    if (not scheduled and owner ~= Game.GetActivePlayer()) or not Players[owner]:IsTurnActive() then
        return false, "TXT_KEY_RO_BUILD_TURN";
    end
    if unit:IsEmbarked() then return false, "TXT_KEY_RT_OUTPOST_SITE"; end
    if scheduled and not Players[owner]:IsHuman() and RO_AI and not RO_AI.CanWork(unit) then return false, "TXT_KEY_RO_ESCORT"; end
    local valid, reason = O.CanConstruct(unit:GetPlot(), owner);
    if not valid then return valid, reason; end
    if unit:IsAutomated() or unit:IsBusy() or unit:GetBuildType() ~= -1 then return false, "TXT_KEY_RO_BUILD_BUSY"; end
    for i = 0, unit:GetPlot():GetNumUnits() - 1 do
        local other = unit:GetPlot():GetUnit(i);
        if other ~= unit and other:GetBuildType() ~= -1 then return false, "TXT_KEY_RO_BUILD_BUSY"; end
    end
    if unit:GetMoves() <= 0 or unit:WorkRate(false) <= 0 then return false, "TXT_KEY_RO_BUILD_MOVES"; end
    return true, "TXT_KEY_RO_BUILD_WORK_HELP";
end

function O.Abandon(owner, plot)
    local player = Players[owner];
    if owner ~= Game.GetActivePlayer() or not player or not player:IsTurnActive()
        or not plot or O.Owner(plot) ~= owner then return false; end
    local site = state.sites[plot:GetPlotIndex()];
    if site then site.abandoned = true; end
    plot:SetImprovementType(-1); -- native accounting handles already-annexed tiles
    O.Reconcile();
    return true;
end

function O.Progress(unit)
    return unit:GetPlot():GetBuildProgress(O.build), unit:GetPlot():GetBuildTime(O.build, unit:GetOwner());
end
function O.Work(unit, scheduled)
    if not O.Status(unit, scheduled) then return false; end
    local plot, owner, work = unit:GetPlot(), unit:GetOwner(), unit:WorkRate(false);
    unit:FinishMoves();
    local finished = plot:ChangeBuildProgress(O.build, work, owner);
    if finished then O.OnBuilt(owner, plot:GetX(), plot:GetY(), O.improvement); end
    return true, finished;
end

function O.Initialize()
    O.Reconcile();
    GameEvents.PlayerDoTurn.Add(O.Reconcile);
    GameEvents.UnitSetXY.Add(O.OnMoved);
    GameEvents.BuildFinished.Add(O.OnBuilt);
    GameEvents.CityCaptureComplete.Add(O.Reconcile);
    GameEvents.CityBoughtPlot.Add(O.Reconcile);
    GameEvents.PlayerCityFounded.Add(O.Reconcile);
    GameEvents.TeamTechResearched.Add(O.Reconcile);
    Events.WarStateChanged.Add(O.Reconcile);
    -- Rendering events are only early refresh hints; correctness also has an
    -- unconditional turn check, including for improvements outside human sight.
    Events.SerialEventGameDataDirty.Add(O.Reconcile);
    Events.LoadScreenClose.Add(O.Reconcile);
end
