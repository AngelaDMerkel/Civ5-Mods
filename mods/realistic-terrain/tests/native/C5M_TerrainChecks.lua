-- Disposable fixture only. Loaded after the unchanged production UI/runtime.
-- The runner supplies a unique token; nothing happens during ordinary play.
local run, attempted, count, reload = nil, false, 0, false;
local progress, later = false, nil;
LuaEvents.C5M_TerrainProbe.Add(function(token) run = token; end);
LuaEvents.C5M_TerrainReload.Add(function(token) run, reload = token, true; end);
LuaEvents.C5M_TerrainTurns.Add(function(token) run, reload, progress = token, true, true; end);
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
local function corridor()
    local width, height = Map.GetGridSize();
    for y = 2, height - 4 do
        for x = 2, width - 13 do
            local valid = not Map.GetPlot(x + 10, y + 1):IsWater();
            for dx = 0, 9 do
                if Map.GetPlot(x + dx, y):IsWater() then valid = false; break; end
            end
            if valid then return x, y; end
        end
    end
end
local function checks()
    check(Game.GetElapsedGameTurns() == 0 and Game.GetActivePlayer() == 0, "fresh single-player fixture");
    check(not Game.IsGameMultiPlayer(), "single-player mode");
    check(Controls.TradeMarkers and Controls.ConstructionPanel and RT_TradeMarkers, "current production UI initialized");
    check(not Game.C5MGetCoreInfo or not Game.C5MGetCoreInfo().OwnsModSimulation, "Lua owns mod simulation");
    check(not Game.C5MHasCapability or not Game.C5MHasCapability("terrain.native-trade", 1), "unimplemented trade capability remains absent");
    check(T.Used(0) == 0, "fresh trade ledger");
    UI.SetDontShowPopups(true);
    -- Preserve coastline topology so this save/load test does not also exercise
    -- live terraforming, which is not a production Terrain operation.
    local x, y = corridor();
    check(x ~= nil, "existing land corridor found");
    local function plot(dx, dy) return Map.GetPlot(x + dx, y + (dy or 0)); end
    local prepared = {plot(10, 1)};
    for dx = 0, 9 do prepared[#prepared + 1] = plot(dx); end
    for _, p in ipairs(prepared) do
        assert(not p:IsWater(), "fixture must preserve coastlines");
        p:SetPlotType(PlotTypes.PLOT_LAND, true, true);
        p:SetTerrainType(I.TERRAIN_GRASS, true, true);
        p:SetFeatureType(-1);
        p:SetResourceType(-1, 0);
        p:SetImprovementType(-1);
        p:SetRouteType(-1);
    end
    local from, to = Players[0]:InitCity(x, y), Players[1]:InitCity(x + 9, y);
    check(from and to, "native cities founded");
    for owner = 0, 1 do
        local player = Players[owner];
        local units = {};
        for u in player:Units() do units[#units + 1] = u; end
        for _, u in ipairs(units) do u:Kill(true, -1); end
        player:SetGold(1000);
        for _, name in ipairs({"TECH_POTTERY", "TECH_ANIMAL_HUSBANDRY", "TECH_THE_WHEEL", "TECH_ENGINEERING"}) do tech(owner, name); end
        for dx = -2, 12 do
            for dy = -2, 3 do plot(dx, dy):SetRevealed(player:GetTeam(), true); end
        end
    end
    Teams[Players[0]:GetTeam()]:Meet(Players[1]:GetTeam(), true);
    for dx = 0, 9 do plot(dx):SetRouteType(I.ROUTE_ROAD); end
    check(not T.Quote(from, to, DomainTypes.DOMAIN_LAND, "international").valid, "foreign trade requires an agreement");
    check(T.Offer(0, 1), "agreement accepted by native AI player");
    check(T.HasAgreement(0, 1) and T.HasAgreement(1, 0), "agreement grants reciprocal commercial access");
    local station = plot(4);
    station:SetOwner(-1);
    station:SetImprovementType(I.IMPROVEMENT_RT_RELIEF_STATION);
    RT_Supply.OnBuildFinished(0, station:GetX(), station:GetY(), I.IMPROVEMENT_RT_RELIEF_STATION);
    check(RT_Supply.Connected(station, 0), "Caravansary connects through actual roads");
    station:SetRouteType(-1);
    check(not RT_Supply.Connected(station, 0), "removing the road breaks the Caravansary connection");
    station:SetRouteType(I.ROUTE_ROAD);
    local quote = T.Quote(from, to, DomainTypes.DOMAIN_LAND, "international");
    check(quote.valid, "connected international route has a native quote");
    check(quote.nativeGold100[0] > 0, "native city trade value is available");

    -- The real production AI must reach Unit:CanBuild and issue native work.
    local road = plot(7);
    road:SetOwner(1, to:GetID()); road:SetRouteType(-1);
    local worker = Players[1]:InitUnit(I.UNIT_WORKER, road:GetX(), road:GetY());
    check(worker:CanBuild(road, I.BUILD_ROAD, 0, 1), "native road eligibility accepts integer flags");
    RT_TradeAI.OnTurn(1);
    check(road:GetBuildProgress(I.BUILD_ROAD) > 0 or road:GetRouteType() == I.ROUTE_ROAD
        or worker:GetBuildType() == I.BUILD_ROAD, "trade AI issues a native road build");
    worker:Kill(true, -1); road:SetRouteType(I.ROUTE_ROAD);
    local farm = plot(10, 1);
    farm:SetOwner(1, to:GetID()); farm:SetTerrainType(I.TERRAIN_DESERT, false, false);
    farm:SetImprovementType(I.IMPROVEMENT_RT_DRY_FARM); farm:SetImprovementPillaged(true);
    worker = Players[1]:InitUnit(I.UNIT_WORKER, farm:GetX(), farm:GetY());
    check(worker:CanBuild(farm, I.BUILD_REPAIR, 0, 1), "native repair eligibility accepts integer flags");
    RT_IrrigationAI.OnTurn(1);
    check(farm:GetBuildProgress(I.BUILD_REPAIR) > 0 or not farm:IsImprovementPillaged()
        or worker:GetBuildType() == I.BUILD_REPAIR, "irrigation AI issues a native repair");
    worker:Kill(true, -1);

    check(T.Capacity(0) > 0, "native technology provides trade capacity");
    local caravan = Players[0]:InitUnit(I.UNIT_CARAVAN, x, y);
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
    Modding.OpenSaveData().SetValue("C5M.TerrainProbe.v2", RT_Serialize.Encode({
        route = persisted.id, position = persisted.position, age = persisted.age,
        gold = gold, paid = T.state.paid[0], cash = T.state.cash[0], turn = Game.GetGameTurn(),
        station = station:GetPlotIndex()
    }));
    T.OpenRoutes();
    UI.LookAt(station, 0);
    UI.SaveGame("C5M_Terrain_Acceptance");
    print("[C5M_NATIVE] run=" .. run .. " status=PASS scenario=terrain assertions=" .. count);
end
local function nativeTurns(route)
    local last, start, waited = Game.GetGameTurn(), Game.GetGameTurn(), 0;
    local previousAge, previousPosition = route.age, route.position;
    later = function(delta)
        waited = waited + delta;
        if not Players[0]:IsTurnActive() or waited < 2 then return; end
        local turn = Game.GetGameTurn();
        if turn > last then
            check(turn == last + 1, "native game advances one turn");
            check(T.state.routes[route.id] == route and route.age == previousAge + 1,
                "production turn hook advances the same route once");
            check(route.position ~= previousPosition and route.lastMove == turn,
                "Caravan moves on the native turn");
            check(T.state.processed[0] == turn and T.state.paid[0] == turn,
                "native turn records movement and payment guards");
            local gold, position = Players[0]:GetGold(), route.position;
            T.OnTurn(0); T.OnTurn(0);
            check(Players[0]:GetGold() == gold, "duplicate native turn cannot pay twice");
            check(route.position == position, "duplicate native turn cannot move twice");
            last, previousAge, previousPosition = turn, route.age, route.position;
            if turn - start == 3 then
                T.OpenRoutes();
                print("[C5M_NATIVE] run=" .. run .. " status=PASS scenario=terrain-reload-turns assertions=" .. count);
                later = nil; return;
            end
        end
        -- Resolve unrelated human choices using native commands. The engine
        -- still runs player/AI turns and the production event subscribers.
        UI.SetDontShowPopups(true);
        local player = Players[0];
        player:SetJONSCulture(0);
        if player:GetCurrentResearch() < 0 then
            for row in GameInfo.Technologies() do
                if player:CanResearch(row.ID) then player:PushResearch(row.ID, true); break; end
            end
        end
        for city in player:Cities() do
            if city:GetOrderQueueLength() == 0 then
                Game.CityPushOrder(city, OrderTypes.ORDER_TRAIN, I.UNIT_WARRIOR, false, false, true);
            end
        end
        for unit in player:Units() do unit:FinishMoves(); end
        print("[C5M_TERRAIN] request native end turn " .. turn .. " blocker=" .. player:GetEndTurnBlockingType());
        Game.DoControl(I.CONTROL_ENDTURN);
        waited = 0;
    end;
end
local function reloadChecks()
    check(Controls.TradeMarkers and RT_TradeMarkers, "production UI reloaded");
    check(T.Used(0) == 1, "one active Caravan survives process restart");
    check(T.HasAgreement(0, 1), "trade agreement survives process restart");
    local record = Modding.OpenSaveData().GetValue("C5M.TerrainProbe.v2");
    check(record, "diagnostic saved-state fingerprint restored");
    local expected = RT_Serialize.Decode(record);
    local route = T.state.routes[expected.route];
    check(route and route.unitType == I.UNIT_CARAVAN, "same invested Caravan identity restored");
    check(route.position == expected.position and route.age == expected.age, "route movement and age restored");
    check(Game.GetGameTurn() == expected.turn, "native game turn restored");
    check(Players[0]:GetGold() == expected.gold, "native treasury restored");
    check(T.state.paid[0] == expected.paid and T.state.cash[0] == expected.cash, "payment guard and fractional balance restored");
    local station = Map.GetPlotByIndex(expected.station);
    check(RT_Supply.Connected(station, 0), "Caravansary builder and road supply restored");
    local gold, position = Players[0]:GetGold(), route.position;
    T.OnTurn(0); T.OnTurn(0);
    check(Players[0]:GetGold() == gold, "reload and duplicate turn cannot pay twice");
    check(route.position == position, "reload and duplicate turn cannot move twice");
    RT_TradeMarkers.Refresh();
    T.OpenRoutes();
    UI.LookAt(station, 0);
    if progress then nativeTurns(route);
    else print("[C5M_NATIVE] run=" .. run .. " status=PASS scenario=terrain-reload assertions=" .. count); end
end
ContextPtr:SetUpdate(function(delta)
    RT_TradeMarkers.Update(delta);
    if not run then return; end
    for _, name in ipairs({"NaturalWonderPopup", "TechAwardPopup", "NewEraPopup", "WhosWinningPopup"}) do
        local popup = ContextPtr:LookUpControl("/InGame/" .. name)
            or ContextPtr:LookUpControl("/InGame/BulkUI/" .. name);
        if popup and not popup:IsHidden() then UIManager:DequeuePopup(popup); end
    end
    if later then
        local ok, message = pcall(later, delta);
        if not ok then
            later = nil;
            print("[C5M_NATIVE] run=" .. run .. " status=FAIL error=" .. tostring(message));
        end
        return;
    end
    if attempted or not Players[0]:IsTurnActive() then return; end
    attempted = true;
    local ok, message = pcall(reload and reloadChecks or checks);
    if not ok then print("[C5M_NATIVE] run=" .. run .. " status=FAIL error=" .. tostring(message)); end
end);
