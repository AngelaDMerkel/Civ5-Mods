include("InstanceManager");
local T = RT_Trade;
local instances = InstanceManager:new("RTTradeRow", "Root", Controls.TradeRows);
local open, mode, message = false, "routes", "";
local refresh;
local function text(key, ...) return Locale.ConvertTextKey("TXT_KEY_RT_TRADE_" .. key, ...); end
local function gold(value) return string.format("%.2f", (value or 0) / 100); end
local function row(title, detail, action, callback, enabled, locate)
    local r = instances:GetInstance();
    r.Title:SetText(title); r.Detail:SetText(detail); r.Root:SetToolTipString(detail);
    local titleHeight = r.Title:GetSizeY() or 18;
    r.Detail:SetOffsetVal(8, titleHeight + 12);
    r.Root:SetSizeY(math.max(112, (r.Detail:GetSizeY() or 24) + titleHeight + 24));
    r.ActionLabel:SetText(action or ""); r.Action:SetHide(not action);
    r.Action:SetDisabled(enabled == false);
    if callback then r.Action:RegisterCallback(Mouse.eLClick, callback); end
    r.Locate:SetHide(locate == nil);
    if locate then r.Locate:RegisterCallback(Mouse.eLClick, function()
        if type(locate) == "function" then locate(); else UI.LookAt(locate, 0); end
    end); end
end
local function mayAct()
    local p = Players[Game.GetActivePlayer()]; return p and p:IsTurnActive();
end
local function perform(callback)
    if not mayAct() then return; end
    local _, result = callback(); message = result and Locale.ConvertTextKey(result) or text("UPDATED"); refresh();
end
local function agreements(owner)
    local player = Players[owner];
    for other = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
        local p = Players[other]; local target = other;
        if p and other ~= owner and p:IsAlive() and not p:IsBarbarian()
            and Teams[player:GetTeam()]:IsHasMet(p:GetTeam()) then
            local active = T.HasAgreement(owner, other);
            row(p:GetCivilizationShortDescription(), text(active and "AGREEMENT_ACTIVE" or "AGREEMENT_HELP"),
                text(active and "REVOKE" or "SIGN"), function()
                    perform(function() if active then T.Revoke(owner, target); return true, text("REVOKED"); end return T.Offer(owner, target); end);
                end, mayAct() and (active or T.Willing(owner, target)));
        end
    end
