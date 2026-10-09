-- Pure route rules. Costs are hundredths of a native range point (a road edge
-- costs 50, a normal land edge 100). The adapter supplies current map facts.
RT_TradeRules = {};
local R = RT_TradeRules;

function R.Access(owner, origin, agreements)
    return owner < 0 or owner == origin or agreements[owner] == true;
end

function R.Inspect(path, options)
    if options.international and not options.destinationAgreement then
        return { valid = false, reason = "Trade agreement required" };
    end
    local result = { valid = true, cost = 0, range = options.baseRange * 100,
        relays = 0, roads = true, relief = true, hasStation = false, usedStations = {} };
    local seen = {};
    for i, tile in ipairs(path) do
        if seen[tile.id] then return { valid = false, reason = "Route contains a loop" }; end
        seen[tile.id] = true;
        if not R.Access(tile.owner, options.origin, options.agreements) then
            return { valid = false, reason = "Transit agreement required" };
        end
        if options.land then
            if tile.owner < 0 and not tile.road and not options.logistics and not options.roadIndependent and not tile.city then
                return { valid = false, reason = "Unclaimed land needs roads before Caravan Logistics" };
            end
            if not tile.road and not tile.city then result.roads = false; end
            if tile.hazard and not tile.relief then result.relief = false; end
            if tile.hazard and tile.reliefStation and not options.roadIndependent then result.usedStations[tile.reliefStation] = true; end
            if tile.station then
                result.hasStation = true;
                -- A motorized convoy uses this stop for commercial servicing,
                -- even when it needs no environmental relief or extra range.
                if options.roadIndependent then result.usedStations[tile.id] = true; end
            end
        end
        if i > 1 then result.cost = result.cost + tile.stepCost; end
        if result.cost > result.range + 99 then
            return { valid = false, reason = "Beyond trade range", cost = result.cost, range = result.range };
        end
        if options.land and tile.station and result.relays < 2 then
            result.relays = result.relays + 1; result.range = result.range + 500;
            result.usedStations[tile.id] = true;
        end
    end
    -- Motorized capability removes environmental penalties, not the economic
    -- cost of operating without roads and a supplied Caravansary stop.
    result.roadIndependent = options.land and options.roadIndependent or false;
    result.roadPenalty = result.roads and 0 or 40;
    result.reliefPenalty = (result.relief or result.roadIndependent) and 0 or 40;
    result.stationPenalty = result.roadIndependent and not result.hasStation and 40 or 0;
    result.efficiency = 100 - result.roadPenalty - result.reliefPenalty - result.stationPenalty;
    -- The motorized infrastructure deductions apply to gold only. Ordinary
    -- caravan cargo retains its existing infrastructure efficiency rules.
    result.cargoEfficiency = result.roadIndependent and 100 or result.efficiency;
    return result;
end

-- Small binary heap for pathfinding; stable tile IDs break ties deterministically.
function R.Path(start, goal, neighbors, valid, cost, maxCost)
    local dist, previous, heap = { [start] = 0 }, {}, {};
    local function less(a, b) return a.cost < b.cost or (a.cost == b.cost and a.id < b.id); end
    local function push(id, value)
        local entry = { id = id, cost = value }; local n = #heap + 1;
        while n > 1 do local parent = math.floor(n / 2); if not less(entry, heap[parent]) then break; end
            heap[n] = heap[parent]; n = parent; end
        heap[n] = entry;
    end
    local function pop()
        local first, last = heap[1], table.remove(heap);
        if #heap > 0 then
            local n = 1;
            while n * 2 <= #heap do
                local child = n * 2;
                if child < #heap and less(heap[child + 1], heap[child]) then child = child + 1; end
                if not less(heap[child], last) then break; end
                heap[n] = heap[child]; n = child;
            end
            heap[n] = last;
        end
        return first;
    end
    push(start, 0);
    while #heap > 0 do
        local current = pop();
        if current.cost == dist[current.id] then
            if current.id == goal then
                local path, id = {}, goal;
                while id do table.insert(path, 1, id); id = previous[id]; end
                return path, current.cost;
            end
            for _, id in ipairs(neighbors(current.id)) do
                if valid(id) then
                    local value = current.cost + cost(current.id, id);
                    if value <= maxCost and (not dist[id] or value < dist[id]) then
                        dist[id] = value; previous[id] = current.id; push(id, value);
                    end
                end
            end
        end
    end
    return nil;
end
