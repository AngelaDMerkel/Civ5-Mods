-- Included only by the disposable fixture copy of RO_UI.lua, after production
-- initialization. Native engine APIs and all production functions stay intact.
if Game.IsGameMultiPlayer() then return; end
local marker = Map.GetPlot(0,0);
if not marker or marker:GetScriptData() ~= "CG2_STATIC_TEST_V1" then return; end
local width, height = Map.GetGridSize();
if width ~= 24 or height ~= 16 or Game.GetActivePlayer() ~= 0 then return; end
if Game.GetElapsedGameTurns() ~= 0 and "__RO_SCENARIO__" ~= "persistence" then return; end
local O, Orders, M, I = RO_Outposts, RO_Orders, RO_Management, GameInfoTypes;
LuaEvents.RO_NativeProbeQuery.Add(function(q) q.loaded = true; end);
local count = 0;
local function check(ok, name, detail)
    assert(ok, "[ROTEST] FAIL " .. name .. " " .. tostring(detail or ""));
    count = count + 1; print("[ROTEST] PASS " .. name);
end
local function equal(actual, expected, name)
    check(actual == expected, name, tostring(actual) .. " expected " .. tostring(expected));
end
local function total(owner, resource) return Players[owner]:GetNumResourceTotal(resource, false); end
local function upkeep(owner) return Players[owner]:GetBuildingGoldMaintenance(); end
local function tech(owner, name)
    Teams[Players[owner]:GetTeam()]:GetTeamTechs():SetHasTech(I[name], true, owner, true, false);
end
local function deposit(x, y, resource, quantity)
    local p = Map.GetPlot(x, y);
    assert(p:GetOwner() == -1 and p:GetImprovementType() == -1, "ROTEST deposit occupied");
    p:SetResourceType(resource, quantity);
    return p;
end
local function finish(plot)
    local worker = Players[0]:InitUnit(I.UNIT_WORKER, plot:GetX(), plot:GetY());
    local required = plot:GetBuildTime(O.build, 0);
    -- Fixture setup leaves exactly one genuine worker contribution to complete.
    plot:ChangeBuildProgress(O.build, math.max(0, required - worker:WorkRate(false)), 0);
    check(Orders.Toggle(worker), "worker order accepted " .. plot:GetPlotIndex());
    check(O.IsOutpost(plot), "native build completed " .. plot:GetPlotIndex());
    check(not Orders.IsOrdered(worker), "completed order cleared " .. plot:GetPlotIndex());
    equal(worker:MovesLeft(), 0, "construction spends movement " .. plot:GetPlotIndex());
    worker:Kill(true, -1);
