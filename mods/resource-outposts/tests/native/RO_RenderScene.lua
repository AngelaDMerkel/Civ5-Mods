-- Disposable Outpost geometry/state fixture, never a campaign hook.
local done=false
local function createScene()
  if done then return end
  local marker=Map.GetPlot(0,0)
  if not marker or marker:GetScriptData()~="CG2_STATIC_TEST_V1" then return end
  if Game.GetElapsedGameTurns()~=0 or Game.IsGameMultiPlayer() then return end
  done=true
  local player=Players[Game.GetActivePlayer()]
  assert(player and player:IsHuman(),"CG2 requires an active human")
  local width,height=Map.GetGridSize()
  assert(width==24 and height==16,"CG2 unexpected map")
  for i=0,Map.GetNumPlots()-1 do
    local plot=Map.GetPlotByIndex(i)
    if plot:IsGoody() then plot:SetImprovementType(-1) end
    -- Reveal only the review area. Revealing the opponent's start opens diplomacy.
    local fogSite="__TERRAIN__"=="mixed" and plot:GetX()==12 and plot:GetY()==10
    if not fogSite and plot:GetX()>=6 and plot:GetX()<=12 and plot:GetY()>=6 and plot:GetY()<=12 then
      plot:ChangeVisibilityCount(player:GetTeam(),1,-1,true,true)
    end
  end
  local kind=assert(GameInfoTypes.IMPROVEMENT_CG2_STATIC)
  local intact=Map.GetPlot(8,8)
  intact:SetImprovementType(kind)
  local construction=Map.GetPlot(10,8)
  construction:ChangeBuildProgress(assert(GameInfoTypes.BUILD_CG2_STATIC),1,player:GetID())
  assert(construction:GetImprovementType()==-1,"CG2 must not complete construction")
  assert(construction:GetBuildProgress(GameInfoTypes.BUILD_CG2_STATIC)==1,"CG2 missing build progress")
  local ruined=Map.GetPlot(8,10)
  ruined:SetImprovementType(kind)
  ruined:SetImprovementPillaged(true)
  Map.GetPlot(10,10):SetImprovementType(GameInfoTypes.IMPROVEMENT_FORT)
  player:InitUnit(GameInfoTypes.UNIT_WARRIOR,8,8)
  if "__TERRAIN__"=="mixed" then
    local remembered=Map.GetPlot(12,10)
    remembered:SetImprovementType(kind)
    -- Stock Lua converts ChangeVisibilityCount's delta to a boolean, so -1
    -- increases sight. Let a disposable unit reveal/leave this tile naturally.
    local observer=player:InitUnit(GameInfoTypes.UNIT_WARRIOR,12,10)
    observer:Kill(false,-1)
    assert(remembered:IsRevealed(player:GetTeam()) and not remembered:IsVisible(player:GetTeam()),"CG2 expected a remembered fogged site")
  end
  UI.SetYieldVisibleMode(false)
  Events.RequestYieldDisplay(YieldDisplayTypes.AREA,0)
  UI.LookAt(Map.GetPlot(9,9))
  print("[CG2] scene-ready era=__ERA__ scale=__SCALE__ intact=8,8 construction=10,8 pillaged=8,10 fort=10,10")
end
Events.SequenceGameInitComplete.Add(createScene)
Events.LoadScreenClose.Add(createScene)
