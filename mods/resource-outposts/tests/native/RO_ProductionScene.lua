-- Only the isolated fresh CG2 map. Uses production RO_Eras and actual BNW setters.
local done=false
local function createScene()
  if done then return end
  local marker=Map.GetPlot(0,0)
  if not marker or marker:GetScriptData()~="CG2_STATIC_TEST_V1" then return end
  if Game.GetElapsedGameTurns()~=0 or Game.IsGameMultiPlayer() then return end
  done=true
  assert(Game.GetActivePlayer()==0 and Players[0]:IsHuman(),"CG2 requires player zero")
  local width,height=Map.GetGridSize()
  assert(width==24 and height==16,"CG2 unexpected map")
  include("RO_Eras")
  for i=0,Map.GetNumPlots()-1 do
    local p=Map.GetPlotByIndex(i)
    if p:IsGoody() then p:SetImprovementType(-1) end
    if p:GetX()>=6 and p:GetX()<=12 and p:GetY()>=6 and p:GetY()<=12 then
      p:ChangeVisibilityCount(Players[0]:GetTeam(),1,-1,true,true)
    end
  end
  local I=GameInfoTypes
  local intact,ruin,construction=Map.GetPlot(8,8),Map.GetPlot(8,10),Map.GetPlot(10,8)
  intact:SetImprovementType(I.IMPROVEMENT_RT_RESOURCE_OUTPOST,-1)
  ruin:SetImprovementType(I.IMPROVEMENT_RT_RESOURCE_OUTPOST,-1)
  ruin:SetImprovementPillaged(true)
  intact:SetUpgradeProgress(17); ruin:SetUpgradeProgress(23)
  construction:ChangeBuildProgress(I.BUILD_RT_RESOURCE_OUTPOST,1,0)
  local unit=Players[0]:InitUnit(I.UNIT_WARRIOR,8,8)
  local damage,moves=unit:GetDamage(),unit:MovesLeft()
  local other=Teams[Players[1]:GetTeam()]
  local rows={}
  for row in GameInfo.RO_OutpostEras() do rows[#rows+1]=row end
  table.sort(rows,function(a,b) return I[a.EraType]<I[b.EraType] end)
  assert(#rows==8,"CG2 must exercise all eight eras")
  for _,row in ipairs(rows) do
    other:SetCurrentEra(I[row.EraType])
    assert(Players[0]:GetCurrentEra()==I.ERA_ANCIENT,"CG2 active player changed era")
    assert(RO_Eras.Target(1)==I[row.ImprovementType],"CG2 claimant target differs")
    RO_Eras.Sync(intact,1); RO_Eras.Sync(ruin,1)
    assert(intact:GetImprovementType()==I[row.ImprovementType],"CG2 intact era swap failed")
    assert(ruin:GetImprovementType()==I[row.ImprovementType] and ruin:IsImprovementPillaged(),"CG2 ruin swap failed")
    assert(intact:GetUpgradeProgress()==17 and ruin:GetUpgradeProgress()==23,"CG2 upgrade progress changed")
    assert(intact:GetOwner()==-1 and ruin:GetOwner()==-1,"CG2 claimed territory")
    assert(construction:GetBuildProgress(I.BUILD_RT_RESOURCE_OUTPOST)==1 and construction:GetImprovementType()==-1,"CG2 altered ongoing construction")
    assert(unit:GetX()==8 and unit:GetY()==8 and unit:GetDamage()==damage and unit:MovesLeft()==moves,"CG2 altered garrison")
    assert(not RO_Eras.Sync(intact,1),"CG2 repeated callback must not swap")
    print("[CG2] native-era-passed "..row.EraType)
  end
  -- Exercise backwards capture-era selection, then return to Information for view.
  RO_Eras.Sync(intact,0)
  assert(intact:GetImprovementType()==I.IMPROVEMENT_RO_OUTPOST_ANCIENT,"CG2 backward selection failed")
  RO_Eras.Sync(intact,1)
  -- The Fort is a visible completion sentinel: it is never placed after a failed assertion.
  Map.GetPlot(10,10):SetImprovementType(I.IMPROVEMENT_FORT)
  UI.SetYieldVisibleMode(false)
  Events.RequestYieldDisplay(YieldDisplayTypes.AREA,0)
  UI.LookAt(Map.GetPlot(9,9))
  print("[CG2] native-production-checks-passed: 8 eras, active-player independence, pillage, repeated callbacks, backwards selection, build progress, garrison and neutral ownership")
  print("[CG2] scene-ready production Information models plus public construction and stock Fort")
end
Events.SequenceGameInitComplete.Add(createScene)
Events.LoadScreenClose.Add(createScene)
