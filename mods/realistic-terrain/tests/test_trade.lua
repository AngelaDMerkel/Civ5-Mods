-- Run the actual replacement trade adapter against a small deterministic world.
local count=0;
local function eq(a,b,why) count=count+1;assert(a==b,why..": "..tostring(a).." ~= "..tostring(b));end
local function check(a,why) eq(not not a,true,why);end
local turn, values = 0, {};
local translations={};
local localeFile=assert(io.open(TEST_ROOT.."/mods/realistic-terrain/src/Text/RT_Text.xml"));
for key,value in localeFile:read("*a"):gmatch('<Row Tag="([^"]+)"><Text>(.-)</Text></Row>')do translations[key]=value;end
localeFile:close();
Locale={ConvertTextKey=function(key,...)
    if key:find("^TXT_KEY_RT_TRADE_")then assert(translations[key],"Missing trade localization: "..key);end
    local args={...};return (translations[key] or key):gsub("{(%d+)[^}]*}",function(i)return tostring(args[tonumber(i)]);end);
end};
Game={GetGameTurn=function()return turn;end,GetActivePlayer=function()return 0;end,GetGameSpeedType=function()return 0;end};
GameDefines={MAX_CIV_PLAYERS=3};DomainTypes={DOMAIN_LAND=0,DOMAIN_SEA=1};
NotificationTypes={NOTIFICATION_GENERIC=1};OrderTypes={ORDER_TRAIN=1,ORDER_CONSTRUCT=2};MissionTypes={MISSION_MOVE_TO=1,MISSION_BUILD=2};
GameInfoTypes={};
for id,name in ipairs({"TERRAIN_DESERT","TERRAIN_TUNDRA","TERRAIN_SNOW","TERRAIN_OCEAN","FEATURE_JUNGLE","FEATURE_OASIS","FEATURE_FLOOD_PLAINS","FEATURE_ICE","ROUTE_ROAD","ROUTE_RAILROAD","IMPROVEMENT_RT_RELIEF_STATION","TECH_RT_CARAVAN_LOGISTICS","TECH_ASTRONOMY","BUILDING_CARAVANSARY","BUILDING_GRANARY","BUILDING_WORKSHOP","UNIT_CARAVAN","UNIT_CARGO_SHIP","UNIT_WORKER","BUILD_RT_RELIEF_STATION","BUILD_ROAD","BUILD_REPAIR","BUILDINGCLASS_CARAVANSARY","UNITCLASS_CARAVAN","UNITCLASS_CARGO_SHIP"})do GameInfoTypes[name]=id;end
local I=GameInfoTypes;
I.TECH_ENGINEERING=100;
I.TECH_COMBUSTION=101;I.UNIT_RT_MOTORIZED_CARAVAN=102;I.UNITCLASS_RT_MOTORIZED_CARAVAN=103;
CommandTypes={COMMAND_UPGRADE=1};
GameInfo={GameSpeeds={[0]={DealDuration=4}},Routes={[I.ROUTE_ROAD]={GoldMaintenance=1},[I.ROUTE_RAILROAD]={GoldMaintenance=2}},
    Improvements={[I.IMPROVEMENT_RT_RELIEF_STATION]={GoldMaintenance=0}}};
