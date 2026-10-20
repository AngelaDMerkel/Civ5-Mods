-- Original disposable map for the shared GR2 renderer test. No production use.
include("MapGenerator")

function GetMapScriptInfo()
  return {Name="GR2 Static Rendering Test", Description="Disposable 24 by 16 grassland scene; two players, no city states.", SupportsMultiplayer=false}
end

function GetMapInitData(worldSize)
  return {Width=24, Height=16, WrapX=false}
end

function GeneratePlotTypes()
  local plots={}
  for i=1,24*16 do plots[i]=PlotTypes.PLOT_LAND end
  SetPlotTypes(plots)
  GenerateCoasts()
end

function GenerateTerrain()
  local terrain={}
  for i=1,24*16 do terrain[i]=GameInfoTypes.TERRAIN_GRASS end
  SetTerrainTypes(terrain)
end

function AddFeatures() end
function AddRivers() end
function AddLakes() end

function StartPlotSystem()
  for id=0,GameDefines.MAX_MAJOR_CIVS-1 do
    local player=Players[id]
    if player and player:IsEverAlive() then
      player:SetStartingPlot(Map.GetPlot(4+(id%4)*5,3+math.floor(id/4)*2))
    end
  end
  Map.GetPlot(0,0):SetScriptData("CG2_STATIC_TEST_V1")
end
