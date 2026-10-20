-- Disposable fixture only. Loaded after the unchanged production UI/runtime.
-- The runner supplies a unique token; nothing happens during ordinary play.
local run, attempted, count, reload = nil, false, 0, false;
LuaEvents.C5M_TerrainProbe.Add(function(token) run = token; end);
LuaEvents.C5M_TerrainReload.Add(function(token) run, reload = token, true; end);
Events.AILeaderMessage.Add(function()
    if run then UI.RequestLeaveLeader(); end
end);
local I, T = GameInfoTypes, RT_Trade;
local function check(value, message)
    assert(value, message);
    count = count + 1;
    print("[C5M_TERRAIN] PASS " .. message);
end
local function tech(owner, name)
    Teams[Players[owner]:GetTeam()]:GetTeamTechs():SetHasTech(I[name], true);
end
local function checks()
    check(Game.GetElapsedGameTurns() == 0 and Game.GetActivePlayer() == 0, "fresh single-player fixture");
    check(not Game.IsGameMultiPlayer(), "single-player mode");
    check(Controls.TradeMarkers and Controls.ConstructionPanel and RT_TradeMarkers, "current production UI initialized");
    check(not Game.C5MGetCoreInfo or not Game.C5MGetCoreInfo().OwnsModSimulation, "Lua owns mod simulation");
    check(not Game.C5MHasCapability or not Game.C5MHasCapability("terrain.native-trade", 1), "unimplemented trade capability remains absent");
    check(T.Used(0) == 0, "fresh trade ledger");
    UI.SetDontShowPopups(true);
    -- Flatten only this disposable new game's test corridor.
    for x = 5, 19 do
        for y = 6, 11 do
            local p = Map.GetPlot(x, y);
            p:SetPlotType(PlotTypes.PLOT_LAND, false, false);
            p:SetTerrainType(I.TERRAIN_GRASS, false, false);
            p:SetFeatureType(-1);
            p:SetResourceType(-1, 0);
            p:SetImprovementType(-1);
            p:SetRouteType(-1);
        end
    end
    local from, to = Players[0]:InitCity(7, 8), Players[1]:InitCity(16, 8);
    check(from and to, "native cities founded");
    for owner = 0, 1 do
        local player = Players[owner];
        local units = {};
        for u in player:Units() do units[#units + 1] = u; end
        for _, u in ipairs(units) do u:Kill(true, -1); end
        player:SetGold(1000);
        for _, name in ipairs({"TECH_POTTERY", "TECH_ANIMAL_HUSBANDRY", "TECH_THE_WHEEL", "TECH_ENGINEERING"}) do tech(owner, name); end
        for x = 5, 19 do
            for y = 6, 11 do Map.GetPlot(x, y):SetRevealed(player:GetTeam(), true); end
        end
    end
    Teams[Players[0]:GetTeam()]:Meet(Players[1]:GetTeam(), true);
    for x = 7, 16 do Map.GetPlot(x, 8):SetRouteType(I.ROUTE_ROAD); end
    check(not T.Quote(from, to, DomainTypes.DOMAIN_LAND, "international").valid, "foreign trade requires an agreement");
    check(T.Offer(0, 1), "agreement accepted by native AI player");
    check(T.HasAgreement(0, 1) and T.HasAgreement(1, 0), "agreement grants reciprocal commercial access");
    local station = Map.GetPlot(11, 8);
    station:SetOwner(-1);
    station:SetImprovementType(I.IMPROVEMENT_RT_RELIEF_STATION);
    RT_Supply.OnBuildFinished(0, 11, 8, I.IMPROVEMENT_RT_RELIEF_STATION);
    check(RT_Supply.Connected(station, 0), "Caravansary connects through actual roads");
    station:SetRouteType(-1);
    check(not RT_Supply.Connected(station, 0), "removing the road breaks the Caravansary connection");
    station:SetRouteType(I.ROUTE_ROAD);
    local quote = T.Quote(from, to, DomainTypes.DOMAIN_LAND, "international");
    check(quote.valid, "connected international route has a native quote");
    check(quote.nativeGold100[0] > 0, "native city trade value is available");

    -- The real production AI must reach Unit:CanBuild and issue native work.
    local road = Map.GetPlot(14, 8);
    road:SetOwner(1, to:GetID()); road:SetRouteType(-1);
    local worker = Players[1]:InitUnit(I.UNIT_WORKER, 14, 8);
    check(worker:CanBuild(road, I.BUILD_ROAD, 0, 1), "native road eligibility accepts integer flags");
    RT_TradeAI.OnTurn(1);
    check(road:GetBuildProgress(I.BUILD_ROAD) > 0 or road:GetRouteType() == I.ROUTE_ROAD
        or worker:GetBuildType() == I.BUILD_ROAD, "trade AI issues a native road build");
    worker:Kill(true, -1); road:SetRouteType(I.ROUTE_ROAD);
    local farm = Map.GetPlot(17, 9);
    farm:SetOwner(1, to:GetID()); farm:SetTerrainType(I.TERRAIN_DESERT, false, false);
    farm:SetImprovementType(I.IMPROVEMENT_RT_DRY_FARM); farm:SetImprovementPillaged(true);
    worker = Players[1]:InitUnit(I.UNIT_WORKER, 17, 9);
    check(worker:CanBuild(farm, I.BUILD_REPAIR, 0, 1), "native repair eligibility accepts integer flags");
    RT_IrrigationAI.OnTurn(1);
    check(farm:GetBuildProgress(I.BUILD_REPAIR) > 0 or not farm:IsImprovementPillaged()
        or worker:GetBuildType() == I.BUILD_REPAIR, "irrigation AI issues a native repair");
    worker:Kill(true, -1);

    check(T.Capacity(0) > 0, "native technology provides trade capacity");
    local caravan = Players[0]:InitUnit(I.UNIT_CARAVAN, 7, 8);
    local launched, reason = T.Launch(caravan, to:Plot():GetPlotIndex(), "international");
    check(launched, "Caravan launches: " .. tostring(reason));
    check(T.Used(0) == 1, "route occupies one slot");
    local route; for _, value in pairs(T.state.routes) do if value.owner == 0 then route = value; end end
    check(route and route.unitType == I.UNIT_CARAVAN, "route retains invested Caravan identity");
    T.Save();
    local saved = RT_Serialize.Decode(Modding.OpenSaveData().GetValue("RealisticTerrain.Trade.v2"));
    check(saved.routes[route.id] and saved.routes[route.id].from == from:Plot():GetPlotIndex(), "native save-data store contains the route");
    local forecast = T.Forecast(0);
    check(forecast.payment100 > 0 and forecast.total100 == forecast.native100 + forecast.payment100, "Accounts combines native GPT and mod income");
    RT_TradeMarkers.Refresh();
    RT_TradeMarkers.Step(route, route.path[1], route.path[2]);
    RT_TradeMarkers.Update(0.3);
    check(RT_TradeMarkers.Visible(route, route.path[1]), "production Caravan marker updates");
    T.Revoke(0, 1);
    check(T.Used(0) == 0, "revocation recalls the route");
    local returned = 0; local idle;
    for u in Players[0]:Units() do
        if u:GetUnitType() == I.UNIT_CARAVAN and not u:IsDelayedDeath() then returned = returned + 1; idle = u; end
    end
    check(returned == 1, "recall returns exactly one Caravan");
    T.ValidateRoutes();
    check(T.Used(0) == 0, "repeat validation leaves recalled route absent");
    check(T.Offer(0, 1), "agreement can be renewed");
    check(T.Launch(idle, to:Plot():GetPlotIndex(), "international"), "renewed route launches for UI review");
    T.OnTurn(0);
    local gold = Players[0]:GetGold();
    T.OnTurn(0);
    check(Players[0]:GetGold() == gold, "duplicate turn cannot pay twice before save");
    local persisted;
    for _, r in pairs(T.state.routes) do if r.owner == 0 then persisted = r; end end
    Modding.OpenSaveData().SetValue("C5M.TerrainProbe.v1", RT_Serialize.Encode({
        route = persisted.id, position = persisted.position, age = persisted.age,
        gold = gold, paid = T.state.paid[0], cash = T.state.cash[0], turn = Game.GetGameTurn()
    }));
    T.OpenRoutes();
    UI.LookAt(station, 0);
    UI.SaveGame("C5M_Terrain_Acceptance");
    print("[C5M_NATIVE] run=" .. run .. " status=PASS scenario=terrain assertions=" .. count);
end
local function reloadChecks()
    check(Controls.TradeMarkers and RT_TradeMarkers, "production UI reloaded");
    check(T.Used(0) == 1, "one active Caravan survives process restart");
    check(T.HasAgreement(0, 1), "trade agreement survives process restart");
    local record = Modding.OpenSaveData().GetValue("C5M.TerrainProbe.v1");
    check(record, "diagnostic saved-state fingerprint restored");
    local expected = RT_Serialize.Decode(record);
    local route = T.state.routes[expected.route];
    check(route and route.unitType == I.UNIT_CARAVAN, "same invested Caravan identity restored");
    check(route.position == expected.position and route.age == expected.age, "route movement and age restored");
    check(Game.GetGameTurn() == expected.turn, "native game turn restored");
    check(Players[0]:GetGold() == expected.gold, "native treasury restored");
    check(T.state.paid[0] == expected.paid and T.state.cash[0] == expected.cash, "payment guard and fractional balance restored");
    check(RT_Supply.Connected(Map.GetPlot(11, 8), 0), "Caravansary builder and road supply restored");
    local gold, position = Players[0]:GetGold(), route.position;
    T.OnTurn(0); T.OnTurn(0);
    check(Players[0]:GetGold() == gold, "reload and duplicate turn cannot pay twice");
    check(route.position == position, "reload and duplicate turn cannot move twice");
    RT_TradeMarkers.Refresh();
    T.OpenRoutes();
    UI.LookAt(Map.GetPlot(11, 8), 0);
    print("[C5M_NATIVE] run=" .. run .. " status=PASS scenario=terrain-reload assertions=" .. count);
end
ContextPtr:SetUpdate(function(delta)
    RT_TradeMarkers.Update(delta);
    if not run then return; end
    for _, name in ipairs({"NaturalWonderPopup", "TechAwardPopup", "NewEraPopup"}) do
        local popup = ContextPtr:LookUpControl("/InGame/" .. name)
            or ContextPtr:LookUpControl("/InGame/BulkUI/" .. name);
        if popup and not popup:IsHidden() then UIManager:DequeuePopup(popup); end
    end
    if attempted or not Players[0]:IsTurnActive() then return; end
    attempted = true;
    local ok, message = pcall(reload and reloadChecks or checks);
    if not ok then print("[C5M_NATIVE] run=" .. run .. " status=FAIL error=" .. tostring(message)); end
end);
