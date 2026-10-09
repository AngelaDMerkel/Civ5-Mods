-- The national wonder must display its painting once per completion, never
-- for another player or merely because a save containing it was loaded.
local count = 0;
local function eq(a, b, message) count = count + 1; assert(a == b, message); end
local values, callbacks, popups = {}, {}, {};
local turn, active, human, owns = 20, 0, true, true;
Game = { GetActivePlayer = function() return active; end,
    GetGameTurn = function() return turn; end, GetStartTurn = function() return 0; end };
GameInfoTypes = { BUILDING_CARAVANSARY = 7 };
ButtonPopupTypes = { BUTTONPOPUP_WONDER_COMPLETED_ACTIVE_PLAYER = 42 };
local city = { GetNumRealBuilding = function() return owns and 1 or 0; end };
Players = { [0] = { IsHuman = function() return human; end,
    GetCityByID = function(_, id) if id == 3 then return city; end end } };
Modding = { OpenSaveData = function() return {
    GetValue = function(k) return values[k]; end,
    SetValue = function(k, v) values[k] = v; end,
}; end };
Events = { SerialEventGameMessagePopup = function(info) popups[#popups + 1] = info; end };
GameEvents = { CityConstructed = { Add = function(fn) callbacks[#callbacks + 1] = fn; end } };
dofile(TEST_ROOT .. '/mod/Lua/RT_Art.lua');
RT_Art.Initialize(); RT_Art.Initialize();
eq(#callbacks, 1, 'initialization is idempotent');
eq(#popups, 0, 'loading an existing Ministry does not show a popup');
RT_Art.OnCityConstructed(1, 3, 7);
RT_Art.OnCityConstructed(0, 3, 8);
RT_Art.OnCityConstructed(nil, nil, nil);
eq(#popups, 0, 'ignore foreign or unrelated completions');
human = false; RT_Art.OnCityConstructed(0, 3, 7); human = true;
owns = false; RT_Art.OnCityConstructed(0, 3, 7); owns = true;
RT_Art.OnCityConstructed(0, 99, 7);
turn = 0; RT_Art.OnCityConstructed(0, 3, 7); turn = 20;
eq(#popups, 0, 'ignore AI, missing building/city, and setup turn');
callbacks[1](0, 3, 7);
eq(#popups, 1, 'human Ministry completion opens the native wonder popup');
eq(popups[1].Type, 42, 'use active-player wonder popup type');
eq(popups[1].Data1, 7, 'popup uses Ministry database art and text');
callbacks[1](0, 3, 7);
eq(#popups, 1, 'duplicate engine callback ignored');
RT_Art = nil; dofile(TEST_ROOT .. '/mod/Lua/RT_Art.lua');
RT_Art.OnCityConstructed(0, 3, 7);
eq(#popups, 1, 'duplicate stays suppressed across Lua reload');
turn = 30; RT_Art.OnCityConstructed(0, 3, 7);
eq(#popups, 2, 'a later genuine rebuild can show its painting');
print('Art completion integration: ' .. count .. ' assertions passed');
