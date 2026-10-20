-- Temporary loader; never initialize the mod in an unrelated campaign.
local loaded = false;
local function start()
    if loaded or MapModData.RO_NativeGameplayLoaded or Game.IsGameMultiPlayer() then return; end
    local marker = Map.GetPlot(0, 0);
    if not marker or marker:GetScriptData() ~= "CG2_STATIC_TEST_V1" then return; end
    local w, h = Map.GetGridSize();
    assert(w == 24 and h == 16 and Game.GetActivePlayer() == 0, "ROTEST wrong fixture");
    loaded = true;
    MapModData.RO_NativeGameplayLoaded = true;
    local parent = ContextPtr:LookUpControl("/InGame");
    assert(parent, "ROTEST missing InGame context");
    RO_NativeContext = parent:LoadNewContext("RO_UI");
    assert(RO_NativeContext, "ROTEST production context did not load");
    print("[ROTEST] loaded production RO_UI context");
end
Events.SequenceGameInitComplete.Add(start);
Events.LoadScreenClose.Add(start);
