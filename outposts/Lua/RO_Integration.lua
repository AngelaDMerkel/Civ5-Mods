-- Lua globals belong to individual UI contexts. Use synchronous LuaEvents
-- requests for optional services; never include another mod's source files.
RO_Integration = {};
local X = RO_Integration;
X.RT_ID = "d571e16c-bb58-40bf-a81f-a919249e7995";
function X.Enabled()
    for _, mod in pairs(Modding.GetActivatedMods()) do
        if string.lower(mod.ID) == X.RT_ID then return true; end
    end
    return false;
end
function X.OtherOrder(unit, action)
    if not X.Enabled() then return false; end
    local q = { owner = unit:GetOwner(), unit = unit:GetID(), action = action };
    LuaEvents.RT_ConstructionQuery(q);
    return q.value == true;
end
function X.Initialize()
    LuaEvents.RO_Query.Add(function(q)
        local p = q.plot and Map.GetPlotByIndex(q.plot);
        local u = q.unit and Players[q.owner] and Players[q.owner]:GetUnitByID(q.unit);
        if q.kind == "shelter" then
            q.value = X.Enabled() and p ~= nil and RO_Outposts.Owner(p) == q.owner
                and not p:IsImprovementPillaged();
        elseif q.kind == "reserved" then
            q.value = u ~= nil and (RO_AI.Reserved(u) or RO_Orders.IsOrdered(u));
        elseif q.kind == "cancel" and u then RO_Orders.Cancel(u);
        elseif q.kind == "worked" and u then q.value = RO_Orders.HasWorked(u); end
    end);
    LuaEvents.RO_RunAI.Add(function(owner) RO_AI.OnTurn(owner); end);
end
