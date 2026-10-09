-- Presentation only: WorldAnchor markers cannot reveal tiles, occupy a unit
-- stack, be captured by the engine, or bypass the route's garrison/raid rules.
include("InstanceManager");
include("IconSupport");
RT_TradeMarkers = {};
local V, T = RT_TradeMarkers, RT_Trade;
local pool = InstanceManager:new("RTTradeMarker", "Anchor", Controls.TradeMarkers);
local markers = {};
local cityView, strategic = false, InStrategicView();
local STEP_SECONDS = 0.22;

function V.Visible(route, id)
    local active = Game.GetActivePlayer(); local player = Players[active];
    local p = Map.GetPlotByIndex(id);
    return player and p and (route.owner == active or p:IsVisible(player:GetTeam(), false)) or false;
end
local function position(control, id)
    local p = Map.GetPlotByIndex(id);
    local x, y, z = GridToWorld(p:GetX(), p:GetY());
    control:SetWorldPositionVal(x, y, z + 25);
end
local function clear()
    pool:ResetInstances(); markers = {};
end
local function ensure(route, at)
    local marker = markers[route.id];
    if marker then return marker; end
    marker = { ui = pool:GetInstance(), queue = {} }; markers[route.id] = marker;
    local info = GameInfo.Units[route.unitType];
    if info then IconHookup(info.PortraitIndex, 32, info.IconAtlas, marker.ui.Portrait); end
    marker.ui.Select:SetToolTipString(Locale.ConvertTextKey("TXT_KEY_RT_TRADE_MARKER",
        info and Locale.ConvertTextKey(info.Description) or Locale.ConvertTextKey("TXT_KEY_RT_TRADE_TITLE"),
        Players[route.owner]:GetCivilizationShortDescription()));
    local id = route.id;
    marker.ui.Select:RegisterCallback(Mouse.eLClick, function()
        local live = T.state.routes[id];
        if live and V.Visible(live, live.path[live.position]) and T.OpenRoutes then T.OpenRoutes(); end
    end);
    position(marker.ui.Anchor, at);
    return marker;
end
function V.Refresh()
    Controls.TradeMarkers:SetHide(cityView or strategic);
    for id, marker in pairs(markers) do
        if not T.state.routes[id] then pool:ReleaseInstance(marker.ui); markers[id] = nil; end
    end
    for _, route in pairs(T.state.routes) do
        local at = route.path[route.position];
        if V.Visible(route, at) then
            local marker = ensure(route, at);
            marker.ui.Anchor:SetHide(false);
            if #marker.queue == 0 then position(marker.ui.Anchor, at); end
        elseif markers[route.id] then
            markers[route.id].ui.Anchor:SetHide(true); markers[route.id].queue = {};
        end
    end
end
function V.Step(route, from, to)
    if cityView or strategic then return; end
    if not V.Visible(route, from) or not V.Visible(route, to) then
        if markers[route.id] then markers[route.id].queue = {}; end
        return;
    end
    local marker = ensure(route, from);
    if #marker.queue >= 12 then marker.queue = {}; position(marker.ui.Anchor, from); end
    marker.queue[#marker.queue + 1] = { from = from, to = to, elapsed = 0 };
end
function V.Update(delta)
    if cityView or strategic then return; end
    for id, marker in pairs(markers) do
        local route = T.state.routes[id]; local step = marker.queue[1];
        if route and step then
            -- Recheck both ends every frame: a fog event or player change must
            -- never leave a tween exposing the route's next hidden position.
            if V.Visible(route, step.from) and V.Visible(route, step.to)
                and V.Visible(route, route.path[route.position]) then
                local a, b = Map.GetPlotByIndex(step.from), Map.GetPlotByIndex(step.to);
                local x1, y1, z1 = GridToWorld(a:GetX(), a:GetY());
                local x2, y2, z2 = GridToWorld(b:GetX(), b:GetY());
                step.elapsed = math.min(STEP_SECONDS, step.elapsed + math.max(0, delta));
                local f = step.elapsed / STEP_SECONDS;
                -- Wrapped map edges snap instead of sweeping across the world.
                if math.abs(x2 - x1) > 160 or math.abs(y2 - y1) > 160 then f = 1; end
                marker.ui.Anchor:SetWorldPositionVal(x1 + (x2 - x1) * f,
                    y1 + (y2 - y1) * f, z1 + (z2 - z1) * f + 25);
                marker.ui.Anchor:SetHide(false);
                if f == 1 then table.remove(marker.queue, 1); end
            else
                marker.queue = {}; marker.ui.Anchor:SetHide(not V.Visible(route, route.path[route.position]));
                position(marker.ui.Anchor, route.path[route.position]);
            end
        end
    end
end
T.OnRouteStep = V.Step;
T.OnVisualChanged = V.Refresh;
Events.HexFOWStateChanged.Add(V.Refresh);
Events.LoadScreenClose.Add(V.Refresh);
Events.GameplaySetActivePlayer.Add(function() clear(); V.Refresh(); end);
Events.StrategicViewStateChanged.Add(function(value) strategic = value; clear(); V.Refresh(); end);
Events.SerialEventEnterCityScreen.Add(function() cityView = true; clear(); V.Refresh(); end);
Events.SerialEventExitCityScreen.Add(function() cityView = false; V.Refresh(); end);
ContextPtr:SetUpdate(V.Update);
V.Refresh();
