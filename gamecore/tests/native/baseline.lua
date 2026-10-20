-- Disposable LoadScreen hook. Never part of a playable mod or developer binary.
do
    local run = "__C5M_RUN__"
    local tested = false
    Events.SequenceGameInitComplete.Add(function()
        if tested then return end
        tested = true
        local ok, message = pcall(function()
            assert(Game.C5MGetCoreInfo, "shared core API is missing")
            local info = Game.C5MGetCoreInfo()
            assert(info.Version == "0.1.0", "unexpected core version")
            assert(info.Ready and info.Phase == "frozen", "core configuration is not ready")
            assert(info.Error == "" and not info.OwnsModSimulation, "unexpected simulation owner")
            assert(Game.C5MHasCapability("c5m.core-introspection", 1), "missing introspection")
            assert(not Game.C5MHasCapability("terrain.native-trade", 1), "unexpected native trade")
            local modules = Game.C5MGetModules()
            assert(#modules == 1 and modules[1] == "c5m.core", "unexpected enabled modules")
            local width, height = Map.GetGridSize()
            assert(width > 0 and height > 0 and Map.GetPlot(0, 0), "map is not initialized")
            assert(Game.GetActivePlayer() == 0 and Players[0]:IsHuman(), "missing test human")
            local units = 0
            for unit in Players[0]:Units() do
                assert(unit:GetPlot() and unit:GetOwner() == 0, "invalid starting unit")
                units = units + 1
            end
            assert(units >= 2 and Players[1]:IsAlive(), "missing starting roster")
            OnActivateButtonClicked()
            print("[C5M_NATIVE] run=" .. run .. " status=PASS version=" .. info.Version ..
                  " turn=" .. Game.GetGameTurn() .. " units=" .. units ..
                  " width=" .. width .. " height=" .. height)
        end)
        if not ok then
            print("[C5M_NATIVE] run=" .. run .. " status=FAIL error=" .. tostring(message))
        end
    end)
end
