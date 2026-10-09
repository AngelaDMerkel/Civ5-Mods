-- National wonders do not emit the stock world-wonder completion popup.
-- Queue the native popup for this one national wonder, using its database art.
RT_Art = RT_Art or {};
local A = RT_Art;

function A.OnCityConstructed(playerID, cityID, buildingID)
    if playerID ~= Game.GetActivePlayer() or buildingID ~= GameInfoTypes.BUILDING_CARAVANSARY then return; end
    local player = Players[playerID];
    if not player or not player:IsHuman() then return; end
    local turn = Game.GetGameTurn();
    if turn <= Game.GetStartTurn() then return; end -- matches the native popup
    local city = player:GetCityByID(cityID);
    if not city or city:GetNumRealBuilding(buildingID) < 1 then return; end
    local data = Modding.OpenSaveData();
    local key = 'RealisticTerrain.Art.Ministry.' .. tostring(playerID);
    local stamp = tostring(turn) .. ':' .. tostring(cityID);
    if data.GetValue(key) == stamp then return; end
    data.SetValue(key, stamp);
    Events.SerialEventGameMessagePopup({
        Type = ButtonPopupTypes.BUTTONPOPUP_WONDER_COMPLETED_ACTIVE_PLAYER,
        Data1 = buildingID,
    });
end

function A.Initialize()
    if A.initialized then return; end
    A.initialized = true;
    GameEvents.CityConstructed.Add(A.OnCityConstructed);
end
