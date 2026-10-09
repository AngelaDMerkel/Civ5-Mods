include("RO_Serialize");
include("RO_Integration");
include("RO_Eras");
include("RO_Outposts");
include("RO_Orders");
include("RO_AI");
include("RO_Management");
include("InstanceManager");
local O, Orders, M = RO_Outposts, RO_Orders, RO_Management;
local instances = InstanceManager:new("ROOverviewRow", "Root", Controls.OverviewRows);
local overview, dismissed = false, nil;
local refresh;
local cityView, managing, chosen, confirming = false, false, nil, nil;
local function text(key, ...) return Locale.ConvertTextKey(key, ...); end
local function owned()
    local ids = {};
    for id in pairs(O.state.sites) do
        if O.Owner(Map.GetPlotByIndex(id)) == Game.GetActivePlayer() then ids[#ids + 1] = id; end
    end
    table.sort(ids); return ids;
end
local function target()
    if managing then return chosen and Map.GetPlotByIndex(chosen); end
    local u = UI.GetHeadSelectedUnit(); return u and u:GetPlot();
end
local function consequences(plot)
    local quote = M.Preview(Game.GetActivePlayer(), plot);
    if not quote then return "", ""; end
    local resource = GameInfo.Resources[quote.resource];
    local lines = { text("TXT_KEY_RO_ABANDON_PREVIEW", quote.loss, resource and text(resource.Description) or text("TXT_KEY_RO_NO_RESOURCE"), quote.baseUpkeep) };
    if resource then lines[#lines + 1] = text("TXT_KEY_RO_AVAILABLE_AFTER", quote.before, quote.after); end
    if quote.lastLuxury then lines[#lines + 1] = text("TXT_KEY_RO_LAST_LUXURY"); end
    if quote.shortage then lines[#lines + 1] = text("TXT_KEY_RO_SHORTAGE", -quote.after); end
    if quote.estimated then lines[#lines + 1] = text("TXT_KEY_RO_ESTIMATE"); end
    local signature = table.concat({ plot:GetPlotIndex(), quote.resource, quote.loss, quote.baseUpkeep, quote.before, quote.after }, ":");
    return table.concat(lines, "[NEWLINE]"), signature;
end
local function conversion(plot)
    local build, reason = M.Conversion(Game.GetActivePlayer(), plot);
    if not build then return text(reason), nil; end
    local improvement = GameInfo.Improvements[GameInfo.Builds[build].ImprovementType];
    return text("TXT_KEY_RO_CONVERT_PREVIEW", text(improvement.Description), O.UPKEEP),
        table.concat({ plot:GetPlotIndex(), build, plot:GetFeatureType() }, ":");
end
local function openSite(id)
    chosen, managing, overview, confirming, dismissed = id, true, false, nil, nil; refresh();
end
local function showOverview(ids, owner)
    instances:ResetInstances();
    Controls.OverviewSummary:SetText(text("TXT_KEY_RO_OVERVIEW_SUMMARY", #ids, #ids * O.UPKEEP));
    for _, id in ipairs(ids) do
        local siteID = id;
        local p = Map.GetPlotByIndex(id); local info = O.Inspect(p);
        local row = instances:GetInstance();
        local resource = GameInfo.Resources[p:GetResourceType(Players[owner]:GetTeam())];
        row.Title:SetText(text("TXT_KEY_RO_OVERVIEW_SITE", p:GetX(), p:GetY(), p:GetNumResource(), resource and text(resource.Description) or text("TXT_KEY_RO_NO_RESOURCE")));
        local defender = M.Defender(p, owner);
        local guard = defender and text("TXT_KEY_RO_DEFENDER", defender:GetName(), defender:GetMaxHitPoints() - defender:GetDamage(), defender:GetMaxHitPoints()) or text("TXT_KEY_RO_UNGUARDED");
        local detail = text("TXT_KEY_RO_OVERVIEW_DETAIL", text("TXT_KEY_RO_STATUS_" .. string.upper(info.mode)), guard, O.UPKEEP);
        row.Detail:SetText(detail); row.Root:SetToolTipString(detail);
        row.Locate:RegisterCallback(Mouse.eLClick, function() UI.LookAt(Map.GetPlotByIndex(siteID), 0); end);
        row.SiteManage:RegisterCallback(Mouse.eLClick, function() openSite(siteID); end);
    end
    Controls.OverviewRows:CalculateSize(); Controls.OverviewRows:ReprocessAnchoring(); Controls.OverviewScroll:CalculateInternalSize();
end
refresh = function()
    local u, owner = UI.GetHeadSelectedUnit(), Game.GetActivePlayer();
    local worker = not cityView and u and u:GetOwner() == owner and O.IsWorker(u);
    Controls.ConstructionPanel:SetHide(not worker);
    Controls.ConstructionPanel:SetOffsetVal(0, RO_Integration.Enabled() and 254 or 64);
    if worker then
        local allowed, reason = O.Status(u);
        local ordered = Orders.IsOrdered(u);
        Controls.OutpostButton:SetDisabled(not allowed and not ordered);
        Controls.OutpostButtonLabel:SetText(text(ordered and "TXT_KEY_RO_BUILD_CANCEL" or "TXT_KEY_RT_BUILD_RESOURCE_OUTPOST"));
        local done, total = O.Progress(u);
        Controls.OutpostProgress:SetText(text("TXT_KEY_RO_BUILD_PROGRESS", done, total));
        Controls.OutpostButton:SetToolTipString(text(reason) .. "[NEWLINE]" .. text("TXT_KEY_RT_RESOURCE_OUTPOST_HELP"));
    end
    local ids = owned();
    Controls.OverviewPanel:SetHide(cityView or not overview);
    if overview and not cityView then showOverview(ids, owner); end;
    Controls.Manage:SetHide(cityView);
    Controls.Manage:SetDisabled(#ids == 0);
    if managing and (not chosen or O.Owner(Map.GetPlotByIndex(chosen)) ~= owner) then chosen = ids[1]; confirming = nil; end
    local plot = target(); local info = plot and O.Inspect(plot);
    local visible = not cityView and not overview and info and info.owner >= 0 and (managing or dismissed ~= plot:GetPlotIndex());
    Controls.OutpostPanel:SetHide(not visible);
    if not visible then return; end
    Controls.OutpostStatus:SetText(text("TXT_KEY_RT_OUTPOST_STATUS", Players[info.owner]:GetCivilizationShortDescription(),
        text("TXT_KEY_RO_STATUS_" .. string.upper(info.mode))));
    local resource = plot:GetResourceType(Players[owner]:GetTeam());
    Controls.Deposit:SetText(resource >= 0 and text("TXT_KEY_RT_OUTPOST_DEPOSIT", plot:GetNumResource(), text(GameInfo.Resources[resource].Description)) or "");
    Controls.Upkeep:SetText(text("TXT_KEY_RO_UPKEEP", O.UPKEEP));
    Controls.OutpostPanel:SetToolTipString(text("TXT_KEY_RT_RESOURCE_OUTPOST_HELP") .. "[NEWLINE]" .. text("TXT_KEY_RO_INTEGRATION_HELP"));
    Controls.Abandon:SetDisabled(info.owner ~= owner or not Players[owner]:IsTurnActive());
    local impact, signature = consequences(plot);
    local convertHelp, convertSignature = conversion(plot);
    Controls.AbandonLabel:SetText(text(confirming == "abandon:" .. signature and "TXT_KEY_RO_ABANDON_CONFIRM" or "TXT_KEY_RO_ABANDON"));
    Controls.Impact:SetText(confirming and string.sub(confirming, 1, 8) == "convert:" and convertHelp or impact);
    Controls.Abandon:SetToolTipString(impact);
    Controls.Convert:SetDisabled(not convertSignature or info.owner ~= owner or not Players[owner]:IsTurnActive());
    Controls.Convert:SetToolTipString(convertHelp);
    Controls.ConvertLabel:SetText(text(convertSignature and confirming == "convert:" .. convertSignature and "TXT_KEY_RO_CONVERT_CONFIRM" or "TXT_KEY_RO_CONVERT"));
    Controls.Previous:SetHide(not managing or #ids < 2); Controls.Next:SetHide(not managing or #ids < 2);
end
Controls.OutpostButton:RegisterCallback(Mouse.eLClick, function() Orders.Toggle(UI.GetHeadSelectedUnit()); refresh(); end);
Controls.Manage:RegisterCallback(Mouse.eLClick, function() overview = not overview; confirming = nil; refresh(); end);
Controls.OverviewClose:RegisterCallback(Mouse.eLClick, function() overview = false; refresh(); end);
Controls.Back:RegisterCallback(Mouse.eLClick, function() overview = true; confirming = nil; refresh(); end);
local function cycle(step)
    local ids, index = owned(), 1;
    for n, id in ipairs(ids) do if id == chosen then index = n; end end
    if #ids > 0 then chosen = ids[(index - 1 + step) % #ids + 1]; end
    confirming = nil; refresh();
end
Controls.Previous:RegisterCallback(Mouse.eLClick, function() cycle(-1); end);
Controls.Next:RegisterCallback(Mouse.eLClick, function() cycle(1); end);
Controls.Locate:RegisterCallback(Mouse.eLClick, function() local p = target(); if p then UI.LookAt(p, 0); end end);
local function act(kind)
    local p = target(); local owner = Game.GetActivePlayer();
    if not p or O.Owner(p) ~= owner or not Players[owner]:IsTurnActive() then return; end
    local _, signature;
    if kind == "convert" then _, signature = conversion(p); else _, signature = consequences(p); end
    if not signature then return; end
    local quote = kind .. ":" .. signature;
    if confirming == quote then
        if kind == "convert" then M.Convert(owner, p); else O.Abandon(owner, p); end
        confirming = nil;
        if O.Owner(p) ~= owner then overview = managing; end
    else confirming = quote; end
    refresh();
end
Controls.Abandon:RegisterCallback(Mouse.eLClick, function() act("abandon"); end);
Controls.Convert:RegisterCallback(Mouse.eLClick, function() act("convert"); end);
Controls.Close:RegisterCallback(Mouse.eLClick, function()
    local p = target(); dismissed = p and p:GetPlotIndex(); managing = false; chosen = nil; confirming = nil; refresh();
end);
Orders.OnChanged = refresh;
RO_Integration.Initialize(); Orders.Initialize(); O.Initialize(); RO_AI.Initialize();
Events.UnitSelectionChanged.Add(function() overview = false; managing = false; confirming = nil; dismissed = nil; refresh(); end);
Events.UnitSelectionCleared.Add(refresh);
Events.SerialEventUnitInfoDirty.Add(refresh);
Events.SerialEventGameDataDirty.Add(refresh);
Events.GameplaySetActivePlayer.Add(function() overview = false; managing = false; confirming = nil; dismissed = nil; refresh(); end);
Events.SerialEventEnterCityScreen.Add(function() cityView = true; confirming = nil; refresh(); end);
Events.SerialEventExitCityScreen.Add(function() cityView = false; refresh(); end);
Events.LoadScreenClose.Add(refresh);
Events.ActivePlayerTurnStart.Add(refresh);
refresh();
