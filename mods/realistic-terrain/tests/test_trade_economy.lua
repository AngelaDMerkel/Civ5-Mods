dofile(TEST_ROOT .. "/mods/realistic-terrain/src/Lua/RT_TradeEconomy.lua");
local E, count = RT_TradeEconomy, 0;
local function eq(a, b, why) count = count + 1; assert(a == b, why .. ": " .. tostring(a) .. " ~= " .. tostring(b)); end
eq(E.Efficiency(true, true), 100, "supported trade");
eq(E.Efficiency(false, true), 60, "road penalty");
eq(E.Efficiency(true, false), 60, "relief penalty");
eq(E.Efficiency(false, false), 20, "additive 80 percent penalty");
local assets = {
    road = { owner = 0, kind = "road", upkeep100 = 100, standardCapital100 = 1000 },
    station = { owner = 1, kind = "caravansary", upkeep100 = 0, standardCapital100 = 2000 },
    guard = { owner = 1, kind = "garrison", upkeep100 = 300, standardCapital100 = 90000 },
};
local a = { id = "a", active = true, authorized = true, efficiency = 100,
    nativeGold100 = { [0] = 1000, [1] = 500 }, efficientDistance = 30,
    assets = { "road", "station", "guard", "road" } };
local one = E.Settle({a}, assets);
eq(one.players[0].upkeepCompensation100, 100, "one road billed once despite path duplicate");
eq(one.players[0].dividend100, 20, "road's ongoing capital return");
eq(one.players[1].dividend100, 40, "no capital dividend for expensive garrison");
eq(one.players[1].upkeepCompensation100, 200, "garrison subsidy capped");
eq(one.players[1].expenses100, 300, "actual unit expense still counted");
eq(one.players[0].distance100, 400, "distance reward apportioned by commerce");
eq(one.players[1].distance100, 200, "partner receives distance share");
eq(one.players[0].net100, 2420, "owner net profit");
eq(one.players[1].net100, 1140, "partner net profit");
eq(one.players[0].nativeAdjustment100, 1520, "native income is not paid twice");
local b = { id = "b", active = true, authorized = true, efficiency = 100,
    nativeGold100 = { [0] = 1000, [1] = 500 }, efficientDistance = 30, assets = { "road", "station", "guard" } };
local two = E.Settle({a,b}, assets);
eq(two.players[0].upkeepCompensation100, 100, "shared road reimbursed once across routes");
eq(two.players[1].upkeepCompensation100, 200, "shared garrison reimbursed once across routes");
eq(two.players[0].expenses100, 100, "shared expense counted once");
eq(two.players[0].dividend100, 25, "second route increases dividend by 25 percent");
local reverse = E.Settle({b,a}, assets);
eq(reverse.routes.a.payments100[0], two.routes.a.payments100[0], "input ordering cannot change rounding allocation");
local poor = E.Settle({ { id = "poor", active = true, authorized = true, efficiency = 20,
    nativeGold100 = a.nativeGold100, efficientDistance = 30, assets = a.assets } }, assets);
eq(poor.players[0].payment100, one.players[0].payment100 / 5, "80 percent penalty applies to entire payout");
eq(poor.players[1].expenses100, 300, "penalties do not erase actual expenses");
eq(E.Settle({a}, assets).players[0].dividend100, 20, "successive settlements retain return indefinitely");
b.active = false;
eq(E.Settle({a,b}, assets).players[0].dividend100, 20, "idle routes earn no traffic dividend");
a.active = false;
eq(next(E.Settle({a,b}, assets).players), nil, "idle network receives no payment"); a.active = true;
assets.road.owner = 2;
local transit = E.Settle({a}, assets);
eq(transit.players[2].payment100, 120, "transit contributor receives infrastructure payment");
eq(transit.players[0].upkeepCompensation100, 0, "origin cannot claim another player's infrastructure");
a.efficientDistance = 500;
local capped = E.Settle({a}, assets);
eq(capped.players[0].distance100 + capped.players[1].distance100, 799, "distance reward capped and conservatively rounded");
a.authorized = false;
eq(pcall(E.Settle, {a}, assets), false, "unauthorized active trade rejected"); a.authorized = true;
eq(pcall(E.Settle, {a,a}, assets), false, "duplicate route ID rejected");
print("Trade economy: " .. count .. " assertions passed");