end
local function planner(owner)
    local unit = UI.GetHeadSelectedUnit();
    if not T.IsTradeUnit(unit) or unit:GetOwner() ~= owner or not unit:GetPlot():GetPlotCity() then
        row(text("SELECT_UNIT"), text("SELECT_HELP")); return;
    end
    local from = unit:GetPlot():GetPlotCity();
    local baseline = T.Settlement(); local base = baseline.players[owner];
    for other = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
        local p = Players[other];
        if p and p:IsAlive() and not p:IsBarbarian() and (other == owner or Teams[Players[owner]:GetTeam()]:IsHasMet(p:GetTeam())) then
            for to in p:Cities() do
                if to ~= from and to:Plot():IsRevealed(Players[owner]:GetTeam(), false) then
                    local kinds = other == owner and {"food", "production"} or {"international"};
                    for _, kind in ipairs(kinds) do
                        local destination, cargo = to:Plot():GetPlotIndex(), kind;
                        local quote = T.Quote(from, to, unit:GetDomainType(), kind, nil, nil, unit:GetUnitType());
                        local detail = Locale.ConvertTextKey(quote.reason or "");
                        if quote.valid then
                            if kind == "international" then
                                local settlement = T.Settlement(quote); local account = settlement.players[owner];
                                local incremental = (account and account.net100 or 0) - (base and base.net100 or 0);
                                local protected = 0;
                                for _, id in ipairs(quote.path) do if quote.context.patrol[id] then protected = protected + 1; end end
                                detail = text("QUOTE", gold(incremental), quote.efficiency, #quote.path - 1, quote.relays, protected)
                                    .. (quote.roadPenalty > 0 and text("ROAD_DEDUCTION") or "")
                                    .. (quote.reliefPenalty > 0 and text("RELIEF_DEDUCTION") or "")
                                    .. (quote.stationPenalty > 0 and text("STOP_DEDUCTION") or "")
                                    .. (quote.roadIndependent and text("MOTORIZED_HELP") or "");
                            else detail = text("CARGO", text(string.upper(kind)), quote.cargoEfficiency); end
                        end
                        row(text("DESTINATION", from:GetName(), to:GetName(), text(string.upper(kind))), detail,
                            text("ESTABLISH"), function() perform(function()
                                if unit:GetOwner() ~= Game.GetActivePlayer() then return false, text("OWN_UNIT"); end
                                return T.Launch(unit, destination, cargo);
                            end); end,
                            quote.valid and mayAct() and T.Used(owner) < T.Capacity(owner), to:Plot());
                    end
                end
            end
        end
    end
end
local function activeRoutes(owner)
    local ids = {}; for id in pairs(T.state.routes) do ids[#ids + 1] = id; end; table.sort(ids);
    local count = 0;
    for _, id in ipairs(ids) do
        local r = T.state.routes[id];
        local at = Map.GetPlotByIndex(r.path[r.position]);
        local owned = r.owner == owner;
        if owned or at:IsVisible(Players[owner]:GetTeam(), false) then
            count = count + 1;
            local from, to, current = Map.GetPlotByIndex(r.from):GetPlotCity(), Map.GetPlotByIndex(r.to):GetPlotCity(), Map.GetPlotByIndex(r.path[r.position]);
            local routeID = id;
            local fromName = from and (owned or from:Plot():IsRevealed(Players[owner]:GetTeam(), false)) and from:GetName() or text("UNKNOWN_ORIGIN");
            local toName = to and (owned or to:Plot():IsRevealed(Players[owner]:GetTeam(), false)) and to:GetName() or text("UNKNOWN_DESTINATION");
            local info = GameInfo.Units and GameInfo.Units[r.unitType];
            row(text(owned and "ROUTE_NAME" or "FOREIGN_ROUTE", fromName, toName),
                text("ROUTE_POSITION", info and Locale.ConvertTextKey(info.Description) or text("TITLE"),
                    current:GetX(), current:GetY()) .. (owned and text("RETURN_HELP", r.age, r.minimumTurns) or ""),
                owned and text("RECALL") or nil, function() perform(function()
                    if T.state.routes[routeID] and T.state.routes[routeID].owner == Game.GetActivePlayer() then T.EndRoute(routeID, text("RECALLED"), false); end
                    return true, text("RECALLED");
                end); end, mayAct(), function()
                    local live = T.state.routes[routeID];
                    local p = live and Map.GetPlotByIndex(live.path[live.position]);
                    local player = Players[Game.GetActivePlayer()];
                    if p and player and (live.owner == Game.GetActivePlayer() or p:IsVisible(player:GetTeam(), false)) then UI.LookAt(p, 0); end
                end);
        end
    end
    if count == 0 then row(text("NO_ROUTES"), text("NO_ROUTES_HELP")); end
end
local function accounts(owner)
    local ledger = T.Settlement(); local p = ledger.players[owner];
    if p then
        row(text("NET", gold(p.net100)), text("NET_HELP", gold(p.payment100), gold(p.expenses100)));
        row(text("BREAKDOWN"), text("BREAKDOWN_HELP", gold(p.commercial100), gold(p.distance100), gold(p.upkeepCompensation100), gold(p.dividend100)));
    else row(text("NO_INCOME"), text("NO_INCOME_HELP")); end
    local forecast = T.Forecast(owner, ledger);
    row(text("FORECAST", gold(forecast.total100)), text("FORECAST_HELP", gold(forecast.native100), gold(forecast.payment100)));
    row(text("ACCOUNTING"), text("ACCOUNTING_HELP"));
    row(text("COMPATIBILITY"), text("COMPATIBILITY_HELP"));
    for index = #T.state.history, 1, -1 do
        local h = T.state.history[index]; if h.owner == owner then row(text("HISTORY", h.turn), Locale.ConvertTextKey(h.message)); end
    end
end
refresh = function()
    if not open then return; end
    local owner = Game.GetActivePlayer(); if owner < 0 then return; end
    instances:ResetInstances();
    Controls.TradeTitle:SetText(text("SLOTS", T.Used(owner), T.Capacity(owner)));
    Controls.TradeStatus:SetText(message);
    if mode == "agreements" then agreements(owner);
    elseif mode == "plan" then planner(owner);
    elseif mode == "accounts" then accounts(owner);
    else activeRoutes(owner); end
    Controls.TradeRows:CalculateSize(); Controls.TradeRows:ReprocessAnchoring(); Controls.TradeScroll:CalculateInternalSize();
end;
for _, tab in ipairs({{"TradePlanTab", "plan"}, {"TradeAgreementTab", "agreements"}, {"TradeRoutesTab", "routes"}, {"TradeAccountsTab", "accounts"}}) do
    local target = tab[2]; Controls[tab[1]]:RegisterCallback(Mouse.eLClick, function() mode = target; message = ""; refresh(); end);
end
Controls.TradeOpen:RegisterCallback(Mouse.eLClick, function() open = not open; Controls.TradePanel:SetHide(not open); refresh(); end);
Controls.TradeClose:RegisterCallback(Mouse.eLClick, function() open = false; Controls.TradePanel:SetHide(true); end);
Controls.TradeOpen:SetToolTipString(text("OPEN_HELP"));
Events.UnitSelectionChanged.Add(refresh);
Events.HexFOWStateChanged.Add(refresh);
Events.SerialEventGameDataDirty.Add(refresh);
Events.SerialEventLeagueScreenDirty.Add(refresh);
Events.GameplaySetActivePlayer.Add(function() open = false; Controls.TradePanel:SetHide(true); end);
Events.SerialEventEnterCityScreen.Add(function() open = false; Controls.TradePanel:SetHide(true); Controls.TradeOpen:SetHide(true); end);
Events.SerialEventExitCityScreen.Add(function() Controls.TradeOpen:SetHide(false); end);
T.OnChanged = refresh;
T.OpenRoutes = function() mode = "routes"; open = true; Controls.TradePanel:SetHide(false); refresh(); end;
ContextPtr:SetInputHandler(function(event, key)
    if open and event == KeyEvents.KeyDown and key == Keys.VK_ESCAPE then
        open = false; Controls.TradePanel:SetHide(true); return true;
    end
    return false;
end);
