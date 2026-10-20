-- Disposable scenarios, loaded only after RO_GameplayChecks validates the map.
RO_NativeAdvanced = {};
local N, O, A, I = RO_NativeAdvanced, RO_Outposts, RO_AI, GameInfoTypes;

local function turns(h, observe, limit)
    local last, waited, start = -1, 0, Game.GetGameTurn();
    return function(dt)
        waited = waited + dt;
        if waited < 2 or not Players[0]:IsTurnActive() then return; end
        local turn = Game.GetGameTurn();
        if turn ~= last then
            if observe(turn) then return true; end
            last = turn;
        end
        assert(turn-start < limit, "[ROTEST] FAIL advanced scenario exceeded turn limit");
        h.ready();
        for u in Players[0]:Units() do u:FinishMoves(); end
        Game.DoControl(I.CONTROL_ENDTURN); waited = 0;
    end;
end

function N.recovery(h)
    Game.SetOption(I.GAMEOPTION_NO_BARBARIANS, true);
    Game.SetOption(I.GAMEOPTION_ALWAYS_PEACE, true);
    h.setup(); h.tech(); h.ready();
    local plot = h.deposit(18,6,I.RESOURCE_IRON,3);
    plot:ChangeBuildProgress(O.build, plot:GetBuildTime(O.build,1),1);
    h.equal(O.Owner(plot),1,"recovery fixture has a native AI claim");
    local guard = Players[1]:InitUnit(I.UNIT_WARRIOR,18,6);
    local id, phase, lastDamage = guard:GetID(), "assign", 0;
    local sawHealing, sawFriendly, sawReservation = false, false, false;
    UI.LookAt(plot);
    return turns(h, function(turn)
        guard = Players[1]:GetUnitByID(id);
        h.check(guard ~= nil,"recovering guard remains alive");
        local ai = O.state.ai[1];
        print("[ROTEST] recovery turn=" .. turn .. " phase=" .. phase .. " damage=" .. guard:GetDamage()
              .. " xy=" .. guard:GetX() .. "," .. guard:GetY());
        if phase == "assign" and ai and ai.guards[id] then
            h.check(guard:GetPlot() == plot,"production AI reserves stationed guard");
            guard:SetDamage(60); lastDamage = guard:GetDamage(); phase = "heal";
        elseif phase == "heal" then
            sawReservation = sawReservation or ai and ai.recovering[id] ~= nil;
            sawFriendly = sawFriendly or guard:GetPlot():GetOwner() == 1;
            sawHealing = sawHealing or guard:GetDamage() < lastDamage;
            if ai and ai.recovering[id] then
                h.check(not ai.guards[id],"recovering guard is excluded from active duty");
            elseif sawReservation then
                h.check(sawFriendly,"retreat reaches friendly healing territory");
                h.check(sawHealing,"native turns actually heal the guard");
                h.check(A.DamagePercent(guard) < 25,"recovery releases only above 75 percent health");
                phase = "return";
            end
            lastDamage = guard:GetDamage();
        elseif phase == "return" and ai and ai.guards[id] and guard:GetPlot() == plot then
            h.check(not ai.recovering[id],"healed guard returns to a production guard assignment");
            h.equal(O.Owner(plot),1,"recovery leaves the original claim intact");
            h.equal(Players[1]:GetNumResourceTotal(I.RESOURCE_IRON,false),3,"recovery preserves resource credit");
            h.complete("AI-heal-release-reassign"); return true;
        end
    end,35);
end

