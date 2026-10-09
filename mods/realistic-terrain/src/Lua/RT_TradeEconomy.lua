-- Engine-independent trade settlement in hundredths of gold. The adapter must
-- supply actual authorized routes and the infrastructure each route uses.
-- This module does not mutate the game or infer routes from city proximity.
RT_TradeEconomy = {};
local E = RT_TradeEconomy;
E.DEFAULTS = {
    commercialPercent = 200,
    distanceGold100 = 20, maxDistance = 40,
    dividendBasisPoints = 200, -- 2% of standardized capital per active turn
    extraRouteDividendPercent = 25, maxDividendPercent = 200,
    garrisonUpkeepCap100 = 200,
};

local function amount(value)
    assert(type(value) == "number" and value >= 0 and value == math.floor(value), "Expected nonnegative integer");
    return value;
end

local function sortedKeys(t)
    local keys = {}; for key in pairs(t) do keys[#keys + 1] = key; end
    table.sort(keys); return keys;
end

local function split(total, count, index)
    -- Deterministic remainder allocation conserves every hundredth of gold.
    return math.floor(total / count) + (index <= total % count and 1 or 0);
end

function E.Efficiency(continuousRoad, adequateRelief)
    return 100 - (continuousRoad and 0 or 40) - (adequateRelief and 0 or 40);
end

function E.Settle(routes, assets, config)
    local C = config or E.DEFAULTS;
    local result = { players = {}, routes = {}, assets = {} };
    local usage, seenRoutes = {}, {};
    local function account(playerID)
        assert(type(playerID) == "number" and playerID >= 0, "Invalid infrastructure owner");
        if not result.players[playerID] then
            result.players[playerID] = { payment100 = 0, nativeGold100 = 0, expenses100 = 0,
                upkeepCompensation100 = 0, dividend100 = 0, commercial100 = 0, distance100 = 0 };
        end
        return result.players[playerID];
    end
    local function pay(route, owner, field, gross)
        local paid = math.floor(gross * route.efficiency / 100);
        local p = account(owner);
        p[field] = p[field] + paid; p.payment100 = p.payment100 + paid;
        local r = result.routes[route.id];
        r.payments100[owner] = (r.payments100[owner] or 0) + paid;
    end
    for _, route in ipairs(routes) do
        assert(type(route.id) == "string" and not seenRoutes[route.id], "Duplicate/invalid route ID");
        seenRoutes[route.id] = true;
        -- Inactive routes incur no economic commitment in this trade ledger.
        -- Their abandoned infrastructure still costs the owner in the game.
        if route.active then
            assert(route.authorized, "Cannot settle an unauthorized active route");
            assert(route.efficiency == 100 or route.efficiency == 60 or route.efficiency == 20,
                "Invalid infrastructure efficiency");
            result.routes[route.id] = { efficiency = route.efficiency, payments100 = {} };
            local owners = sortedKeys(route.nativeGold100);
            local nativeTotal = 0;
            for _, owner in ipairs(owners) do nativeTotal = nativeTotal + amount(route.nativeGold100[owner]); end
            local distanceBonus = math.min(amount(route.efficientDistance), C.maxDistance) * C.distanceGold100;
            for i, owner in ipairs(owners) do
                local native = route.nativeGold100[owner];
                local p = account(owner); p.nativeGold100 = p.nativeGold100 + native;
                pay(route, owner, "commercial100", math.floor(native * C.commercialPercent / 100));
                -- Divide one route's distance reward, rather than granting it
                -- in full to every participant or paying for artificial detours.
                local share = nativeTotal > 0 and math.floor(distanceBonus * native / nativeTotal)
                    or split(distanceBonus, #owners, i);
                pay(route, owner, "distance100", share);
            end
            local seenAssets = {};
            for _, id in ipairs(route.assets) do
                assert(assets[id], "Unknown infrastructure asset: " .. tostring(id));
                if not seenAssets[id] then
                    seenAssets[id] = true;
                    usage[id] = usage[id] or {};
                    usage[id][#usage[id] + 1] = route;
                end
            end
        end
    end
    for _, id in ipairs(sortedKeys(usage)) do
        local asset, users = assets[id], usage[id];
        table.sort(users, function(a, b) return a.id < b.id; end);
        assert(asset.kind == "road" or asset.kind == "railroad" or asset.kind == "caravansary"
            or asset.kind == "garrison", "Invalid asset kind");
        local expense = amount(asset.upkeep100);
        local capital = amount(asset.standardCapital100);
        local eligible = expense;
        if asset.kind == "garrison" then eligible = math.min(expense, C.garrisonUpkeepCap100); capital = 0; end
        local trafficPercent = math.min(C.maxDividendPercent, 100 + (#users - 1) * C.extraRouteDividendPercent);
        -- No repayment deadline, construction date, route start date, or reset
        -- bonus. The same useful asset earns on every active trade turn.
        local dividend = math.floor(capital * C.dividendBasisPoints * trafficPercent / 1000000);
        account(asset.owner).expenses100 = account(asset.owner).expenses100 + expense;
        result.assets[id] = { uses = #users, eligibleUpkeep100 = eligible, dividendBeforePenalty100 = dividend };
        for index, route in ipairs(users) do
            pay(route, asset.owner, "upkeepCompensation100", split(eligible, #users, index));
            pay(route, asset.owner, "dividend100", split(dividend, #users, index));
        end
    end
    for _, p in pairs(result.players) do
        -- A native-route adapter pays this delta, NOT payment100 on top of
        -- native income. A replacement-route engine pays payment100 directly.
        p.nativeAdjustment100 = p.payment100 - p.nativeGold100;
        p.net100 = p.payment100 - p.expenses100;
    end
    return result;
end