end
local function setup()
    UI.SetDontShowPopups(true);
    local cities = {Players[0]:InitCity(3, 3), Players[1]:InitCity(20, 3)};
    for owner = 0, 1 do
        local units = {}; for u in Players[owner]:Units() do units[#units + 1] = u; end
        for _, u in ipairs(units) do u:Kill(true, -1); end
        Players[owner]:SetGold(500);
        for i = 0, Map.GetNumPlots() - 1 do
            local p = Map.GetPlotByIndex(i);
            if p:IsGoody() then p:SetImprovementType(-1); end
            p:SetRevealed(Players[owner]:GetTeam(), true);
        end
    end
    return cities;
end
local function technologies()
    for owner = 0, 1 do
        for _, name in ipairs({"TECH_MINING", "TECH_BRONZE_WORKING", "TECH_IRON_WORKING", "TECH_ENGINEERING", "TECH_CALENDAR"}) do tech(owner, name); end
    end
end
local function readyTurns()
    UI.SetDontShowPopups(true);
    -- Informational awards still queue a native turn-timer semaphore in stock
    -- BNW. Close them through the same UI path as their Continue button.
    for _, name in ipairs({"TechAwardPopup", "NewEraPopup", "WhosWinningPopup"}) do
        local popup = ContextPtr:LookUpControl("/InGame/" .. name)
            or ContextPtr:LookUpControl("/InGame/BulkUI/" .. name);
        if popup and not popup:IsHidden() then UIManager:DequeuePopup(popup); end
    end
    local player = Players[0];
    -- Keep unrelated research/production/policy choices from blocking the
    -- bounded automation; worker/AI turns still run through the native engine.
    player:SetJONSCulture(0);
    if player:GetCurrentResearch() < 0 then
        for row in GameInfo.Technologies() do
            if player:CanResearch(row.ID) then player:PushResearch(row.ID, true); break; end
        end
    end
    for c in Players[0]:Cities() do
        if c:GetOrderQueueLength() == 0 then
            Game.CityPushOrder(c, OrderTypes.ORDER_TRAIN, I.UNIT_WARRIOR, false, false, true);
        end
    end
end
local function complete(name)
    print("[ROTEST] native-" .. name .. "-passed assertions=" .. count);
    print("[CG2] scene-ready " .. name .. " checks completed");
end
local function run()
    check(Controls.OutpostButton ~= nil and Controls.Manage ~= nil and Controls.OverviewRows ~= nil,
          "production XML controls loaded");
    check(not RO_Integration.Enabled(), "standalone detection");
    check(next(O.state.sites) == nil, "fresh save ledger");
    local cities = setup();
    local iron = deposit(8, 8, I.RESOURCE_IRON, 3);
    check(not O.CanConstruct(iron, 0), "construction requires technology");
    technologies();
    check(O.CanConstruct(iron, 0), "neutral strategic site eligible");
    local baseIron, baseUpkeep = total(0, I.RESOURCE_IRON), upkeep(0);
    finish(iron);
    equal(iron:GetOwner(), -1, "construction leaves territory neutral");
    equal(O.Owner(iron), 0, "completion records claimant");
    equal(total(0, I.RESOURCE_IRON), baseIron + 3, "strategic stockpile credited");
    equal(upkeep(0), baseUpkeep + 2, "base upkeep charged");
    check(iron:GetRouteType() == -1, "extraction works without a road");
    local guard = Players[0]:InitUnit(I.UNIT_SWORDSMAN, 8, 8);
    equal(M.Defender(iron, 0):GetID(), guard:GetID(), "garrison recognized");
    equal(Players[0]:GetNumResourceAvailable(I.RESOURCE_IRON, true), baseIron + 2, "strategic unit consumes claimed iron");
    local q = {kind="shelter",owner=0,plot=iron:GetPlotIndex()}; LuaEvents.RO_Query(q);
    equal(q.value, false, "shelter absent without Terrain");
    for n = 1, 5 do O.Reconcile(); end
    equal(total(0, I.RESOURCE_IRON), baseIron + 3, "repeat reconciliation does not duplicate resources");
    equal(upkeep(0), baseUpkeep + 2, "repeat reconciliation does not duplicate upkeep");
    iron:SetImprovementPillaged(true); O.Reconcile();
    equal(total(0, I.RESOURCE_IRON), baseIron, "pillage suspends resources");
    equal(upkeep(0), baseUpkeep + 2, "pillage retains upkeep");
    local repair = iron:ChangeBuildProgress(I.BUILD_REPAIR, iron:GetBuildTime(I.BUILD_REPAIR, 0), 0);
    check(repair and not iron:IsImprovementPillaged(), "native repair completes");
    O.Reconcile();
    equal(total(0, I.RESOURCE_IRON), baseIron + 3, "repair restores resources");
    equal(O.Owner(iron), 0, "repair preserves claimant");
    guard:Kill(true, -1);

    local silk = deposit(10, 8, I.RESOURCE_SILK, 1);
    local baseSilk, happy = total(0, I.RESOURCE_SILK), Players[0]:GetHappinessFromResources();
    finish(silk);
    equal(total(0, I.RESOURCE_SILK), baseSilk + 1, "luxury credited");
    equal(Players[0]:GetHappinessFromResources(), happy + GameInfo.Resources[I.RESOURCE_SILK].Happiness,
          "luxury adds native happiness");
    check(M.Preview(0, silk).lastLuxury, "abandon preview warns about last luxury");
    check(O.Abandon(0, silk), "owner can abandon");
    equal(total(0, I.RESOURCE_SILK), baseSilk, "abandon removes luxury");
    equal(Players[0]:GetHappinessFromResources(), happy, "abandon removes luxury happiness");
    equal(upkeep(0), baseUpkeep + 2, "abandon releases upkeep");

    local enemyIron, enemyUpkeep = total(1, I.RESOURCE_IRON), upkeep(1);
    Teams[1]:DeclareWar(0);
    local enemy = Players[1]:InitUnit(I.UNIT_WARRIOR, 9, 8);
    enemy:SetXY(8, 8);
    equal(O.Owner(iron), 1, "native movement event captures neutral outpost");
    equal(total(0, I.RESOURCE_IRON), baseIron, "capture removes former claimant resource");
    equal(total(1, I.RESOURCE_IRON), enemyIron + 3, "capture credits new claimant");
    equal(upkeep(0), baseUpkeep, "capture releases former upkeep");
    equal(upkeep(1), enemyUpkeep + 2, "capture transfers upkeep");
    enemy:Kill(true, -1);
    local own = Players[0]:InitUnit(I.UNIT_WARRIOR, 7, 8); own:SetXY(8, 8);
    equal(O.Owner(iron), 0, "neutral outpost can be recaptured");
    own:Kill(true, -1);
    Teams[1]:MakePeace(0);
    iron:SetOwner(0, cities[1]:GetID()); O.Reconcile();
    equal(O.Owner(iron), 0, "annexed outpost follows territorial owner");
    equal(total(0, I.RESOURCE_IRON), baseIron + 3, "annexation avoids double credit");
    check(M.Convert(0, iron), "annexed site converts through native build");
    equal(iron:GetImprovementType(), I.IMPROVEMENT_MINE, "conversion creates ordinary mine");
    equal(total(0, I.RESOURCE_IRON), baseIron + 3, "conversion retains native resource");
    equal(upkeep(0), baseUpkeep, "conversion releases outpost upkeep");
    check(next(O.state.sites) == nil, "removed and converted sites leave no ledger entries");
    UI.LookAt(iron);
    complete("gameplay");
end
local later;
local function persistence()
    local savedPlot = Map.GetPlot(0, 1);
    local record = savedPlot:GetScriptData();
    if record == "" then
        check(Game.GetElapsedGameTurns() == 0, "save fixture starts in a fresh game");
        setup(); technologies();
        local iron, silk = deposit(8, 8, I.RESOURCE_IRON, 3), deposit(10, 8, I.RESOURCE_SILK, 1);
        finish(iron); finish(silk);
        silk:SetImprovementPillaged(true); O.Reconcile();
        local plot = deposit(8, 10, I.RESOURCE_IRON, 2);
        local worker = Players[0]:InitUnit(I.UNIT_WORKER, 8, 10);
        check(Orders.Toggle(worker), "begin multi-turn construction");
        local progress = plot:GetBuildProgress(O.build);
        check(progress > 0 and not O.IsOutpost(plot), "one worker turn leaves unfinished build");
        local state = {tag="RO_GAMEPLAY_SAVE_V1", worker=worker:GetID(), turn=Game.GetGameTurn(),
                       iron=total(0,I.RESOURCE_IRON), silk=total(0,I.RESOURCE_SILK), upkeep=upkeep(0),
                       progress=progress, work=worker:WorkRate(true)};
        savedPlot:SetScriptData(RO_Serialize.Encode(state));
        readyTurns();
        UI.SelectUnit(worker); UI.LookAt(plot);
        UI.SaveGame("RO_NativeGameplay_Persistence");
        print("[ROTEST] saved fixture for process-restart persistence check");
        complete("save-preparation");
    else
        local state = RO_Serialize.Decode(record);
        check(state.tag == "RO_GAMEPLAY_SAVE_V1", "loaded the diagnostic save");
        local plot, iron, silk = Map.GetPlot(8,10), Map.GetPlot(8,8), Map.GetPlot(10,8);
        local worker = Players[0]:GetUnitByID(state.worker);
        check(worker ~= nil, "worker survives process restart");
        -- Earlier diagnostic saves measured after movement was spent. In the
        -- native API WorkRate(false) is then zero; true gives the full rate.
        if state.work == 0 then state.work = worker:WorkRate(true); end
        check(state.work > 0, "native worker rate available for turn expectation");
        equal(Game.GetGameTurn(), state.turn, "reload retains game turn");
        equal(O.Owner(iron), 0, "reload retains neutral claimant");
        equal(O.Owner(silk), 0, "reload retains pillaged claimant");
        check(silk:IsImprovementPillaged(), "reload retains pillage");
        equal(total(0,I.RESOURCE_IRON), state.iron, "reload does not duplicate resource credit");
        equal(total(0,I.RESOURCE_SILK), state.silk, "reload keeps pillaged luxury disconnected");
        equal(upkeep(0), state.upkeep, "reload does not duplicate upkeep");
        check(Orders.IsOrdered(worker), "reload restores assigned worker order");
        check(Orders.HasWorked(worker), "reload restores same-turn work guard");
        Orders.OnTurn(0); Orders.OnTurn(0);
        equal(plot:GetBuildProgress(O.build), state.progress, "reload cannot repeat same-turn work");
        readyTurns(); UI.SelectUnit(worker); UI.LookAt(plot);
        local last, waited = state.turn, 0;
        later = function(dt)
            waited = waited + dt;
            if not Players[0]:IsTurnActive() or waited < 2 then return; end
            local turn = Game.GetGameTurn();
            if turn > last then
                equal(turn, last + 1, "native turn advances once");
                if O.IsOutpost(plot) then
                    check(not Orders.IsOrdered(worker), "native turn clears completed order");
                    equal(total(0,I.RESOURCE_IRON), state.iron + 2, "multi-turn completion credits once");
                    equal(upkeep(0), state.upkeep + 2, "multi-turn completion charges once");
                    equal(plot:GetImprovementType(), RO_Eras.Target(0), "completion uses current claimant era");
                    print("[ROTEST] real-turn construction completed on turn " .. turn);
                    complete("reload-and-turns"); later = nil; return;
                end
                equal(plot:GetBuildProgress(O.build), state.progress + state.work * (turn-state.turn),
                      "production turn hooks advance construction exactly once");
                check(Orders.HasWorked(worker), "native turn persists work guard");
                last = turn;
            end
            assert(turn-state.turn < 10, "[ROTEST] FAIL construction did not finish within ten turns");
            readyTurns();
            for u in Players[0]:Units() do u:FinishMoves(); end
            print("[ROTEST] request native end turn " .. turn .. " blocker=" .. Players[0]:GetEndTurnBlockingType());
            Game.DoControl(I.CONTROL_ENDTURN);
            waited = 0;
        end;
    end
end
local function ai()
    -- This sequence isolates the planner lifecycle. Random wars/camp spawns are
    -- separate contested-expedition tests, not a deterministic repair fixture.
    Game.SetOption(I.GAMEOPTION_NO_BARBARIANS, true);
    Game.SetOption(I.GAMEOPTION_ALWAYS_PEACE, true);
    setup(); technologies(); readyTurns();
    local plot = deposit(16, 8, I.RESOURCE_IRON, 3);
    local expedition = Players[1]:InitUnit(I.UNIT_WORKER, 16, 7);
    local domestic = Players[1]:InitUnit(I.UNIT_WORKER, 20, 3);
    local guard = Players[1]:InitUnit(I.UNIT_WARRIOR, 17, 8);
    local expeditionID, domesticID, guardID = expedition:GetID(), domestic:GetID(), guard:GetID();
    local before = total(1,I.RESOURCE_IRON);
    local last, waited, phase, phaseTurn = -1, 0, "build", 0;
    local reservedChecked = false;
    GameEvents.PlayerDoTurn.Add(function(owner)
        if owner ~= 1 then return; end
        local roster = O.state.ai[1];
        if roster and next(roster.workers) and not reservedChecked then
            check(roster.workers[expeditionID] ~= nil, "AI reserves nearby expedition worker");
            check(roster.workers[domesticID] == nil, "AI retains a domestic worker");
            reservedChecked = true;
        end
    end);
    UI.LookAt(plot);
    later = function(dt)
        waited = waited + dt;
        if not Players[0]:IsTurnActive() or waited < 2 then return; end
        local turn = Game.GetGameTurn();
        if turn ~= last then
            -- Native unit userdata can dangle after capture/death; resolve IDs
            -- again each turn, just as the production planner does.
            expedition = Players[1]:GetUnitByID(expeditionID);
            guard = Players[1]:GetUnitByID(guardID);
            check(expedition ~= nil and guard ~= nil, "controlled AI fixture units remain alive");
            print("[ROTEST] AI turn=" .. turn .. " phase=" .. phase .. " work=" .. plot:GetBuildProgress(O.build)
                  .. " worker=" .. expedition:GetX() .. "," .. expedition:GetY()
                  .. " guard=" .. guard:GetX() .. "," .. guard:GetY());
            if phase == "build" and O.IsOutpost(plot) then
                check(reservedChecked, "native AI turn hook ran");
                equal(O.Owner(plot), 1, "AI completes and claims its outpost");
                equal(total(1,I.RESOURCE_IRON), before+3, "AI completion credits resources");
                equal(O.state.maintenance[1], 2, "AI completion records one upkeep charge");
                local billed = upkeep(1); O.Reconcile();
                equal(upkeep(1), billed, "AI reconciliation preserves native building maintenance");
                equal(plot:GetOwner(), -1, "AI claim remains neutral territory");
                phase, phaseTurn = "guard", turn;
            elseif phase == "guard" and M.Defender(plot,1) then
                guard = M.Defender(plot,1);
                guardID = guard:GetID();
                check(O.state.ai[1].guards[guard:GetID()] ~= nil, "AI guard reservation reaches site");
                plot:SetImprovementPillaged(true); O.Reconcile();
                equal(total(1,I.RESOURCE_IRON), before, "AI pillage suspends extraction");
                phase, phaseTurn = "repair", turn;
            elseif phase == "repair" and not plot:IsImprovementPillaged() then
                equal(total(1,I.RESOURCE_IRON), before+3, "AI repairs and reconnects resource");
                equal(O.state.maintenance[1], 2, "AI repair keeps one upkeep charge");
                guard:SetDamage(math.floor(guard:GetMaxHitPoints()*0.6));
                phase, phaseTurn = "recover", turn;
            elseif phase == "recover" and O.state.ai[1].recovering[guard:GetID()] then
                check(not O.state.ai[1].guards[guard:GetID()], "wounded guard leaves active reservation");
                check(guard:GetPlot() ~= plot, "wounded AI guard retreats through native movement");
                complete("AI-build-guard-repair-retreat"); later=nil; return;
            end
            last = turn;
        end
        assert(turn-phaseTurn < 12, "[ROTEST] FAIL AI stalled in " .. phase);
        readyTurns();
        for u in Players[0]:Units() do u:FinishMoves(); end
        print("[ROTEST] request native end turn " .. turn .. " blocker=" .. Players[0]:GetEndTurnBlockingType());
        Game.DoControl(I.CONTROL_ENDTURN); waited=0;
    end;
end
local function integration()
    check(RO_Integration.Enabled(), "real activated Terrain UUID enables integration");
    setup(); technologies(); readyTurns();
    for y=7,11 do for x=6,12 do Map.GetPlot(x,y):SetTerrainType(I.TERRAIN_DESERT, false, true); end end
    local plot = deposit(8,8,I.RESOURCE_IRON,3); finish(plot);
    local guard = Players[0]:InitUnit(I.UNIT_WARRIOR,8,8);
    local exposed = Players[0]:InitUnit(I.UNIT_WARRIOR,9,8);
    local function inspect(unit)
        local q = {owner=unit:GetOwner(),unit=unit:GetID()}; LuaEvents.RO_NativeTerrain(q);
        check(q.loaded and q.info ~= nil, "production Terrain context answers native query");
        return q.info;
    end
    local info = inspect(guard);
    check(info.env.outpostShelter and info.env.safe, "own intact outpost supplies Terrain shelter");
    check(not info.env.home and not info.env.relief and plot:GetRouteType() == -1,
          "shelter works without territory road or Caravansary");
    check(not inspect(exposed).env.outpostShelter, "shelter does not extend to adjacent tile");
    local initialIron, initialUpkeep = total(0,I.RESOURCE_IRON), upkeep(0);
    UI.SelectUnit(guard); UI.LookAt(plot);
    local start, last, waited, phase = Game.GetGameTurn(), -1, 0, "exposure";
    later = function(dt)
        waited = waited + dt;
        if not Players[0]:IsTurnActive() or waited < 2 then return; end
        local turn = Game.GetGameTurn();
        if turn ~= last then
            local own, other = inspect(guard), inspect(exposed);
            print("[ROTEST] shelter turn=" .. turn .. " phase=" .. phase .. " own-heat=" .. own.state.heat
                  .. " exposed-heat=" .. other.state.heat .. " exposed-damage=" .. exposed:GetDamage());
            if phase == "exposure" and turn-start >= 5 then
                equal(own.state.heat, 0, "roadless shelter prevents heat accumulation over real turns");
                equal(guard:GetDamage(), 0, "sheltered garrison takes no exposure damage");
                check(other.state.heat > 0 and exposed:GetDamage() > 0, "adjacent unsheltered unit suffers native exposure");
                equal(total(0,I.RESOURCE_IRON), initialIron, "Terrain adds no extraction gate");
                equal(upkeep(0), initialUpkeep, "Terrain adds no outpost upkeep");
                plot:SetImprovementPillaged(true); O.Reconcile();
                check(not inspect(guard).env.outpostShelter, "pillaged outpost loses shelter");
                phase, start = "pillaged", turn;
            elseif phase == "pillaged" and turn-start >= 2 then
                check(own.state.heat > 0, "pillaged garrison begins accumulating heat");
                plot:ChangeBuildProgress(I.BUILD_REPAIR, plot:GetBuildTime(I.BUILD_REPAIR,0),0); O.Reconcile();
                check(inspect(guard).env.outpostShelter, "native repair restores shelter");
                phase, start = "repaired", turn;
            elseif phase == "repaired" and turn-start >= 2 then
                equal(own.state.heat, 0, "repaired shelter restores garrison counters");
                equal(total(0,I.RESOURCE_IRON), initialIron, "repair reconnects independent extraction");
                equal(upkeep(0), initialUpkeep, "repair keeps original upkeep");
                complete("ordinary-mods-and-Terrain-shelter"); later=nil; return;
            end
            last = turn;
        end
        readyTurns();
        for u in Players[0]:Units() do u:FinishMoves(); end
        Game.DoControl(I.CONTROL_ENDTURN); waited=0;
    end;
end
local elapsed, done = 0, false;
ContextPtr:SetUpdate(function(dt)
    if later then
        local ok, err = pcall(later, dt);
        if not ok then print("[ROTEST] FAIL runtime " .. tostring(err)); later = nil; end
        if not later then ContextPtr:ClearUpdate(); end
        return;
    end
    if done then return; end
    elapsed = elapsed + dt;
    if elapsed < 3 or not Players[0]:IsTurnActive() then return; end
    done = true;
    local ok, err = pcall(function()
        if "__RO_SCENARIO__" == "persistence" then persistence();
        elseif "__RO_SCENARIO__" == "ai" then ai();
        elseif "__RO_SCENARIO__" == "integration" then integration(); else run(); end
    end);
    if not ok then print("[ROTEST] FAIL runtime " .. tostring(err)); end
    if not later then ContextPtr:ClearUpdate(); end
end);
