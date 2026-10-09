-- Era selection is derived from the claim owner, never the active player or the
-- world's art era. Internal improvement variants share all gameplay properties.
RO_Eras = {};
local E, I = RO_Eras, GameInfoTypes;
local legacy = I.IMPROVEMENT_RT_RESOURCE_OUTPOST;
local family, stages = { [legacy] = true }, {};
for row in GameInfo.RO_OutpostEras() do
    local improvement, era = I[row.ImprovementType], I[row.EraType];
    if improvement and era then
        family[improvement] = true;
        stages[#stages + 1] = { era = era, improvement = improvement };
    end
end
table.sort(stages, function(a, b) return a.era < b.era; end);

function E.IsType(improvement) return family[improvement] == true; end
function E.IsOutpost(plot) return plot ~= nil and E.IsType(plot:GetImprovementType()); end

function E.Target(owner)
    local player = Players[owner];
    if not player or not player:IsAlive() or player:IsBarbarian() then return; end
    local era, result = player:GetCurrentEra(), stages[1];
    -- For an additional era, retain the latest supported stage not after it.
    for _, stage in ipairs(stages) do
        if stage.era <= era then result = stage; else break; end
    end
    return result and result.improvement;
end

local function legacyOwnedSafe(plot, owner)
    -- Old neutral builds can carry the engine's "gift from major" flag, which
    -- stock Lua cannot read/clear directly. Replacing one after annexation while
    -- its resource is unavailable can remove a native credit that never existed.
    -- Wait for the territorial owner's resource/trade tech before that one-time
    -- legacy migration; new variants are normalized on completion while neutral.
    local player = Players[owner];
    local resource = GameInfo.Resources[plot:GetResourceType(player:GetTeam())];
    return resource and (not resource.TechCityTrade
        or Teams[player:GetTeam()]:GetTeamTechs():HasTech(I[resource.TechCityTrade]));
end

function E.Sync(plot, owner)
    if not E.IsOutpost(plot) then return false; end
    local target = E.Target(owner);
    local old = plot:GetImprovementType();
    if not target or old == target then return false; end
    if old == legacy and plot:GetOwner() >= 0 and not legacyOwnedSafe(plot, owner) then return false; end
    local pillaged, upgrade = plot:IsImprovementPillaged(), plot:GetUpgradeProgress();
    -- Explicit NO_PLAYER prevents setting a new "gift" flag on neutral sites.
    -- The existing claimant is retained in RO_Outposts' ledger.
    plot:SetImprovementType(target, -1);
    plot:SetUpgradeProgress(upgrade);
    if pillaged then
        plot:SetImprovementPillaged(true); -- SetImprovementType clears this flag
    elseif plot:GetOwner() >= 0 then
        -- Stock BNW disconnects the old city resource link AFTER connecting the
        -- new improvement. A balanced native pillage/repair pair reconnects it.
        -- Both variants have identical ResourceTrade rows, so the net credit is
        -- zero. Never compensate from a player's aggregate resource totals.
        plot:SetImprovementPillaged(true);
        plot:SetImprovementPillaged(false);
    end
    return true;
end
