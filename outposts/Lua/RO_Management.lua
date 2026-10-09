-- Read-only consequences and explicit owner actions for the outpost controls.
RO_Management = {};
local M, O, I = RO_Management, RO_Outposts, GameInfoTypes;
local normal = { IMPROVEMENT_MINE = true, IMPROVEMENT_QUARRY = true, IMPROVEMENT_PASTURE = true,
    IMPROVEMENT_CAMP = true, IMPROVEMENT_PLANTATION = true, IMPROVEMENT_WELL = true };
local function hasTech(player, tech)
    return not tech or Teams[player:GetTeam()]:GetTeamTechs():HasTech(I[tech]);
end

-- Stock CvPlot::getNumResourceForPlayer is not exposed to Lua. Mirror its
-- terrain/resource traits and city luxury bonus for annexed tiles only.
local function nativeQuantity(plot, player, resource)
    local quantity = plot:GetNumResource();
    if not hasTech(player, resource.TechReveal)
        or resource.PolicyReveal and not player:HasPolicy(I[resource.PolicyReveal]) then return quantity; end
    local terrainMod, resourceMod = 0, 0;
    local leader = GameInfo.Leaders[player:GetLeaderType()];
    if leader then
        for link in GameInfo.Leader_Traits { LeaderType = leader.Type } do
            local trait = GameInfo.Traits[link.TraitType];
            if trait and hasTech(player, trait.PrereqTech) and (not trait.ObsoleteTech or not hasTech(player, trait.ObsoleteTech)) then
                for row in GameInfo.Trait_Terrains { TraitType = trait.Type } do
                    if I[row.TerrainType] == plot:GetTerrainType() then terrainMod = row.StrategicResourceQuantityModifier; end
                end
                for row in GameInfo.Trait_ResourceQuantityModifiers { TraitType = trait.Type, ResourceType = resource.Type } do
                    resourceMod = row.ResourceQuantityModifier;
                end
            end
        end
    end
    if resource.ResourceClassType == "RESOURCECLASS_LUXURY" then
        local city = plot:GetWorkingCity();
        if city then
            for building in GameInfo.Buildings() do
                if (building.ExtraLuxuries or 0) > 0 and city:GetNumBuilding(building.ID) > 0 then quantity = quantity + 1; break; end
            end
        end
    else quantity = math.floor(quantity * (100 + terrainMod) / 100); end
    if resourceMod > 0 then quantity = math.floor(quantity * (100 + resourceMod) / 100); end
    return quantity;
end

function M.Preview(owner, plot)
    if not plot or O.Owner(plot) ~= owner then return; end
    local player = Players[owner];
    local resourceID = plot:GetResourceType(player:GetTeam());
    local resource = GameInfo.Resources[resourceID];
    local result = { resource = resourceID, loss = 0, baseUpkeep = O.UPKEEP, before = 0, after = 0 };
    if not resource then return result; end
    local raw = 0;
    if plot:GetOwner() >= 0 then
        if not plot:IsImprovementPillaged() and hasTech(player, resource.TechCityTrade) then raw = nativeQuantity(plot, player, resource); end
    else raw = O.Inspect(plot).amount; end
    local factor = 0;
    if resource.ResourceClassType ~= "RESOURCECLASS_LUXURY" then
        for policy in GameInfo.Policies() do
            if player:HasPolicy(policy.ID) and not player:IsPolicyBlocked(policy.ID) then factor = factor + (policy.StrategicResourceMod or 0); end
        end
    end
    if factor == 0 then factor = 100; end
    -- Recover the raw domestic count before the native multiplier and exports.
    -- Stock BNW uses a 200% policy; the interval also handles fractional mods.
    local domestic = player:GetNumResourceTotal(resourceID, false) + player:GetResourceExport(resourceID);
    local rawMin = math.ceil(domestic * 100 / factor);
    local rawMax = math.ceil((domestic + 1) * 100 / factor) - 1;
    result.loss = math.max(0, domestic - math.floor((rawMin - raw) * factor / 100));
    result.estimated = rawMin ~= rawMax;
    result.before = player:GetNumResourceAvailable(resourceID, true);
    result.after = result.before - result.loss;
    result.lastLuxury = resource.ResourceClassType == "RESOURCECLASS_LUXURY" and result.loss > 0 and result.before > 0 and result.after <= 0;
    result.shortage = resource.ResourceClassType ~= "RESOURCECLASS_LUXURY" and result.loss > 0 and result.after < 0;
    return result;
end

function M.Conversion(owner, plot)
    local player = Players[owner];
    if not player or not plot or O.Owner(plot) ~= owner or plot:GetOwner() ~= owner or plot:GetPlotCity() then
        return nil, "TXT_KEY_RO_CONVERT_TERRITORY";
    end
    if plot:IsImprovementPillaged() or O.Blockaded(plot, owner) then return nil, "TXT_KEY_RO_CONVERT_REPAIR"; end
    local resource = GameInfo.Resources[plot:GetResourceType(player:GetTeam())];
    if not resource then return nil, "TXT_KEY_RT_OUTPOST_RESOURCE"; end
    local choices = {};
    for row in GameInfo.Improvement_ResourceTypes { ResourceType = resource.Type } do
        if normal[row.ImprovementType] and (row.ResourceTrade == true or row.ResourceTrade == 1) then
            for build in GameInfo.Builds { ImprovementType = row.ImprovementType } do
                local allowed = hasTech(player, build.PrereqTech);
                for feature in GameInfo.BuildFeatures { BuildType = build.Type } do
                    if I[feature.FeatureType] == plot:GetFeatureType() and not hasTech(player, feature.PrereqTech) then allowed = false; end
                end
                if allowed and plot:CanBuild(build.ID, owner, false, true) then choices[#choices + 1] = build.ID; end
            end
        end
    end
    table.sort(choices);
    return choices[1], choices[1] and "TXT_KEY_RO_CONVERT_HELP" or "TXT_KEY_RO_CONVERT_TECH";
end

function M.Convert(owner, plot)
    local player = Players[owner];
    if owner ~= Game.GetActivePlayer() or not player or not player:IsTurnActive() then return false; end
    local buildID = M.Conversion(owner, plot);
    if not buildID then return false; end
    -- Set the intent before engine callbacks. Completion uses the ordinary
    -- build so feature removal, city resource links and yields stay native.
    local site = O.state.sites[plot:GetPlotIndex()];
    if site then site.converted = true; end
    local work = math.max(1, plot:GetBuildTime(buildID, owner) - plot:GetBuildProgress(buildID));
    plot:ChangeBuildProgress(buildID, work, owner);
    local finished = plot:GetImprovementType() == I[GameInfo.Builds[buildID].ImprovementType];
    if site and not finished then site.converted = nil; end
    O.Reconcile();
    return finished;
end

function M.Defender(plot, owner)
    for n = 0, plot:GetNumUnits() - 1 do
        local u = plot:GetUnit(n);
        if u:GetOwner() == owner and O.IsTroop(u) then return u; end
    end
end