function N.threat(h)
    Game.SetOption(I.GAMEOPTION_NO_BARBARIANS, true);
    h.setup(); h.tech(); h.ready(); Teams[0]:DeclareWar(1);
    local plot = h.deposit(16,8,I.RESOURCE_IRON,3);
    local worker = Players[1]:InitUnit(I.UNIT_WORKER,16,7);
    Players[1]:InitUnit(I.UNIT_WORKER,20,3);
    local escort = Players[1]:InitUnit(I.UNIT_SPEARMAN,16,7);
    local enemy = Players[0]:InitUnit(I.UNIT_WARRIOR,15,8);
    local wid, eid = worker:GetID(), escort:GetID();
    h.check(not A.Safe(plot,1),"visible hostile unit makes the destination unsafe");
    h.check(A.Path(worker:GetPlot(),plot,1) == nil,"unescorted planner rejects threatened destination");
    h.check(A.Path(worker:GetPlot(),plot,1,true) ~= nil,"escort route can reach the threatened destination");
    local phase, lostTurn, progress = "escort", nil, 0;
    UI.LookAt(plot);
    return turns(h,function(turn)
        worker = Players[1]:GetUnitByID(wid);
        escort = Players[1]:GetUnitByID(eid);
        h.check(worker ~= nil,"threatened expedition worker remains alive");
        local ai = O.state.ai[1];
        local work = plot:GetBuildProgress(O.build);
        print("[ROTEST] threat turn=" .. turn .. " phase=" .. phase .. " work=" .. work
              .. " worker=" .. worker:GetX() .. "," .. worker:GetY());
        if phase == "escort" and work > 0 then
            h.check(ai.escorts[eid] and ai.escorts[eid].worker == wid,"production AI assigns an escort to the worker");
            h.check(escort and escort:GetPlot() == worker:GetPlot(),"escort and worker stay together on threatened site");
            h.check(A.CanWork(worker),"escorted worker can contribute actual native progress");
            progress, lostTurn, phase = work, turn, "lost";
            escort:Kill(true,-1);
            h.check(not A.CanWork(worker),"escort death immediately removes protection");
        elseif phase == "lost" and turn > lostTurn then
            h.equal(work,progress,"worker cannot build unprotected after escort loss");
            h.check(not ai.escorts[eid],"dead escort reservation is released");
            -- Remove this controlled threat; this is a routing/escort test,
            -- not a claim of combat outcome or tactical balance acceptance.
            enemy:Kill(true,-1); Teams[0]:MakePeace(1);
            h.check(A.Safe(plot,1),"removing visible threat restores a safe destination");
            phase = "resume";
        elseif phase == "resume" and O.IsOutpost(plot) then
            h.equal(O.Owner(plot),1,"AI resumes and completes claim after threat disappears");
            h.equal(Players[1]:GetNumResourceTotal(I.RESOURCE_IRON,false),3,"resumed expedition credits resources once");
            h.equal(O.state.maintenance[1],2,"resumed expedition charges one upkeep entry");
            h.complete("AI-threat-escort-loss-resume"); return true;
        end
    end,25);
end

