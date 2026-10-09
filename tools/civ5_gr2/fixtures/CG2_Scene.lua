-- Original fixture, deliberately independent of mod gameplay and test GameCores.
local done=false
print("[CG2] registering guarded scene callbacks")
local function createScene()
  if done then return end
  local marker=Map.GetPlot(0,0)
  print("[CG2] scene-check marker="..tostring(marker and marker:GetScriptData()).." turn="..tostring(Game.GetElapsedGameTurns()))
  if not marker or marker:GetScriptData()~="CG2_STATIC_TEST_V1" then return end
  done=true
  -- Loading any later save is observation only; never mutate a user's campaign.
  if Game.GetElapsedGameTurns()~=0 or Game.IsGameMultiPlayer() then return end
  local width,height=Map.GetGridSize()
  assert(width==24 and height==16,"CG2 unexpected test map dimensions")
  local player=Players[Game.GetActivePlayer()]
  assert(player and player:IsHuman(),"CG2 needs an active human")
  assert(GameInfoTypes.IMPROVEMENT_CG2_STATIC,"CG2 database fixture missing")
  local candidate=Map.GetPlot(8,8)
  local control=Map.GetPlot(10,8)
  candidate:SetImprovementType(GameInfoTypes.IMPROVEMENT_CG2_STATIC)
  control:SetImprovementType(GameInfoTypes.IMPROVEMENT_FORT)
  player:InitUnit(GameInfoTypes.UNIT_SCOUT,9,7)
  for i=0,Map.GetNumPlots()-1 do
    Map.GetPlotByIndex(i):SetRevealed(player:GetTeam(),true)
  end
  UI.LookAt(candidate)
  print("[CG2] scene-ready candidate=8,8 control-fort=10,8 model=__MODEL__ scale=__SCALE__ gr2-sha256=__HASH__")
  print("[CG2] placement-only; native rendering requires a visible screenshot and review")
end
Events.SequenceGameInitComplete.Add(createScene)
Events.LoadScreenClose.Add(createScene)
