-- The normal mod loader must instantiate the production UI entry. Do not
-- compensate for a missing entrypoint by manually loading its Lua or XML.
local checked = false;
local function verify()
    if checked or Game.IsGameMultiPlayer() then return; end
    if Map.GetPlot(0,0):GetScriptData() ~= "CG2_STATIC_TEST_V1" then return; end
    checked = true;
    local q = {}; LuaEvents.RO_NativeProbeQuery(q);
    assert(q.loaded, "[ROTEST] FAIL ordinary RO_UI entrypoint did not initialize");
    print("[ROTEST] ordinary RO_UI entrypoint verified");
end
Events.SequenceGameInitComplete.Add(verify);
Events.LoadScreenClose.Add(verify);
