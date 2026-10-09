-- Pure rules: no game globals. Also executed by the Lua 5.1 test suite.
RT_Rules = {};
local R = RT_Rules;
R.HAZARDS = { "heat", "cold", "jungle" };

function R.NewState()
    return { heat = 0, cold = 0, jungle = 0, coldGrace = 3, lastTurn = -1, stage = 0 };
end

function R.Copy(state)
    local result = {};
    for k, v in pairs(state) do result[k] = v; end
    return result;
end

function R.Reset(state)
    for _, hazard in ipairs(R.HAZARDS) do state[hazard] = 0; end
    state.stage = 0;
end

function R.Stage(state, grace, config)
    local worst = 0;
    for _, hazard in ipairs(R.HAZARDS) do
        local excess = state[hazard] - grace[hazard];
        local stage = excess > config.STRAINED_TURNS and 2 or (excess > 0 and 1 or 0);
        worst = math.max(worst, stage);
    end
    return worst;
end

-- Called once at the start of the owner's turn for the tile occupied overnight.
-- env: safe, paused, hazard, rate, water. Grace already includes support bonuses.
function R.Advance(previous, env, grace, config, turn)
    local state = R.Copy(previous);
    if state.lastTurn == turn then return state, false; end
    state.lastTurn = turn;
    if env.safe then
        R.Reset(state);
    elseif not env.paused then
        if env.water then state.heat = 0; end
        if env.hazard then
            local hazard = env.hazard;
            state[hazard] = math.min(config.MAX_EXPOSURE, state[hazard] + (env.rate or 1));
            if hazard == "cold" then state.coldGrace = env.coldBase or config.GRACE.cold; end
            -- Other counters are retained while moving between hostile climates.
        else
            for _, hazard in ipairs(R.HAZARDS) do
                state[hazard] = math.max(0, state[hazard] - config.RECOVERY_PER_TURN);
            end
        end
        state.stage = R.Stage(state, grace, config);
    end
    return state, true;
end

function R.Damage(stage, damage, maxHP, config, paused)
    if paused or stage < 2 then return 0; end
    local floorHP = math.ceil(maxHP * config.MIN_HP_PERCENT / 100);
    return math.max(0, math.min(config.DAMAGE_PER_TURN, maxHP - floorHP - damage));
end

-- Decimal counters preserve half-turn cold exposure in forested tundra.
function R.Encode(s)
    return table.concat({ 1, s.birth, s.unitType, s.originalOwner, s.lastTurn,
        s.heat, s.cold, s.jungle, s.coldGrace, s.stage, s.x, s.y }, "|");
end

function R.Decode(value)
    if type(value) ~= "string" then return nil; end
    local fields = {};
    for part in string.gmatch(value, "[^|]+") do
        local number = tonumber(part);
        if not number or number ~= number or math.abs(number) == math.huge then return nil; end
        fields[#fields + 1] = number;
    end
    if #fields ~= 12 or fields[1] ~= 1 then return nil; end
    return { birth = fields[2], unitType = fields[3], originalOwner = fields[4],
        lastTurn = fields[5], heat = math.max(0, fields[6]), cold = math.max(0, fields[7]),
        jungle = math.max(0, fields[8]), coldGrace = fields[9], stage = fields[10],
        x = fields[11], y = fields[12] };
end