function N.ui(h)
    Game.SetOption(I.GAMEOPTION_NO_BARBARIANS, true);
    Game.SetOption(I.GAMEOPTION_ALWAYS_PEACE, true);
    local cities = h.setup(); h.tech(); h.ready();
    local plot = h.deposit(8,8,I.RESOURCE_IRON,3);
    local silk = h.deposit(10,8,I.RESOURCE_SILK,1); h.finish(silk);
    local annex = h.deposit(8,10,I.RESOURCE_IRON,4); h.finish(annex);
    annex:SetOwner(0,cities[1]:GetID()); O.Reconcile();
    for x=10,20,2 do local p=h.deposit(x,10,I.RESOURCE_IRON,1); h.finish(p); end
    local worker = Players[0]:InitUnit(I.UNIT_WORKER,8,8);
    local rate, required = worker:WorkRate(true), plot:GetBuildTime(O.build,0);
    local initial = math.max(0,required-2*rate);
    plot:ChangeBuildProgress(O.build,initial,0);
    UI.SelectUnit(worker); UI.LookAt(plot);
    local width,height = UIManager:GetScreenSizeVal();
    print("[ROTEST] ui-ready native-viewport=" .. width .. "x" .. height);
    print("[ROTEST] UI steps: build, cancel, wait one turn, resume; open overview; confirm then cancel abandonment; abandon Silk; convert annexed Iron.");
    local phase, waited, overviewSeen, confirmSeen, cancelSeen = "build",0,false,false,false;
    local silkGone, converted = false,false;
    local beforeHappy = Players[0]:GetHappinessFromResources();
    local beforeIron, beforeUpkeep;
    return function(dt)
        waited=waited+dt;
        if waited<0.5 or not Players[0]:IsTurnActive() then return; end
        waited=0;
        if phase=="build" and RO_Orders.IsOrdered(worker) then
            h.equal(plot:GetBuildProgress(O.build),initial+rate,"mouse build click contributes one native worker step");
            phase="cancel"; print("[ROTEST] ui-await-cancel");
        elseif phase=="cancel" and not RO_Orders.IsOrdered(worker) then
            h.equal(plot:GetBuildProgress(O.build),initial+rate,"mouse cancellation preserves completed progress");
            phase="resume"; h.ready();
            for u in Players[0]:Units() do u:FinishMoves(); end
            Game.DoControl(I.CONTROL_ENDTURN);
            print("[ROTEST] ui-await-resume-after-native-turn");
        elseif phase=="resume" and O.IsOutpost(plot) then
            h.equal(O.Owner(plot),0,"mouse resume completes and claims the resource");
            h.check(not RO_Orders.IsOrdered(worker),"completed UI construction clears its persistent order");
            beforeIron=Players[0]:GetNumResourceTotal(I.RESOURCE_IRON,false);
            beforeUpkeep=Players[0]:GetBuildingGoldMaintenance();
            phase="manage"; print("[ROTEST] ui-await-management");
        elseif phase=="manage" then
            if not overviewSeen and not Controls.OverviewPanel:IsHidden() then
                overviewSeen=true;
                h.check(true,"mouse opens populated nine-site overview");
            end
            if not confirmSeen and Controls.AbandonLabel:GetText()==Locale.ConvertTextKey("TXT_KEY_RO_ABANDON_CONFIRM") then
                h.check(O.IsOutpost(plot) and O.IsOutpost(silk),"first abandonment click only requests confirmation");
                confirmSeen=true;
                print("[ROTEST] ui-await-close-to-cancel");
            end
            if confirmSeen and not cancelSeen and Controls.OutpostPanel:IsHidden() and Controls.OverviewPanel:IsHidden() then
                h.check(O.IsOutpost(plot) and O.IsOutpost(silk),"closing confirmation cancels destructive action");
                cancelSeen=true; print("[ROTEST] ui-await-Silk-abandonment");
            end
            if not silkGone and not O.IsOutpost(silk) then
                h.check(cancelSeen,"cancelled preview precedes explicit Silk abandonment");
                h.equal(Players[0]:GetNumResourceTotal(I.RESOURCE_SILK,false),0,"confirmed UI abandonment removes luxury");
                h.equal(Players[0]:GetHappinessFromResources(),beforeHappy-GameInfo.Resources[I.RESOURCE_SILK].Happiness,
                        "confirmed UI abandonment removes native luxury happiness");
                silkGone=true; print("[ROTEST] ui-await-annexed-Iron-conversion");
            end
            if not converted and not O.IsOutpost(annex) then
                h.equal(annex:GetImprovementType(),I.IMPROVEMENT_MINE,"confirmed UI conversion installs native Mine");
                h.equal(Players[0]:GetNumResourceTotal(I.RESOURCE_IRON,false),beforeIron,"UI conversion preserves native resource quantity");
                converted=true;
            end
            if overviewSeen and cancelSeen and silkGone and converted then
                h.equal(Players[0]:GetBuildingGoldMaintenance(),beforeUpkeep-4,"UI abandonment and conversion release exactly two upkeep entries");
                h.complete("mouse-construction-management"); return true;
            end
        end
    end;
end
