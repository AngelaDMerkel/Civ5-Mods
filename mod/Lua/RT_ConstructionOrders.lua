-- Persistent Caravansary and irrigation orders. Native progress is the source of
-- truth; saved orders only remember who is assigned and prevent repeat work.
RT_ConstructionOrders = {};
local O, B = RT_ConstructionOrders, RT_Construction;
local saved = Modding.OpenSaveData();
local PREFIX = "RealisticTerrain.v1.Construction.";
local rosters = {};

local function identity(unit)
    return unit:GetGameTurnCreated() .. "," .. unit:GetOriginalOwner() .. "," .. unit:GetUnitType();
end

local function load(playerID)
    if rosters[playerID] then return rosters[playerID]; end
    local jobs = {};
    local record = saved:GetValue(PREFIX .. playerID) or "";
    for entry in string.gmatch(record, "[^;]+") do
        local base, construction = string.match(entry, "^(.-),([a-z]+)$");
        local id, birth, owner, kind, x, y = string.match(base or entry, "^(%d+),(%d+),(%d+),(%d+),(%d+),(%d+)$");
        if id and (not construction or construction == "station" or construction == "irrigation") then
            jobs[tonumber(id)] = { identity = birth .. "," .. owner .. "," .. kind,
                x = tonumber(x), y = tonumber(y), kind = construction or "station" }; end
    end
    rosters[playerID] = jobs;
    return jobs;
end

local function flush(playerID)
    local jobs, ids, encoded = load(playerID), {}, {};
    for id in pairs(jobs) do ids[#ids + 1] = id; end
    table.sort(ids);
    for _, id in ipairs(ids) do
        local job = jobs[id];
        encoded[#encoded + 1] = id .. "," .. job.identity .. "," .. job.x .. "," .. job.y .. "," .. (job.kind or "station");
    end
    saved:SetValue(PREFIX .. playerID, table.concat(encoded, ";"));
end

local function stampKey(unit)
    return PREFIX .. "Last." .. unit:GetOwner() .. "." .. unit:GetID();
end

local function stamp(unit)
    return identity(unit) .. "," .. Game.GetGameTurn();
end

function O.HasWorked(unit) return saved:GetValue(stampKey(unit)) == stamp(unit); end

function O.IsOrdered(unit, kind)
    if not B.IsWorker(unit) then return false; end
    local job = load(unit:GetOwner())[unit:GetID()];
    local plot = unit:GetPlot();
    return job ~= nil and job.identity == identity(unit) and plot ~= nil
        and job.x == plot:GetX() and job.y == plot:GetY() and (not kind or job.kind == kind);
end

function O.Cancel(unit)
    if not unit then return; end
    load(unit:GetOwner())[unit:GetID()] = nil;
    flush(unit:GetOwner());
end

local function advance(unit)
    if saved:GetValue(stampKey(unit)) == stamp(unit) then return false; end
    if RT_OutpostBridge and RT_OutpostBridge.OtherOrder(unit, "worked") then return false; end
    local kind = load(unit:GetOwner())[unit:GetID()].kind;
    local allowed = B.Status(unit, true, kind);
    if not allowed then return false; end
    -- Save the guard before any engine mutation that may trigger callbacks.
    saved:SetValue(stampKey(unit), stamp(unit));
    local worked, finished = B.Work(unit, true, kind);
    if finished then O.Cancel(unit); end
    return worked;
end

function O.Start(unit, kind, scheduled)
    kind = kind or "station";
    if kind ~= "station" and kind ~= "irrigation" then return false; end
    local allowed = B.Status(unit, scheduled, kind);
    if not allowed or saved:GetValue(stampKey(unit)) == stamp(unit) then return false; end
    if RT_OutpostBridge then
        if RT_OutpostBridge.OtherOrder(unit, "worked") then return false; end
        RT_OutpostBridge.OtherOrder(unit, "cancel");
    end
    local plot = unit:GetPlot();
    load(unit:GetOwner())[unit:GetID()] = { identity = identity(unit), x = plot:GetX(), y = plot:GetY(), kind = kind };
    flush(unit:GetOwner());
    return advance(unit);
end

function O.Toggle(unit, kind)
    if not unit or unit:GetOwner() ~= Game.GetActivePlayer()
        or not Players[unit:GetOwner()]:IsTurnActive() then return false; end
    if O.IsOrdered(unit, kind or "station") then O.Cancel(unit); return true; end
    return O.Start(unit, kind);
end

function O.OnTurn(playerID)
    local player = Players[playerID];
    if not player or not player:IsAlive() then return; end
    local jobs, ids = load(playerID), {};
    for id in pairs(jobs) do ids[#ids + 1] = id; end
    table.sort(ids);
    for _, id in ipairs(ids) do
        local unit = player:GetUnitByID(id);
        if not O.IsOrdered(unit) or unit:IsAutomated() or unit:GetBuildType() ~= -1 then
            jobs[id] = nil; -- death, conversion, movement or a replacement order
        else
            local _, reason = B.Status(unit, true, jobs[id].kind);
            if reason == "TXT_KEY_RT_BUILD_PLOT" or reason == "TXT_KEY_RT_IRRIGATION_PLOT" then jobs[id] = nil;
            else advance(unit); end -- missing building/water/tech/movement pauses work
        end
    end
    flush(playerID);
    if O.OnChanged then O.OnChanged(); end
end

function O.OnMoved(playerID, unitID)
    local jobs = load(playerID);
    if not jobs[unitID] then return; end
    local player = Players[playerID];
    local unit = player and player:GetUnitByID(unitID);
    if not O.IsOrdered(unit) then jobs[unitID] = nil; flush(playerID); end
end

function O.Initialize()
    GameEvents.PlayerDoTurn.Add(O.OnTurn);
    GameEvents.UnitSetXY.Add(O.OnMoved);
    -- Some game versions refresh unit movement after PlayerDoTurn. This second
    -- opportunity is guarded by the persisted per-unit/turn work stamp.
    Events.ActivePlayerTurnStart.Add(function() O.OnTurn(Game.GetActivePlayer()); end);
end
