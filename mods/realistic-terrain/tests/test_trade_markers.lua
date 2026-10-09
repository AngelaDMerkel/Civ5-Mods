-- Exercise the actual presentation adapter without real units or game writes.
local count=0;
local function eq(a,b,why)count=count+1;assert(a==b,why..": "..tostring(a).." ~= "..tostring(b));end
local active, cityMode, strategic=0,false,false;
Game={GetActivePlayer=function()return active;end};
Players={[0]={GetTeam=function()return 0;end,GetCivilizationShortDescription=function()return "Us";end},
    [1]={GetTeam=function()return 1;end,GetCivilizationShortDescription=function()return "Them";end}};
local plots={};for id=0,3 do
    local p={id=id,visible=true};plots[id]=p;
    function p:GetX()return self.id;end;function p:GetY()return 0;end
    function p:IsVisible()return self.visible;end
end
Map={GetPlotByIndex=function(id)return plots[id];end};
GridToWorld=function(x,y)return x*20,y*20,0;end;
InStrategicView=function()return strategic;end;
local callbacks={};
Events=setmetatable({},{__index=function(t,k)local event={Add=function(f)callbacks[k]=f;end};t[k]=event;return event;end});
local all={};
local function control()return{
    SetHide=function(self,v)self.hidden=v;end,
    SetWorldPositionVal=function(self,x,y,z)self.x,self.y,self.z=x,y,z;end,
    SetToolTipString=function(self,v)self.tooltip=v;end,
    RegisterCallback=function(self,_,f)self.callback=f;end
};end
Controls={TradeMarkers=control()};ContextPtr={SetUpdate=function(self,f)self.update=f;end};Mouse={eLClick=1};
GameInfo={Units={[5]={PortraitIndex=9,IconAtlas="UNIT_ATLAS",Description="Caravan"}}};
Locale={ConvertTextKey=function(key,...)return key..table.concat({...}," ");end};
include=function(name)assert(name=="InstanceManager" or name=="IconSupport");end;
IconHookup=function(index,size,atlas,control)control.index,control.size,control.atlas=index,size,atlas;end;
InstanceManager={new=function()return{
    GetInstance=function()local row={Anchor=control(),Select=control(),Portrait={}};all[#all+1]=row;return row;end,
    ReleaseInstance=function(_,row)row.released=true;row.Anchor.hidden=true;end,
    ResetInstances=function()for _,row in ipairs(all)do row.Anchor.hidden=true;row.released=true;end;end
};end};
local route={id=1,owner=0,recipient=1,unitType=5,path={0,1,2,3},position=1};
local foreign={id=2,owner=1,recipient=0,unitType=5,path={3,2,1,0},position=2};
local openCount=0;
RT_Trade={state={routes={[1]=route}},OpenRoutes=function()openCount=openCount+1;end};
dofile(RT_LUA("RT_TradeMarkers"));local V=RT_TradeMarkers;
eq(#all,1,"saved route gets a marker on load");eq(all[1].Anchor.x,0,"saved initial position");
eq(all[1].Portrait.index,9,"marker uses native portrait reference");
eq(all[1].Portrait.size,32,"portrait uses supported atlas size");
all[1].Select.callback();eq(openCount,1,"marker opens route manager");
route.position=2;RT_Trade.OnRouteStep(route,0,1);route.position=3;RT_Trade.OnRouteStep(route,1,2);
RT_Trade.OnVisualChanged();ContextPtr.update(0.11);
eq(all[1].Anchor.x,10,"first road segment interpolates without teleporting");
ContextPtr.update(0.11);eq(all[1].Anchor.x,20,"first segment completes");
ContextPtr.update(0.22);eq(all[1].Anchor.x,40,"second segment follows saved path");
eq(route.position,3,"presentation never advances saved simulation");
plots[2].visible=false;RT_Trade.state.routes[2]=foreign;V.Refresh();
eq(#all,1,"foreign incoming route hidden in fog");eq(V.Visible(route,2),true,"own position remains known without revealing terrain");
plots[2].visible=true;callbacks.HexFOWStateChanged();local f=all[#all];
eq(#all,2,"foreign traffic appears only when visible");
foreign.position=3;V.Step(foreign,2,1);plots[1].visible=false;V.Update(0.1);
eq(f.Anchor.hidden,true,"fog change cancels foreign animation immediately");
f.Select.callback();eq(openCount,1,"stale foreign callback is visibility checked");
plots[1].visible=true;V.Refresh();eq(f.Anchor.x,20,"newly visible traffic snaps to current position");
eq(f.Anchor.hidden,false,"reappearing marker is shown");
callbacks.SerialEventEnterCityScreen();eq(Controls.TradeMarkers.hidden,true,"city screen hides markers");
callbacks.SerialEventExitCityScreen();eq(Controls.TradeMarkers.hidden,false,"map restores markers");
callbacks.StrategicViewStateChanged(true);eq(Controls.TradeMarkers.hidden,true,"strategic view hides 3D anchors");
callbacks.StrategicViewStateChanged(false);eq(Controls.TradeMarkers.hidden,false,"normal view restores anchors");
active=-1;callbacks.GameplaySetActivePlayer();
eq(all[#all].Anchor.hidden,true,"invalid active player clears previous player's traffic");
active=1;plots[2].visible=false;callbacks.GameplaySetActivePlayer();
eq(V.Visible(route,2),false,"new player cannot inherit old owner's fog exemption");
RT_Trade.state.routes={};RT_Trade.OnVisualChanged();
eq(all[#all].released,true,"ended route releases marker");
print("Moving trade markers and visibility: "..count.." assertions passed");