Modding={OpenSaveData=function()return{
    GetValue=function(k)assert(type(k)=="string","GetValue expects a string key, no self");return values[k];end,
    SetValue=function(k,v)assert(type(k)=="string","SetValue expects a string key, no self");values[k]=v;end,
};end};
local eventMeta={__index=function(t,k)local callbacks={};local event={Add=function(f)callbacks[#callbacks+1]=f;end,Fire=function(...)for _,f in ipairs(callbacks)do f(...);end;end};rawset(t,k,event);return event;end};
GameEvents=setmetatable({},eventMeta);Events=setmetatable({},eventMeta);
Teams={};local techs={};
for id=0,2 do
    local t={wars={}};Teams[id]=t;
    function t:IsAtWar(other)return self.wars[other] or false;end
    function t:IsHasMet()return true;end
    function t:GetTeamTechs()return{HasTech=function(_,tech)return techs[id..":"..tech] or false;end,
        ChangeResearchProgress=function(_,tech,amount,owner)self.science=(self.science or 0)+amount;end};end
end
local plots={};
for id=0,6 do
    local p={id=id,owner=id<=1 and 0 or id>=4 and 1 or -1,route=I.ROUTE_ROAD,units={},feature=-1,terrain=-1};plots[id]=p;
    function p:GetPlotIndex()return self.id;end
    function p:GetX()return self.id;end;function p:GetY()return 0;end
    function p:GetOwner()return self.owner;end
    function p:GetPlotCity()return self.city;end
    function p:GetRouteType()return self.route;end
    function p:IsRoutePillaged()return self.routePillaged or false;end
    function p:GetImprovementType()return self.improvement or -1;end
    function p:IsImprovementPillaged()return self.pillaged or false;end
    function p:IsWater()return self.water or false;end
    function p:IsMountain()return self.mountain or false;end
    function p:IsLake()return self.lake or false;end
    function p:IsRiver()return false;end
    function p:GetFeatureType()return self.feature;end
    function p:GetTerrainType()return self.terrain;end
    function p:GetNumUnits()return #self.units;end
    function p:GetUnit(i)return self.units[i+1];end
    function p:IsRevealed()return self.revealed~=false;end
    function p:IsVisible()return self.revealed~=false;end
    function p:CanBuild()return not self.city;end
end
Map={GetPlotByIndex=function(id)return plots[id];end,GetPlot=function(x)return plots[x];end,GetNumPlots=function()return 7;end,
    PlotDirection=function(x,y,d)if d==0 then return plots[x-1];elseif d==1 then return plots[x+1];end;end,
    PlotDistance=function(x,y,a,b)return math.abs(x-a);end};
local function iterator(list)local n=0;return function()n=n+1;return list[n];end;end
Players={};
for id=0,2 do
    local p={id=id,units={},cities={},gold=0,created=0};Players[id]=p;
    function p:IsAlive()return true;end
    function p:IsBarbarian()return self.id==2;end
    function p:IsHuman()return self.id==0;end
    function p:IsMinorCiv()return self.minor or false;end
    function p:CalculateGoldRateTimes100()return -375;end
    function p:IsTurnActive()return true;end
    function p:GetTeam()return self.id;end
    function p:IsDenouncedPlayer()return self.denounced or false;end
    function p:GetCivilizationShortDescription()return "Player "..self.id;end
    function p:Units()local a={};for _,u in pairs(self.units)do a[#a+1]=u;end;table.sort(a,function(x,y)return x.id<y.id;end);return iterator(a);end
    function p:Cities()return iterator(self.cities);end
    function p:GetUnitByID(id)return self.units[id];end
    function p:AddNotification()end
    function p:ChangeGold(n)self.gold=self.gold+n;end
    function p:GetNumInternationalTradeRoutesAvailable()return 3;end
    function p:GetTradeRouteRange(domain,city)return 10;end
    function p:GetInternationalTradeRouteTotal(from,to,domain,origin)return origin and 1000 or 500;end
    function p:GetInternationalTradeRouteScience()return 100;end
    function p:GetCurrentResearch()return 1;end
    function p:GetCurrentEra()return 1;end
    function p:CalculateUnitCost()return 2;end
    function p:GetNumUnits()local n=0;for _ in pairs(self.units)do n=n+1;end;return n;end
    function p:GetImprovementGoldMaintenance()return 4;end
    function p:GetCapitalCity()return self.cities[1];end
    function p:CountNumBuildings()return 1;end
    function p:GetBuildingClassMaking()return 0;end
    function p:GetUnitClassMaking()return 0;end
end
local function makeCity(id,owner)
    local c={id=id,owner=owner,food=0,production=0};plots[id].city=c;plots[id].owner=owner;
    function c:GetOwner()return self.owner;end;function c:GetX()return self.id;end;function c:GetY()return 0;end
    function c:Plot()return plots[self.id];end;function c:GetName()return "City "..self.id;end
    function c:GetNumBuilding()return 1;end
    function c:ChangeFood(n)self.food=self.food+n;end;function c:ChangeProduction(n)self.production=self.production+n;end
    function c:CanTrain()return true;end;function c:CanConstruct()return true;end
    function c:PushOrder(kind,item)self.queued=item;end
    table.insert(Players[owner].cities,c);return c;
end
local from,to=makeCity(0,0),makeCity(6,1);
local serial=0;
local function unit(owner,tile,kind,combat)
    serial=serial+1;local u={id=serial,owner=owner,tile=tile,kind=kind,moves=120,combat=combat,birth=turn};Players[owner].units[u.id]=u;table.insert(plots[tile].units,u);
    function u:GetID()return self.id;end;function u:GetOwner()return self.owner;end
    function u:GetTeam()return self.owner;end;function u:GetUnitType()return self.kind;end
    function u:GetPlot()return plots[self.tile];end;function u:GetGameTurnCreated()return self.birth;end
    function u:GetDomainType()return self.kind==I.UNIT_CARGO_SHIP and 1 or 0;end
    function u:IsCombatUnit()return self.combat or false;end
    function u:IsEmbarked()return false;end;function u:IsDelayedDeath()return self.dead or false;end
    function u:IsAutomated()return false;end;function u:GetBuildType()return -1;end
    function u:GetMoves()return self.moves;end;function u:FinishMoves()self.moves=0;end
    function u:CanBuild()return true;end;function u:PushMission(kind,a,b)self.mission={kind,a,b};end
    function u:Kill()self.dead=true;Players[self.owner].units[self.id]=nil;for i,v in ipairs(plots[self.tile].units)do if v==self then table.remove(plots[self.tile].units,i);break;end;end;end
    return u;
end
for id=0,2 do Players[id].InitUnit=function(self,kind,x,y)self.created=self.created+1;return unit(self.id,x,kind);end;end
local function load(name)dofile(RT_LUA(name));end
for _,name in ipairs({"RT_Serialize","RT_TradeRules","RT_TradeEconomy","RT_Supply","RT_TradeMap","RT_Trade"})do load(name);end
local T=RT_Trade;T.Initialize();
T.OnBuild(0,2,0);T.OnBuild(0,3,0);
local caravan=unit(0,0,I.UNIT_CARAVAN);
eq(T.Launch(caravan,6,"international"),false,"agreement blocks actual launch");eq(caravan.dead,nil,"rejected launch preserves unit");
check(T.Offer(0,1),"AI signs willing agreement");check(T.HasAgreement(1,0),"agreement reciprocal");
check(T.Launch(caravan,6,"international"),"authorized route starts");check(caravan.dead,"trade unit invested in route");
eq(T.Used(0),1,"route takes slot");
eq(T.Quote(from,to,0,"international").valid,false,"duplicate destination blocked in planner");
local steps={};T.OnRouteStep=function(route,a,b)steps[#steps+1]=a..":"..b;end;
turn=1;T.OnTurn(0);eq(T.state.routes[1].position,3,"caravan advances two tiles");check(Players[0].gold>0,"trade pays real player gold");
eq(table.concat(steps,","),"0:1,1:2","map presentation receives every actual route step in order");
eq(Teams[0].science,1,"international science credited to research");
local gold=Players[0].gold;T.OnTurn(0);eq(Players[0].gold,gold,"duplicate turn does not pay twice");eq(T.state.routes[1].position,3,"duplicate turn does not move twice");
T.OnTurn(1);check(Players[1].gold>0,"partner receives its own trade return");
local partnerGold=Players[1].gold;T.OnTurn(1);eq(Players[1].gold,partnerGold,"partner payment is also guarded");
load("RT_Trade");T=RT_Trade;RT_Supply.CanTransit=T.HasAgreement;
eq(T.Used(0),1,"active route survives save reload");T.OnTurn(0);eq(Players[0].gold,gold,"reload preserves payment guard");
T.Revoke(0,1);eq(T.Used(0),0,"revoking recalls affected route");eq(Players[0].created,1,"recall returns invested caravan once");
T.ValidateRoutes();eq(Players[0].created,1,"repeat validation does not duplicate caravan");
T.Offer(0,1);Teams[0].wars[1]=true;T.ValidateRoutes();Teams[0].wars[1]=false;
eq(T.HasAgreement(0,1),false,"peace does not silently reinstate agreement broken by war");
T.Offer(0,1);caravan=unit(0,0,I.UNIT_CARAVAN);T.Launch(caravan,6,"international");
plots[2].routePillaged=true;turn=2;T.OnTurn(0);eq(T.Used(0),0,"broken neutral road destroys pre-logistics caravan on entry");eq(Players[0].created,1,"lost caravan not refunded");
techs["0:"..I.TECH_RT_CARAVAN_LOGISTICS]=true;
plots[3].terrain=I.TERRAIN_DESERT;
local quote=T.Quote(from,to,0,"international");eq(quote.valid,true,"logistics permits roadless route");eq(quote.efficiency,20,"actual map applies both 40 percent penalties");
plots[2].routePillaged=false;plots[3].terrain=-1;
plots[2].improvement=I.IMPROVEMENT_RT_RELIEF_STATION;RT_Supply.OnBuildFinished(0,2,0,I.IMPROVEMENT_RT_RELIEF_STATION);
local guard=unit(0,2,999,true);T.UpdateGuards(0);
eq(RT_TradeMap.Patrol(RT_TradeMap.Context(0))[5],nil,"new garrison needs a full turn");
turn=3;check(RT_TradeMap.Patrol(RT_TradeMap.Context(0))[5],"mature garrison patrols shared road");
local enemy=unit(2,5,999,true);Teams[0].wars[2]=true;Teams[2].wars[0]=true;
caravan=unit(0,0,I.UNIT_CARAVAN);T.Launch(caravan,6,"international");
local route;for _,r in pairs(T.state.routes)do route=r;end;route.position=6;
eq(T.Raid(route),false,"patrol prevents caravan raid");check(T.state.routes[route.id],"protected caravan survives");
local civilian=unit(0,5,I.UNIT_WORKER);eq(T.IsTradeUnit(civilian),false,"ordinary civilians excluded from caravan protection");
plots[2].pillaged=true;eq(T.Raid(route),true,"pillage disables protection");eq(T.Used(0),0,"unprotected caravan destroyed");eq(Players[2].gold,100,"raider rewarded once");
plots[2].pillaged=false;enemy:Kill();
-- Leaving and returning cannot preserve an old patrol activation timestamp.
guard.tile=1;T.OnUnitMoved(0,guard.id);guard.tile=2;T.OnUnitMoved(0,guard.id);
eq(RT_TradeMap.Patrol(RT_TradeMap.Context(0))[5],nil,"moving garrison resets full-turn requirement");
caravan=unit(0,0,I.UNIT_CARAVAN);T.Launch(caravan,6,"international");
for n=4,12 do turn=n;T.OnTurn(0);end
eq(T.Used(0),0,"route eventually completes its circuit");eq(Players[0].created,2,"completed route returns one caravan");
caravan=unit(0,0,I.UNIT_CARAVAN);T.Launch(caravan,6,"international");to.owner=2;plots[6].owner=2;T.ValidateRoutes();
eq(T.Used(0),0,"city capture recalls route");to.owner=1;plots[6].owner=1;
-- Domestic cargo remains available and uses the same route slot lifecycle.
local own=makeCity(1,0);caravan=unit(0,0,I.UNIT_CARAVAN);check(T.Launch(caravan,1,"food"),"domestic food route starts without foreign agreement");
turn=13;T.OnTurn(0);check(own.food>0,"domestic route delivers food");
-- AI issues native worker/production missions rather than creating free assets.
RT_Construction={IsWorker=function(u)return u.kind==I.UNIT_WORKER;end,Work=function(u)u.worked=true;return true;end};
load("RT_TradeAI");local worker=unit(1,4,I.UNIT_WORKER);plots[4].route=-1;
RT_TradeAI.OnTurn(1);check(worker.mission and worker.mission[1]==MissionTypes.MISSION_BUILD,"AI worker builds missing road");
worker.mission=nil;
RT_OutpostBridge={Reserved=function(u)return u==worker;end};
RT_TradeAI.OnTurn(1);eq(worker.mission,nil,"trade logistics cannot reassign an outpost worker");
RT_OutpostBridge=nil;
eq(plots[4].route,-1,"AI does not instantly materialize road");plots[4].route=I.ROUTE_ROAD;
check(#T.state.projects[1]>0,"AI maintains corridor plan");
-- Sea routes require agreements but neither roads nor land relief.
for i=1,5 do plots[i].water=true;end;plots[3].terrain=I.TERRAIN_OCEAN;
eq(T.Quote(from,to,1,"international").valid,false,"ocean needs Astronomy");
techs["0:"..I.TECH_ASTRONOMY]=true;
local sea=T.Quote(from,to,1,"international");check(sea.valid,"Astronomy permits ocean route");eq(sea.efficiency,100,"no land infrastructure penalty at sea");eq(#sea.assetIDs,0,"sea route claims no land maintenance");
T.Revoke(0,1);eq(T.Quote(from,to,1,"international").valid,false,"sea agreement still mandatory");T.Offer(0,1);
for i=1,5 do plots[i].water=false;end;plots[3].terrain=-1;
-- A direct path may miss a station on a useful alternative road branch.
local oldDirection,oldCount,oldRange=Map.PlotDirection,Map.GetNumPlots,Players[0].GetTradeRouteRange;
plots[2].improvement=nil;
plots[7]=setmetatable({id=7,owner=-1,units={},improvement=I.IMPROVEMENT_RT_RELIEF_STATION},{__index=plots[2]});
Map.GetNumPlots=function()return 8;end;
Map.PlotDirection=function(x,y,d)
    if x==7 then if d==0 then return plots[3];elseif d==1 then return plots[4];end;return nil;end
    if (x==3 or x==4) and d==2 then return plots[7];end
    if x==6 and d==1 then return nil;end
    return oldDirection(x,y,d);
end;
Players[0].GetTradeRouteRange=function()return 2;end;
RT_Supply.OnBuildFinished(0,7,0,I.IMPROVEMENT_RT_RELIEF_STATION);
local relayed=T.Quote(from,to,0,"international");check(relayed.valid,"planner finds off-direct-path relay");
local visits=false;for _,id in ipairs(relayed.path)do if id==7 then visits=true;end;end;check(visits,"valid alternative actually visits relay");
eq(relayed.relays,1,"alternative route earns only one relay extension");
Players[0].GetTradeRouteRange=oldRange;
local motorDetour=T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN);
eq(motorDetour.efficiency,100,"motorized planner seeks a supplied stop even without a range shortage");
local motorVisits=false;for _,id in ipairs(motorDetour.path)do if id==7 then motorVisits=true;end;end;
check(motorVisits,"commercial detour actually visits the supplied Caravansary");
plots[7]=nil;plots[2].improvement=I.IMPROVEMENT_RT_RELIEF_STATION;Map.PlotDirection,Map.GetNumPlots,Players[0].GetTradeRouteRange=oldDirection,oldCount,oldRange;
local capacityUnit=unit(0,0,I.UNIT_CARAVAN);local oldCapacity=Players[0].GetNumInternationalTradeRoutesAvailable;
Players[0].GetNumInternationalTradeRoutesAvailable=function()return T.Used(0);end;
eq(T.Launch(capacityUnit,6,"international"),false,"capacity enforced on actual launch");eq(capacityUnit.dead,nil,"capacity rejection preserves unit");
Players[0].GetNumInternationalTradeRoutesAvailable=oldCapacity;
print("Replacement trade lifecycle, map rules and AI: "..count.." assertions passed");

-- Bootstrap the actual trade UI against controls; native rendering remains pending.
local function control()return setmetatable({}, {__index=function(t,k)
    if k=="RegisterCallback" then return function(self,_,f)self.callback=f;end;
    elseif k=="SetText" then return function(self,v)self.text=v;end;
    elseif k=="SetHide" then return function(self,v)self.hidden=v;end;
    elseif k=="SetDisabled" then return function(self,v)self.disabled=v;end;
    else return function()end;end
end});end
Controls={};for _,name in ipairs({"TradeRows","TradeTitle","TradeStatus","TradeScroll","TradePlanTab","TradeAgreementTab","TradeRoutesTab","TradeAccountsTab","TradeOpen","TradePanel","TradeClose"})do Controls[name]=control();end
local rows={};InstanceManager={new=function()return{GetInstance=function()local r={};for _,name in ipairs({"Title","Detail","Root","ActionLabel","Action","Locate"})do r[name]=control();end;rows[#rows+1]=r;return r;end,
    ResetInstances=function()rows={};end};end};
Mouse={eLClick=1};local selected=unit(0,0,I.UNIT_CARAVAN);
ContextPtr={SetInputHandler=function(self,f)self.input=f;end};KeyEvents={KeyDown=1};Keys={VK_ESCAPE=27};
UI={GetHeadSelectedUnit=function()return selected;end,LookAt=function()end};include=function(name)assert(name=="InstanceManager");end;
load("RT_TradeUI");Controls.TradeOpen.callback();eq(Controls.TradePanel.hidden,false,"planner opens");
Controls.TradeAgreementTab.callback();check(#rows>0,"agreement rows rendered");
Controls.TradePlanTab.callback();check(#rows>0,"destination previews rendered");
local launch;
for _,r in ipairs(rows)do if string.find(r.Title.text,"City 6") and not r.Action.disabled then launch=r.Action.callback;end;end
check(launch,"eligible international route has launch control");launch();check(selected.dead,"planner action invests selected caravan");
Controls.TradeAccountsTab.callback();check(string.find(rows[1].Title.text,"Projected net"),"income breakdown rendered");
Controls.TradeClose.callback();eq(Controls.TradePanel.hidden,true,"planner closes");
local raider=unit(2,4,999,true);Players[2].IsBarbarian=function()return false;end;
RT_TradeAI.OnTurn(2);check(raider.mission and raider.mission[1]==MissionTypes.MISSION_MOVE_TO,"hostile AI targets visible trade traffic");
raider.mission=nil;
RT_OutpostBridge={Reserved=function(u)return u==raider;end};
RT_TradeAI.OnTurn(2);eq(raider.mission,nil,"trade raiding cannot steal an outpost defender");
RT_OutpostBridge=nil;
print("Replacement trade + planner UI: "..count.." assertions passed");

-- The actual invested unit type controls road independence through every layer.
local ended={};for id in pairs(T.state.routes)do ended[#ended+1]=id;end
for _,id in ipairs(ended)do T.EndRoute(id,"Reset test world",true);end
raider:Kill();Teams[0].wars[2]=false;Teams[2].wars[0]=false;
for i=1,5 do plots[i].improvement=nil;plots[i].route=-1;plots[i].routePillaged=false;plots[i].terrain=-1;plots[i].feature=-1;plots[i].water=false;end
plots[3].terrain=I.TERRAIN_DESERT;
techs["0:"..I.TECH_RT_CARAVAN_LOGISTICS]=false;
techs["0:"..I.TECH_COMBUSTION]=true;
local truck=unit(0,0,I.UNIT_RT_MOTORIZED_CARAVAN);
check(T.IsTradeUnit(truck),"Motorized Caravan recognized as a trade unit");
eq(T.Quote(from,to,0,"international").valid,false,"Combustion does not grant ordinary Caravan road independence");
local shared=RT_TradeMap.Context(0);
for _,hazard in ipairs({I.TERRAIN_DESERT,I.TERRAIN_TUNDRA,I.TERRAIN_SNOW,I.FEATURE_JUNGLE})do
    plots[3].terrain=hazard==I.FEATURE_JUNGLE and -1 or hazard;
    plots[3].feature=hazard==I.FEATURE_JUNGLE and hazard or -1;
    local mq=T.Quote(from,to,0,"international",nil,shared,I.UNIT_RT_MOTORIZED_CARAVAN);
    check(mq.valid,"motorized path crosses each roadless harsh environment");
    eq(mq.efficiency,20,"motorized quote applies economic infrastructure deductions");
    eq(mq.roadPenalty,40,"motorized missing-road gold deduction applies");
    eq(mq.reliefPenalty,0,"motorized route is immune to terrain relief penalties");
    eq(mq.cargoEfficiency,100,"motorized food and production ignore gold deductions");
end
plots[3].terrain=-1;plots[3].feature=-1;
eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).efficiency,20,"mild terrain does not hide missing infrastructure");
plots[3].feature=I.FEATURE_OASIS;
eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).efficiency,20,"oasis is not a motorized commercial service stop");
plots[3].feature=-1;
for i=1,5 do plots[i].route=I.ROUTE_ROAD;end
eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).efficiency,60,"roads alone restore one commercial component");
plots[2].improvement=I.IMPROVEMENT_RT_RELIEF_STATION;
RT_Supply.OnBuildFinished(0,2,0,I.IMPROVEMENT_RT_RELIEF_STATION);
local serviced=T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN);
eq(serviced.efficiency,100,"continuous roads and supplied Caravansary restore full motorized gold");
check(serviced.usedStations[2],"actual commercial stop earns station compensation");
plots[3].route=-1;
eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).efficiency,60,"station can remain supplied while another road segment is absent");
plots[2].pillaged=true;
eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).efficiency,20,"pillaged stop loses service discount");plots[2].pillaged=false;
plots[2].route=-1;
eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).efficiency,20,"disconnected stop loses service discount");
for i=1,5 do plots[i].route=-1;plots[i].improvement=nil;end
plots[3].terrain=I.TERRAIN_DESERT;plots[3].feature=-1;
eq(T.Quote(from,to,0,"international",nil,shared,I.UNIT_CARAVAN).valid,false,"unit capability never leaks through shared map context");
techs["0:"..I.TECH_RT_CARAVAN_LOGISTICS]=true;
eq(T.Quote(from,to,0,"international",nil,shared,I.UNIT_CARAVAN).efficiency,20,"ordinary Caravan retains both penalties after Combustion");
techs["0:"..I.TECH_RT_CARAVAN_LOGISTICS]=false;
plots[3].mountain=true;eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).valid,false,"motorized trader cannot cross mountains");plots[3].mountain=false;
plots[3].feature=I.FEATURE_ICE;eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).valid,false,"motorized trader cannot cross ice");plots[3].feature=-1;
plots[3].water=true;eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).valid,false,"motorized land route cannot cross water");plots[3].water=false;
plots[3].revealed=false;eq(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).valid,false,"motorized trader cannot use unrevealed land");plots[3].revealed=true;
T.Revoke(0,1);eq(T.Launch(truck,6,"international"),false,"motorized route still needs a trade agreement");T.Offer(0,1);
check(T.Launch(truck,6,"international"),"motorized unit launches without roads or Logistics");
local motorID=T.state.nextID-1;local mr=T.state.routes[motorID];
eq(mr.unitType,I.UNIT_RT_MOTORIZED_CARAVAN,"route records motorized investment");
local ledger=T.Settlement();eq(ledger.routes[tostring(motorID)].efficiency,20,"settlement applies economic deductions to motorized gold");
eq(ledger.players[0].commercial100,400,"origin receives 20 percent of doubled native commerce");
eq(ledger.players[1].commercial100,200,"partner receives the same infrastructure percentage");
local oldUnits={};for u in Players[0]:Units()do oldUnits[u:GetID()]=true;end
turn=turn+1;T.OnTurn(0);check(T.state.routes[motorID],"motorized caravan survives roadless neutral movement");
eq(mr.position,3,"motorized route keeps normal caravan speed");
local oldGold=Players[0].gold;T.OnTurn(0);eq(Players[0].gold,oldGold,"motorized payment is guarded against duplicate turns");
load("RT_Trade");T=RT_Trade;RT_Supply.CanTransit=T.HasAgreement;
eq(T.state.routes[motorID].unitType,I.UNIT_RT_MOTORIZED_CARAVAN,"motorized identity survives save reload");
eq(T.Settlement().routes[tostring(motorID)].efficiency,20,"motorized gold rules survive save reload");
T.EndRoute(motorID,"Recall motorized trader",false);
local returned;for u in Players[0]:Units()do if not oldUnits[u:GetID()]then returned=u;end;end
check(returned and returned:GetUnitType()==I.UNIT_RT_MOTORIZED_CARAVAN,"recall returns the motorized unit, never a basic Caravan");
check(T.Launch(returned,6,"international"),"returned motorized caravan can establish a new route");
motorID=T.state.nextID-1;
for n=1,16 do turn=turn+1;T.OnTurn(0);end
eq(T.state.routes[motorID],nil,"motorized route completes normally");
local latest;for u in Players[0]:Units()do if not latest or u:GetID()>latest:GetID()then latest=u;end;end
eq(latest:GetUnitType(),I.UNIT_RT_MOTORIZED_CARAVAN,"completion returns the motorized unit type");
check(T.Launch(latest,6,"international"),"motorized route launched for raid test");
local lost=T.state.routes[T.state.nextID-1];lost.position=4;
local motorRaider=unit(2,3,999,true);Teams[0].wars[2]=true;Teams[2].wars[0]=true;
check(T.Raid(lost),"motorized caravan is not raid immune");motorRaider:Kill();Teams[0].wars[2]=false;Teams[2].wars[0]=false;

