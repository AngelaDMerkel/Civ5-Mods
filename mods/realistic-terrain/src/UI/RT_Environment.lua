-- Exact VFS filenames keep prefix siblings (such as IrrigationAI) unambiguous.
include("RT_Config.lua");
include("RT_Rules.lua");
include("RT_Supply.lua");
include("RT_Irrigation.lua");
include("RT_Construction.lua");
include("RT_OutpostBridge.lua");
include("RT_ConstructionOrders.lua");
include("RT_IrrigationAI.lua");
include("RT_Gameplay.lua");

local G, C = RT_Gameplay, RT_Config;
local cityView = false;
local function text(key, ...) return Locale.ConvertTextKey(key, ...); end

local function refresh()
    local unit = UI.GetHeadSelectedUnit();
    local builder = not cityView and unit and unit:GetOwner() == Game.GetActivePlayer()
        and RT_Construction.IsWorker(unit);
    Controls.ConstructionPanel:SetHide(not builder);
    if builder then
        local allowed, reason = RT_Construction.Status(unit);
        local ordered = RT_ConstructionOrders.IsOrdered(unit, "station");
        Controls.ConstructionButton:SetDisabled(not allowed and not ordered);
        Controls.ConstructionButtonLabel:SetText(text(ordered and "TXT_KEY_RT_BUILD_CANCEL" or "TXT_KEY_RT_BUILD_RELIEF_STATION"));
        local progress, total = RT_Construction.Progress(unit);
        Controls.ConstructionProgress:SetText(text("TXT_KEY_RT_BUILD_PROGRESS", progress, total));
        local help = text(reason) .. "[NEWLINE][NEWLINE]" .. text("TXT_KEY_RT_RELIEF_STATION_HELP");
        Controls.ConstructionPanel:SetToolTipString(help);
        Controls.ConstructionButton:SetToolTipString(help);
        local canIrrigate, irrigationReason = RT_Construction.Status(unit, false, "irrigation");
        local irrigating = RT_ConstructionOrders.IsOrdered(unit, "irrigation");
        Controls.IrrigationButton:SetDisabled(not canIrrigate and not irrigating);
        Controls.IrrigationButtonLabel:SetText(text(irrigating and "TXT_KEY_RT_BUILD_CANCEL" or "TXT_KEY_RT_BUILD_IRRIGATED_FARM"));
        local done, required = RT_Construction.Progress(unit, "irrigation");
        local status = RT_Irrigation.Inspect(unit:GetPlot());
        Controls.IrrigationProgress:SetText(status and text(status) or text("TXT_KEY_RT_BUILD_PROGRESS", done, required));
        Controls.IrrigationButton:SetToolTipString(text(irrigationReason) .. "[NEWLINE][NEWLINE]" .. text("TXT_KEY_RT_IRRIGATED_FARM_HELP"));
        Controls.IrrigationProgress:SetToolTipString(text("TXT_KEY_RT_IRRIGATED_FARM_HELP"));
    end
    local info = unit and unit:GetOwner() == Game.GetActivePlayer() and G.Inspect(unit);
    Controls.ExposurePanel:SetHide(cityView or builder or not info);
    if not info then return; end
    local status = G.StateLabel(info.stage);
    if info.env.home then status = text("TXT_KEY_RT_HOME");
    elseif info.env.paused then status = text("TXT_KEY_RT_EMBARKED");
    elseif info.env.outpostShelter then status = text("TXT_KEY_RT_OUTPOST_SHELTER");
    elseif info.env.relief then status = text("TXT_KEY_RT_RELIEF_CONNECTED");
    elseif info.env.hazard then
        status = text("TXT_KEY_RT_" .. string.upper(info.env.hazard)) .. " / " .. status;
    elseif info.env.water then status = text("TXT_KEY_RT_FRESHWATER");
    else status = text("TXT_KEY_RT_RECOVERING") .. " / " .. status; end
    Controls.ExposureStatus:SetText(status);
    local lines = { unit:GetName(), G.StateLabel(info.stage), "" };
    for _, hazard in ipairs(RT_Rules.HAZARDS) do
        lines[#lines + 1] = text("TXT_KEY_RT_COUNTER", text("TXT_KEY_RT_" .. string.upper(hazard)),
            tostring(info.state[hazard]), tostring(info.grace[hazard]));
    end
    if info.env.reliefNearby then
        lines[#lines + 1] = text(info.env.relief and "TXT_KEY_RT_RELIEF_CONNECTED" or "TXT_KEY_RT_RELIEF_DISCONNECTED");
    end
    if not info.env.home and not info.env.paused then
        lines[#lines + 1] = text("TXT_KEY_RT_NEXT", G.StateLabel(info.nextStage));
        if info.nextStage == 2 then
            lines[#lines + 1] = text("TXT_KEY_RT_DAMAGE", C.DAMAGE_PER_TURN, C.MIN_HP_PERCENT);
        end
    end
    lines[#lines + 1] = "";
    lines[#lines + 1] = text("TXT_KEY_RT_RULES");
    lines[#lines + 1] = "";
    lines[#lines + 1] = text("TXT_KEY_RT_SUPPORT");
    lines[#lines + 1] = "";
    lines[#lines + 1] = text("TXT_KEY_RT_RELIEF_STATION_HELP");
    local tooltip = table.concat(lines, "[NEWLINE]");
    Controls.ExposurePanel:SetToolTipString(tooltip);
    Controls.ExposureTitle:SetToolTipString(tooltip);
    Controls.ExposureStatus:SetToolTipString(tooltip);
end

Controls.ExposurePanel:SetOffsetVal(C.UI_OFFSET_X, C.UI_OFFSET_Y);
Controls.ConstructionPanel:SetOffsetVal(C.UI_OFFSET_X, C.UI_OFFSET_Y);
Controls.ConstructionButton:RegisterCallback(Mouse.eLClick, function()
    RT_ConstructionOrders.Toggle(UI.GetHeadSelectedUnit());
    refresh();
end);
Controls.IrrigationButton:RegisterCallback(Mouse.eLClick, function()
    RT_ConstructionOrders.Toggle(UI.GetHeadSelectedUnit(), "irrigation");
    refresh();
end);
G.OnChanged = refresh;
RT_ConstructionOrders.OnChanged = refresh;
RT_Irrigation.Initialize();
RT_ConstructionOrders.Initialize();
RT_IrrigationAI.Initialize();
G.Initialize();
RT_OutpostBridge.Initialize();
Events.UnitSelectionChanged.Add(refresh);
Events.UnitSelectionCleared.Add(refresh);
Events.SerialEventUnitInfoDirty.Add(refresh);
Events.GameplaySetActivePlayer.Add(refresh);
Events.SerialEventEnterCityScreen.Add(function() cityView = true; refresh(); end);
Events.SerialEventExitCityScreen.Add(function() cityView = false; refresh(); end);
Events.LoadScreenClose.Add(refresh);
Events.ActivePlayerTurnStart.Add(refresh);
GameEvents.CityConstructed.Add(refresh);
refresh();
include("RT_TradeBootstrap.lua");
include("RT_Art.lua");
RT_Art.Initialize();
