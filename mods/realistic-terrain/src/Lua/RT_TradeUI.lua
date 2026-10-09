include("InstanceManager");
local T = RT_Trade;
local instances = InstanceManager:new("RTTradeRow", "Root", Controls.TradeRows);
local open, mode, message = false, "routes", "";
local refresh;
local function gold(value) return string.format("%.2f", (value or 0) / 100); end
local function row(title, detail, action, callback, enabled, locate)
    local r = instances:GetInstance();
    r.Title:SetText(title); r.Detail:SetText(detail); r.Root:SetToolTipString(detail);
    r.ActionLabel:SetText(action or ""); r.Action:SetHide(not action);
    r.Action:SetDisabled(enabled == false);
    if callback then r.Action:RegisterCallback(Mouse.eLClick, callback); end
    r.Locate:SetHide(locate == nil);
    if locate then r.Locate:RegisterCallback(Mouse.eLClick, function() UI.LookAt(locate, 0); end); end
end
local function mayAct()
    local p = Players[Game.GetActivePlayer()]; return p and p:IsTurnActive();
end
local function perform(callback)
    if not mayAct() then return; end
    local _, text = callback(); message = text or "Updated"; refresh();
end
local function agreements(owner)
    local player = Players[owner];
    for other = 0, GameDefines.MAX_CIV_PLAYERS - 1 do
        local p = Players[other]; local target = other;
        if p and other ~= owner and p:IsAlive() and not p:IsBarbarian()
            and Teams[player:GetTeam()]:IsHasMet(p:GetTeam()) then
            local active = T.HasAgreement(owner, other);
            row(p:GetCivilizationShortDescription(), active and "Commercial access is reciprocal. Contributions earn compensation and continuing dividends. Revoking recalls affected routes."
                or "Sign to allow routes and transit. Military Open Borders are separate. AI partners accept during peace without denunciations.",
                active and "Revoke" or "Sign agreement", function()
                    perform(function() if active then T.Revoke(owner, target); return true, "Agreement revoked"; end return T.Offer(owner, target); end);
                end, mayAct() and (active or T.Willing(owner, target)));
        end
    end
end
local function planner(owner)
    local unit = UI.GetHeadSelectedUnit();
    if not T.IsTradeUnit(unit) or unit:GetOwner() ~= owner or not unit:GetPlot():GetPlotCity() then
        row("Select a Caravan, Motorized Caravan or Cargo Ship in your city", "Use this planner to establish routes. Active trade units are tracked here as simulated caravans."); return;
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
                        local detail = quote.reason;
                        if quote.valid then
                            if kind == "international" then
                                local settlement = T.Settlement(quote); local account = settlement.players[owner];
                                local incremental = (account and account.net100 or 0) - (base and base.net100 or 0);
                                local protected = 0;
                                for _, id in ipairs(quote.path) do if quote.context.patrol[id] then protected = protected + 1; end end
                                detail = "Additional net: " .. gold(incremental) .. " gold/turn; efficiency " .. quote.efficiency .. "%"
                                    .. "; " .. (#quote.path - 1) .. " tiles, " .. quote.relays .. " range relays, " .. protected .. " patrolled tiles."
                                    .. (quote.roadPenalty > 0 and " Road continuity missing (-40%)." or "")
                                    .. (quote.reliefPenalty > 0 and " Harsh-terrain relief missing (-40%)." or "")
                                    .. (quote.stationPenalty > 0 and " No supplied Caravansary stop (-40%)." or "")
                                    .. (quote.roadIndependent and " Motorized Caravan: terrain immune; infrastructure deductions affect gold only." or "");
                            else detail = "Domestic " .. kind .. "; cargo efficiency " .. quote.cargoEfficiency .. "%. Uses one trade slot."; end
                        end
                        row(from:GetName() .. " → " .. to:GetName() .. " (" .. kind .. ")", detail,
                            "Establish", function() perform(function()
                                if unit:GetOwner() ~= Game.GetActivePlayer() then return false, "Select your own trade unit"; end
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
        local related = r.owner == owner or r.recipient == owner;
        if related or at:IsVisible(Players[owner]:GetTeam(), false) then
            count = count + 1;
            local from, to, current = Map.GetPlotByIndex(r.from):GetPlotCity(), Map.GetPlotByIndex(r.to):GetPlotCity(), Map.GetPlotByIndex(r.path[r.position]);
            local routeID = id;
            local fromName = from and (related or from:Plot():IsRevealed(Players[owner]:GetTeam(), false)) and from:GetName() or "Unknown origin";
            local toName = to and (related or to:Plot():IsRevealed(Players[owner]:GetTeam(), false)) and to:GetName() or "Unknown destination";
            row((related and "" or "Foreign traffic: ") .. fromName .. " → " .. toName,
                (T.IsRoadIndependent(r.unitType) and "Motorized Caravan; " or "") .. r.kind .. "; position " .. current:GetX() .. "," .. current:GetY() .. "; active " .. r.age .. " turns. Returns after at least " .. r.minimumTurns .. " turns and the current circuit.",
                r.owner == owner and "Recall" or nil, function() perform(function()
                    if T.state.routes[routeID] and T.state.routes[routeID].owner == Game.GetActivePlayer() then T.EndRoute(routeID, "Trade route recalled", false); end
                    return true, "Route recalled";
                end); end, mayAct(), current);
        end
    end
    if count == 0 then row("No active routes", "Select a ready Caravan, Motorized Caravan or Cargo Ship, sign an agreement, and open Plan routes."); end
end
local function accounts(owner)
    local ledger = T.Settlement(); local p = ledger.players[owner];
    if p then
        row("Projected net: " .. gold(p.net100) .. " gold/turn", "Gross payment " .. gold(p.payment100) .. "; allocated infrastructure expenses " .. gold(p.expenses100) .. ". Expenses are charged by the game; compensation is paid by this mod.");
        row("Payment breakdown", "Commerce " .. gold(p.commercial100) .. "; distance " .. gold(p.distance100) .. "; upkeep compensation " .. gold(p.upkeepCompensation100) .. "; permanent infrastructure dividend " .. gold(p.dividend100) .. ".");
    else row("No current trade income", "Infrastructure earns only while an authorized route uses it."); end
    row("Accounting rules", "Shared infrastructure is counted once. Dividends continue for every active turn, with capped growth from extra routes. Garrison upkeep is an empire-average estimate capped at 2 gold per turn for reimbursement.");
    for index = #T.state.history, 1, -1 do
        local h = T.state.history[index]; if h.owner == owner then row("Turn " .. h.turn, h.message); end
    end
end
refresh = function()
    if not open then return; end
    local owner = Game.GetActivePlayer(); if owner < 0 then return; end
    instances:ResetInstances();
    Controls.TradeTitle:SetText("Trade and logistics — " .. T.Used(owner) .. "/" .. T.Capacity(owner) .. " slots");
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
Events.UnitSelectionChanged.Add(refresh);
Events.GameplaySetActivePlayer.Add(function() open = false; Controls.TradePanel:SetHide(true); end);
Events.SerialEventEnterCityScreen.Add(function() open = false; Controls.TradePanel:SetHide(true); Controls.TradeOpen:SetHide(true); end);
Events.SerialEventExitCityScreen.Add(function() Controls.TradeOpen:SetHide(false); end);
T.OnChanged = refresh;
