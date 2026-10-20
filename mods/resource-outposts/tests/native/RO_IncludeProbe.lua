-- Separate disposable context: observe include resolution without changing the
-- production Terrain UI globals or calling either module's Initialize method.
include("RT_Irrigation");
print("[ROTEST] include-prefix RT_Irrigation=" .. type(RT_Irrigation)
      .. " RT_IrrigationAI=" .. type(RT_IrrigationAI));
include("RT_Irrigation.lua");
print("[ROTEST] include-exact RT_Irrigation=" .. type(RT_Irrigation));
