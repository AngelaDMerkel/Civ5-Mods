-- Run real network, construction, saved orders and AI through a Civ V API boundary.
local count = 0;
local function eq(a, b, label)
    count = count + 1; assert(a == b, label .. ': ' .. tostring(a) .. ' ~= ' .. tostring(b));
end
local function eventBus()
    return setmetatable({}, { __index = function(t, k)
        local callbacks = {};
        local e = { Add = function(f) callbacks[#callbacks + 1] = f; end,
            Fire = function(...) for _, f in ipairs(callbacks) do f(...); end end };
        setmetatable(e, { __call = function(_, ...) e.Fire(...); end }); rawset(t, k, e); return e;
    end });
end
GameEvents, Events, LuaEvents = eventBus(), eventBus(), eventBus();
GameInfoTypes = {};
for i, name in ipairs({ 'IMPROVEMENT_RT_IRRIGATED_FARM', 'IMPROVEMENT_RT_DRY_FARM',
    'BUILDING_RT_IRRIGATION_WORKS', 'BUILDINGCLASS_RT_IRRIGATION_WORKS', 'TERRAIN_DESERT',
    'TERRAIN_GRASS', 'FEATURE_OASIS', 'FEATURE_FLOOD_PLAINS', 'RESOURCE_WHEAT', 'RESOURCE_IRON',
    'IMPROVEMENT_FARM', 'BUILD_RT_IRRIGATED_FARM', 'BUILD_RT_RELIEF_STATION',
    'BUILDING_CARAVANSARY', 'TECH_ENGINEERING', 'UNIT_WORKER', 'BUILD_REPAIR' }) do GameInfoTypes[name] = i; end
local I = GameInfoTypes;
local values, turn = {}, 1;
Modding = { OpenSaveData = function() return {
    GetValue = function(_, k) return values[k]; end, SetValue = function(_, k, v) values[k] = v; end }; end };
Game = { GetGameTurn = function() return turn; end, GetActivePlayer = function() return 0; end };
DomainTypes = { DOMAIN_LAND = 0 }; MissionTypes = { MISSION_MOVE_TO = 1, MISSION_BUILD = 2 };
OrderTypes = { ORDER_CONSTRUCT = 1 };
GameInfo = { Builds = {
    [I.BUILD_RT_IRRIGATED_FARM] = { Type = 'BUILD_RT_IRRIGATED_FARM', PrereqTech = 'TECH_ENGINEERING' },
    [I.BUILD_RT_RELIEF_STATION] = { Type = 'BUILD_RT_RELIEF_STATION', PrereqTech = 'TECH_ENGINEERING' },
}, Unit_Builds = function() local done = false; return function()
    if not done then done = true; return { UnitType = 'UNIT_WORKER' }; end; end; end,
BuildFeatures = function() return function() return nil; end; end };
Teams, Players = {}, {};
for id = 0, 1 do
    local team = { engineering = true, war = false };
    function team:GetTeamTechs() return { HasTech = function() return self.engineering; end }; end
    function team:IsAtWar(other) return self.war and other ~= id; end
    Teams[id] = team;
    local player = { id = id, units = {}, cities = {}, human = id == 0, making = 0, rate = 5, gold = 100 };
    function player:GetTeam() return id; end
    function player:IsTurnActive() return true; end
    function player:IsAlive() return true; end
    function player:IsHuman() return self.human; end
    function player:IsBarbarian() return false; end
    function player:CountNumBuildings() return 0; end -- no Ministry: irrigation must still work
    function player:GetUnitByID(i) return self.units[i]; end
    function player:Units() local key; return function() key = next(self.units, key); return self.units[key]; end; end
    function player:Cities() local n = 0; return function() n = n + 1; return self.cities[n]; end; end
    function player:GetBuildingClassMaking() return self.making; end
    function player:CalculateGoldRate() return self.rate; end
    function player:GetGold() return self.gold; end
    Players[id] = player;
end
local plots, coords = {}, {};
local dirs = { {1,0}, {0,1}, {-1,1}, {-1,0}, {0,-1}, {1,-1} };
Map = { GetNumPlots = function() return #plots; end, GetPlotByIndex = function(i) return plots[i + 1]; end,
    PlotDirection = function(x,y,d) local v = dirs[d+1]; return coords[(x+v[1])..','..(y+v[2])]; end,
    PlotDistance = function(x,y,a,b) return math.max(math.abs(x-a),math.abs(y-b),math.abs(x+y-a-b)); end };
local function plot(x,y)
    local p = { x=x,y=y,id=#plots,owner=0,terrain=I.TERRAIN_DESERT,feature=-1,resource=-1,
        improvement=-1,units={},progress=0,total=300 };
    plots[#plots+1]=p; coords[x..','..y]=p;
    function p:GetPlotIndex() return self.id; end
    function p:GetX() return self.x; end; function p:GetY() return self.y; end
    function p:GetOwner() return self.owner; end
    function p:GetTerrainType() return self.terrain; end
    function p:GetFeatureType() return self.feature; end
    function p:GetResourceType() return self.resource; end
    function p:IsWater() return self.water or self.lake or false; end
    function p:IsMountain() return self.mountain or false; end
    function p:IsHills() return self.hills or false; end
    function p:IsRiver() return self.river or false; end
    function p:IsLake() return self.lake or false; end
    function p:IsImpassable() return self.impassable or false; end
    function p:IsRevealed() return not self.hidden; end
    function p:IsVisible() return not self.hidden; end
    function p:GetPlotCity() return self.city; end
    function p:GetWorkingCity() return self.workingCity; end
    function p:GetImprovementType() return self.improvement; end
    function p:IsImprovementPillaged() return self.pillaged or false; end
    function p:SetImprovementType(i, owner)
        self.improvement = i; self.pillaged = false; -- emulate the real engine's repair side effect
        self.switches = (self.switches or 0) + 1;
        if self.reenter then RT_Irrigation.Refresh(); end
    end
    function p:GetNumUnits() return #self.units; end
    function p:GetUnit(i) return self.units[i+1]; end
    function p:GetBuildType() return -1; end
    function p:CanBuild() return not self.invalid; end
    function p:GetBuildTime() return self.total; end
    function p:GetBuildProgress() return self.progress; end
    function p:ChangeBuildProgress(action, rate, owner)
        assert(action == I.BUILD_RT_IRRIGATED_FARM); self.progress = self.progress + rate;
        if self.progress >= self.total then self.improvement=I.IMPROVEMENT_RT_DRY_FARM; self.progress=0; return true; end
        return false;
    end
    return p;
end
local mountain, a, b, c = plot(0,0), plot(1,0), plot(2,0), plot(3,0);
mountain.mountain = true;
for _,p in ipairs({a,b,c}) do p.improvement=I.IMPROVEMENT_RT_DRY_FARM; end
local city = { works = 1, owner = 0, id = 1 };
function city:GetOwner() return self.owner; end
function city:GetID() return self.id; end
function city:GetNumBuilding(i) assert(i==I.BUILDING_RT_IRRIGATION_WORKS); return self.works; end
function city:CanConstruct() return self.works==0; end
function city:PushOrder(order, item, data, save, pop, append)
    assert(order==OrderTypes.ORDER_CONSTRUCT and item==I.BUILDING_RT_IRRIGATION_WORKS and append and not pop);
    self.queued=(self.queued or 0)+1; Players[self.owner].making=1;
end
Players[0].cities={city}; a.workingCity=city; b.workingCity=city; c.workingCity=city;
dofile(TEST_ROOT..'/mod/Lua/RT_Irrigation.lua'); local F=RT_Irrigation;
F.Initialize();
eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'chain fills from mountain');
eq(F.Connected(c,0),true,'live connection follows chain');
a.pillaged=true;
eq(F.Connected(c,0),false,'live query rejects pillaged upstream before refresh');
Events.AIProcessingEndedForPlayer.Fire(1);
eq(c.improvement,I.IMPROVEMENT_RT_DRY_FARM,'enemy end turn dries downstream before next food processing');
eq(a.pillaged,true,'refresh never repairs pillaged root');
a.pillaged=false; GameEvents.BuildFinished.Fire();
eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'repair reactivates whole chain');
b.improvement=I.IMPROVEMENT_FARM; Events.ActivePlayerTurnEnd.Fire();
eq(c.improvement,I.IMPROVEMENT_RT_DRY_FARM,'ordinary farm breaks channel');
b.improvement=I.IMPROVEMENT_RT_DRY_FARM; b.owner=1; F.Refresh();
eq(c.improvement,I.IMPROVEMENT_RT_DRY_FARM,'foreign irrigation cannot carry water');
b.owner=0; F.Refresh();
eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'recapture restores chain');
-- A second source supports the far side of a broken connection.
c.river=true; b.pillaged=true; F.Refresh();
eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'alternate river source survives severance');
c.river=false; b.pillaged=false;
local alternate = plot(2,1); alternate.improvement=I.IMPROVEMENT_RT_DRY_FARM; alternate.river=true;
b.pillaged=true; F.Refresh();
eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'alternate connected branch survives pillage');
alternate.river=false; b.pillaged=false; mountain.mountain=false;
F.Refresh(); eq(c.improvement,I.IMPROVEMENT_RT_DRY_FARM,'closed farm loop cannot create water');
mountain.water=true; F.Refresh(); eq(a.improvement,I.IMPROVEMENT_RT_DRY_FARM,'coast is not freshwater');
mountain.lake=true; F.Refresh(); eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'lake supplies network');
mountain.lake=false; mountain.water=false; mountain.feature=I.FEATURE_OASIS; F.Refresh();
eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'oasis supplies network');
mountain.feature=-1; mountain.mountain=true;
a.owner=-1; F.Refresh(); eq(c.improvement,I.IMPROVEMENT_RT_DRY_FARM,'unowned node breaks connection');
a.owner=0; a.reenter=true; F.Refresh(); eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'reentrant refresh guarded');
local switches=c.switches; F.Refresh(); eq(c.switches,switches,'duplicate refresh makes no native mutations');
dofile(TEST_ROOT..'/mod/Lua/RT_Irrigation.lua'); F=RT_Irrigation; F.Refresh();
eq(c.switches,switches,'reload preserves correct native state without stacking');
city.works=0; F.Refresh(); eq(c.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'existing farms survive building sale'); city.works=1;
-- Flat desert, wheat/floodplain validity, local rather than empire building gate.
local site=plot(4,0); site.workingCity=city;
eq(F.BuildStatus(site,0),true,'extension permitted');
city.works=0; local ok,reason=F.BuildStatus(site,0);
eq(ok,false,'local works required'); eq(reason,'TXT_KEY_RT_IRRIGATION_BUILDING','local building explanation'); city.works=1;
site.hills=true; eq(F.BuildStatus(site,0),false,'hills rejected'); site.hills=false;
site.owner=1; eq(F.BuildStatus(site,0),false,'foreign land rejected'); site.owner=0;
site.resource=I.RESOURCE_IRON; eq(F.BuildStatus(site,0),false,'other visible resource protected');
site.resource=I.RESOURCE_WHEAT; eq(F.BuildStatus(site,0),true,'wheat permitted'); site.resource=-1;
site.feature=I.FEATURE_OASIS; eq(F.BuildStatus(site,0),false,'oasis cannot be destroyed');
site.feature=I.FEATURE_FLOOD_PLAINS; eq(F.BuildStatus(site,0),true,'floodplains permitted'); site.feature=-1;
site.terrain=I.TERRAIN_GRASS; eq(F.BuildStatus(site,0),false,'non desert rejected'); site.terrain=I.TERRAIN_DESERT;
site.improvement=1234; eq(F.BuildStatus(site,0),false,'special improvement protected');
site.improvement=I.IMPROVEMENT_FARM; eq(F.BuildStatus(site,0),true,'existing farm can be upgraded');
-- Worker orders, suspended supply, reload and cross-order work guard.
local worker={id=1,owner=0,plot=site,moves=120,rate=100}; Players[0].units[1]=worker;
function worker:GetID() return self.id; end
function worker:GetOwner() return self.owner; end
function worker:GetTeam() return self.owner; end
function worker:GetUnitType() return I.UNIT_WORKER; end
function worker:GetDomainType() return DomainTypes.DOMAIN_LAND; end
function worker:GetGameTurnCreated() return self.birth or 0; end
function worker:GetOriginalOwner() return 0; end
function worker:IsDelayedDeath() return self.dead or false; end
function worker:IsEmbarked() return self.embarked or false; end
function worker:IsAutomated() return self.automated or false; end
function worker:IsBusy() return false; end
function worker:GetBuildType() return self.build or -1; end
function worker:IsCombatUnit() return false; end
function worker:GetPlot() return self.plot; end
function worker:GetMoves() return self.moves; end
function worker:WorkRate() return self.moves>0 and self.rate or 0; end
function worker:FinishMoves() self.moves=0; end
function worker:CanMoveThrough() return true; end
function worker:CanBuild() return true; end
function worker:PushMission(kind, x, y)
    self.mission={kind,x,y}; if kind==MissionTypes.MISSION_BUILD then self:FinishMoves(); end