-- Domestic motorized deliveries are independent of commercial gold deductions.
local ownFar=makeCity(5,0);plots[3].terrain=-1;
truck=unit(0,0,I.UNIT_RT_MOTORIZED_CARAVAN);local foodBefore=ownFar.food;
check(T.Launch(truck,5,"food"),"motorized domestic route launches across roadless neutral land");
turn=turn+1;T.OnTurn(0);eq(ownFar.food-foodBefore,4,"domestic cargo receives no missing-road penalty");
T.EndRoute(T.state.nextID-1,"Domestic test complete",true);

-- Combustion leaves ordinary AI traders in service and preserves a reason to
-- produce each type. No automatic replacement or paid upgrade command exists.
load("RT_TradeAI");techs["1:"..I.TECH_COMBUSTION]=true;
local aiOld=unit(1,6,I.UNIT_CARAVAN);
function aiOld:DoCommand()error("AI must not replace an ordinary Caravan");end
local ordinaryRouteID=T.state.nextID;
RT_TradeAI.OnTurn(1);check(T.state.routes[ordinaryRouteID],"AI continues using ordinary Caravan after Combustion");
eq(T.state.routes[ordinaryRouteID].unitType,I.UNIT_CARAVAN,"existing AI trader retains original type");
T.EndRoute(ordinaryRouteID,"AI alternative test complete",true);
local remove={};for u in Players[1]:Units()do if T.IsTradeUnit(u)then remove[#remove+1]=u;end;end;for _,u in ipairs(remove)do u:Kill();end
for i=1,5 do plots[i].route=I.ROUTE_ROAD;end
T.state.aiLast[1]=turn-8;to.queued=nil;
RT_TradeAI.OnTurn(1);eq(to.queued,I.UNIT_CARAVAN,"AI retains cheaper Caravan production on developed corridor");
-- Remove road access in neutral territory, without granting early Logistics.
for i=1,5 do plots[i].route=-1;end
techs["1:"..I.TECH_RT_CARAVAN_LOGISTICS]=false;
eq(RT_TradeAI.LandUnitForRoute(to,from),I.UNIT_RT_MOTORIZED_CARAVAN,"AI selects motorized capability for roadless neutral access");
local allDestinations=Players[0].cities;Players[0].cities={from};
T.state.aiLast[1]=turn-8;to.queued=nil;
RT_TradeAI.OnTurn(1);eq(to.queued,I.UNIT_RT_MOTORIZED_CARAVAN,"AI produces motorized alternative when it opens the route");
Players[0].cities=allDestinations;

-- Planner must show the selected unit's exact penalty and launch that unit.
selected=unit(0,0,I.UNIT_RT_MOTORIZED_CARAVAN);plots[3].terrain=I.TERRAIN_DESERT;
load("RT_TradeUI");Controls.TradeOpen.callback();Controls.TradePlanTab.callback();
local motorLaunch;
for _,r in ipairs(rows)do
    if string.find(r.Title.text,"City 6") and not r.Action.disabled then
        check(string.find(r.Detail.text,"efficiency 20%%"),"planner reports motorized efficiency");
        check(string.find(r.Detail.text,"terrain immune"),"planner explains unit exemption");
        check(string.find(r.Detail.text,"Road continuity missing"),"planner shows road gold deduction");
        check(string.find(r.Detail.text,"No supplied Caravansary stop"),"planner shows station gold deduction");
        eq(string.find(r.Detail.text,"Harsh-terrain relief missing"),nil,"planner does not report a terrain penalty");
        motorLaunch=r.Action.callback;
    end
end
check(motorLaunch,"planner offers motorized destination");motorLaunch();check(selected.dead,"planner invests motorized unit");
print("Replacement trade including Motorized Caravan: "..count.." assertions passed");

-- Real settlement/launch/pay paths must all respect current Congress decisions.
local resolutionRows, member = {}, true;
GameInfo.Resolutions={[10]={EmbargoPlayer=true},[11]={EmbargoCityStates=1},[12]={EmbargoPlayer=0,EmbargoCityStates=false}};
Game.GetActiveLeague=function()return{IsMember=function(_,owner)return member and owner~=2;end,
    GetActiveResolutions=function()return resolutionRows;end};end;
local account=T.Settlement().players[0];local forecast=T.Forecast(0);
eq(forecast.native100,-375,"forecast preserves native maintenance and deficit");
eq(forecast.payment100,account.payment100,"forecast adds gross treasury credit");
eq(forecast.total100,-375+account.payment100,"forecast does not deduct infrastructure expenses twice");
local beforeEmbargo=Players[0].created;
resolutionRows={{Type=10,ProposerDecision=1}};
check(T.IsEmbargoed(0,1),"targeted recipient is embargoed");
check(T.IsEmbargoed(1,0),"targeted origin is embargoed");
eq(T.IsEmbargoed(0,0),false,"domestic trade is exempt");
eq(T.IsEmbargoed(2,1),false,"nonmember outgoing trade is exempt");
member=false;eq(T.IsEmbargoed(0,1),false,"Congress membership is required");member=true;
Players[1].minor=true;eq(T.IsEmbargoed(0,1),false,"major sanctions do not also embargo city states");
resolutionRows={{Type=11,ProposerDecision=-1}};check(T.IsEmbargoed(0,1),"city-state embargo applies");
Players[1].minor=false;eq(T.IsEmbargoed(0,1),false,"city-state embargo does not target majors");
resolutionRows={{Type=12,ProposerDecision=1},{Type=999,ProposerDecision=1}};
eq(T.IsEmbargoed(0,1),false,"zero SQL booleans and unrelated/unknown resolutions are ignored");
resolutionRows={{Type=10,ProposerDecision=1}};
eq(T.Quote(from,to,0,"international",{0,1,2,3,4,5,6},nil,I.UNIT_RT_MOTORIZED_CARAVAN).reason,"TXT_KEY_RT_TRADE_EMBARGO","saved paths do not bypass embargoes");
truck=unit(0,0,I.UNIT_RT_MOTORIZED_CARAVAN);
eq(T.Launch(truck,6,"international"),false,"embargo prevents new launch");eq(truck.dead,nil,"rejection preserves idle unit");
eq(T.Forecast(0).payment100,0,"embargoed routes cannot earn before recall runs");
turn=turn+1;local cashBefore=Players[0].gold;T.Pay(0);
eq(Players[0].gold,cashBefore,"no embargoed income is paid");
T.ValidateRoutes();eq(T.Used(0),0,"active embargoed routes recalled");
eq(Players[0].created,beforeEmbargo+1,"recall returns exactly one invested trade unit");
check(T.HasAgreement(0,1),"sanctions preserve signed commercial agreements");
T.ValidateRoutes();eq(Players[0].created,beforeEmbargo+1,"repeat validation cannot duplicate returned unit");
resolutionRows={};check(T.Quote(from,to,0,"international",nil,nil,I.UNIT_RT_MOTORIZED_CARAVAN).valid,"repeal reopens planning");
Game.GetActiveLeague=function()return nil;end;eq(T.IsEmbargoed(0,1),false,"pre-Congress game permits trade");
print("Congress enforcement and income forecast: "..count.." assertions passed");

-- Incoming foreign traffic is not privileged information: both list entries
-- and stale Locate callbacks must respect current visibility.
local foreign={id=999,owner=1,recipient=0,from=6,to=0,path={6,5,4,3,2,1,0},position=4,
    unitType=I.UNIT_CARAVAN,kind="international",age=1,minimumTurns=10};
T.state.routes[999]=foreign;plots[3].revealed=false;T.OpenRoutes();
eq(#rows,1,"hidden incoming route is omitted");eq(rows[1].Title.text,"No active routes","recipient cannot track route through fog");
plots[3].revealed=true;plots[6].revealed=false;T.OnChanged();
check(rows[1].Title.text:find("Unknown origin"),"visible foreign marker cannot expose unrevealed endpoint name");
eq(rows[1].Action.hidden,true,"foreign route cannot be recalled");
local locate=rows[1].Locate.callback;local looked=false;UI.LookAt=function()looked=true;end;
plots[3].revealed=false;locate();eq(looked,false,"stale Locate callback cannot reveal hidden position");
plots[3].revealed=true;plots[6].revealed=true;T.state.routes[999]=nil;
Controls.TradeAccountsTab.callback();local foundForecast,foundLimits=false,false;
for _,r in ipairs(rows)do
    foundForecast=foundForecast or r.Title.text:find("Empire forecast");
    foundLimits=foundLimits or r.Detail.text:find("religious pressure");
end
check(foundForecast,"accounts renders combined empire forecast");check(foundLimits,"accounts discloses native subsystem limits");
eq(ContextPtr.input(KeyEvents.KeyDown,Keys.VK_ESCAPE),true,"Escape closes only open planner");
eq(Controls.TradePanel.hidden,true,"Escape hides planner");
eq(ContextPtr.input(KeyEvents.KeyDown,Keys.VK_ESCAPE),false,"closed planner does not consume Escape");
print("Trade UI localization, forecast and fog-of-war: "..count.." assertions passed");
