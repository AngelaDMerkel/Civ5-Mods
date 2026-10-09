-- Optional Resource Outposts integration. Empty LuaEvents requests are harmless
-- when the companion mod is disabled; RT has no dependency on its Lua globals.
RT_OutpostBridge = {};
local X = RT_OutpostBridge;
function X.Shelter(unit)
    local q = { kind = "shelter", owner = unit:GetOwner(), plot = unit:GetPlot():GetPlotIndex() };
    LuaEvents.RO_Query(q);
    return q.value == true;
end
function X.Reserved(unit)
    local q = { kind = "reserved", owner = unit:GetOwner(), unit = unit:GetID() };
    LuaEvents.RO_Query(q);
    return q.value == true;
end
function X.OtherOrder(unit, action)
    local q = { kind = action, owner = unit:GetOwner(), unit = unit:GetID() };
    LuaEvents.RO_Query(q);
    return q.value == true;
end
function X.Initialize()
    LuaEvents.RT_ConstructionQuery.Add(function(q)
        local u = Players[q.owner] and Players[q.owner]:GetUnitByID(q.unit);
        if not u then return; end
        if q.action == "cancel" then RT_ConstructionOrders.Cancel(u);
        elseif q.action == "worked" then q.value = RT_ConstructionOrders.HasWorked(u);
        elseif q.action == "reserved" then q.value = RT_ConstructionOrders.IsOrdered(u); end
    end);
end