end
site.units={worker};
RT_Supply={OnBuildFinished=function() error('irrigation must not record a station'); end};
local otherWorked, reserved = false,false;
RT_OutpostBridge={ OtherOrder=function(_,action) return action=='worked' and otherWorked; end,
    Reserved=function() return reserved; end };
dofile(TEST_ROOT..'/mod/Lua/RT_Construction.lua'); local B=RT_Construction;
dofile(TEST_ROOT..'/mod/Lua/RT_ConstructionOrders.lua'); local O=RT_ConstructionOrders;
eq(O.Start(worker,'irrigation'),true,'custom order needs no Ministry');
eq(site.progress,100,'one worker turn'); eq(worker.moves,0,'movement consumed');
turn=2; worker.moves=120; a.pillaged=true; O.OnTurn(0);
eq(site.progress,100,'source loss pauses ongoing construction'); eq(O.IsOrdered(worker,'irrigation'),true,'paused order retained');
dofile(TEST_ROOT..'/mod/Lua/RT_ConstructionOrders.lua'); O=RT_ConstructionOrders;
eq(O.IsOrdered(worker,'irrigation'),true,'irrigation kind survives save reload');
a.pillaged=false; O.OnTurn(0); eq(site.progress,200,'repair resumes order');
worker.moves=120; O.OnTurn(0); eq(site.progress,200,'duplicate turn cannot double work');
eq(O.Start(worker,'station'),false,'shared guard/gate blocks other construction');
turn=3; worker.moves=120; city.works=0; O.OnTurn(0); eq(site.progress,200,'building sale pauses work');
city.works=1; O.OnTurn(0);
eq(site.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'completion activates native wet improvement');
eq(O.IsOrdered(worker),false,'completion removes assignment');
site.improvement=I.IMPROVEMENT_FARM; turn=4; worker.moves=120; otherWorked=true;
eq(O.Start(worker,'irrigation'),false,'companion worker stamp prevents extra work'); otherWorked=false;
O.Start(worker,'irrigation'); worker.plot=c; O.OnMoved(0,1); worker.plot=site;
eq(O.IsOrdered(worker),false,'moving cancels order');
turn=5; worker.moves=120; O.Start(worker,'irrigation'); worker.automated=true; O.OnTurn(0);
eq(O.IsOrdered(worker),false,'native automation replaces custom order'); worker.automated=false;
turn=6; worker.moves=120; site.progress=0; O.Start(worker,'irrigation'); worker.birth=1; O.OnTurn(0);
eq(O.IsOrdered(worker),false,'reused unit identity cannot inherit irrigation job');
-- AI uses paid buildings, legal worker orders and prioritizes repairs safely.
dofile(TEST_ROOT..'/mod/Lua/RT_IrrigationAI.lua'); local AI=RT_IrrigationAI;
Players[0].human=false; turn=10; worker.moves=120; site.progress=0;
AI.OnTurn(0); eq(O.IsOrdered(worker,'irrigation'),true,'AI starts real persistent construction');
local progress=site.progress; worker.moves=120; AI.OnTurn(0); eq(site.progress,progress,'AI duplicate event guarded');
O.Cancel(worker); turn=11; site.improvement=I.IMPROVEMENT_RT_IRRIGATED_FARM; site.pillaged=true;
worker.moves=120; AI.OnTurn(0); eq(worker.mission[1],MissionTypes.MISSION_BUILD,'AI repairs instead of rebuilding');
eq(worker.mission[2],I.BUILD_REPAIR,'native repair action');
worker.mission=nil; reserved=true; turn=12; worker.moves=120; AI.OnTurn(0);
eq(worker.mission,nil,'outpost worker reservations respected'); reserved=false;
Teams[0].war=true;
site.units={worker,{IsCombatUnit=function() return true; end,GetTeam=function() return 1; end}};
turn=13; worker.moves=120; AI.OnTurn(0); eq(worker.mission,nil,'AI avoids visible enemy');
site.units={worker}; Teams[0].war=false; site.pillaged=false;
worker.plot=mountain; mountain.mountain=false; mountain.terrain=I.TERRAIN_GRASS;
mountain.river=true; a.river=true; b.improvement=I.IMPROVEMENT_FARM; c.improvement=I.IMPROVEMENT_FARM;
city.works=0; turn=14; worker.moves=120; AI.OnTurn(0);
eq(city.queued,1,'AI commissions useful Irrigation Works through city production');
turn=15; AI.OnTurn(0); eq(city.queued,1,'queued building not duplicated');
city.works=1; c.improvement=I.IMPROVEMENT_RT_DRY_FARM; b.workingCity=city;
turn=16; worker.moves=120; AI.OnTurn(0);
eq(worker.mission[1],MissionTypes.MISSION_MOVE_TO,'AI moves toward reachable construction');
eq(worker.moves,0,'movement reserves worker from same-turn trade logistics');
a.owner=1; eq(AI.Path(mountain,b,0),nil,'AI path cannot cross foreign land'); a.owner=0;
a.hidden=true; eq(AI.Path(mountain,b,0),nil,'AI path cannot use unrevealed land'); a.hidden=false;
a.water=true; eq(AI.Path(mountain,b,0),nil,'AI path cannot embark');
-- Captured city assignments and disconnected build starts must revalidate live data.
worker.plot=site; site.improvement=I.IMPROVEMENT_FARM; site.pillaged=false;
site.progress=0; worker.moves=120; turn=20; a.water=false;
city.owner=1; eq(B.Work(worker,false,'irrigation'),false,'captured assigned city blocks construction');
city.owner=0; Teams[0].engineering=false;
eq(B.Work(worker,false,'irrigation'),false,'Engineering gate enforced on work'); Teams[0].engineering=true;
a.river=false; mountain.river=false; mountain.mountain=false; alternate.river=false;
F.Refresh(); eq(B.Work(worker,false,'irrigation'),false,'disconnected wet-state remnants cannot start construction');
eq(site.progress,0,'denied construction cannot grant work');
-- Long networks use an iterative traversal, with no arbitrary chain-length cap.
local root=plot(100,0); root.mountain=true;
local endPlot;
for x=101,600 do endPlot=plot(x,0); endPlot.improvement=I.IMPROVEMENT_RT_DRY_FARM; end
F.Refresh(); eq(endPlot.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'500-farm chain supplied');
coords['350,0'].pillaged=true; Events.AIProcessingStartedForPlayer.Fire(0);
eq(endPlot.improvement,I.IMPROVEMENT_RT_DRY_FARM,'long downstream chain dries at turn start boundary');
coords['350,0'].pillaged=false; F.Refresh(); eq(endPlot.improvement,I.IMPROVEMENT_RT_IRRIGATED_FARM,'long chain repairs without stack recursion');
print('Connected irrigation, saved construction, turn hooks and AI: '..count..' assertions passed');
