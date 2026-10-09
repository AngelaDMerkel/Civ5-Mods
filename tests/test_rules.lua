local R, C = RT_Rules, RT_Config;
local count = 0;
local function eq(actual, expected, message)
    count = count + 1;
    assert(actual == expected, (message or "assertion") .. ": expected " .. tostring(expected) .. ", got " .. tostring(actual));
end
local function grace(cold) return { heat = 2, cold = cold or 3, jungle = 4 }; end
local function tick(s, env, g, turn) return R.Advance(s, env, g or grace(), C, turn or s.lastTurn + 1); end

local s = R.NewState();
local desert = { hazard = "heat" };
for turn = 1, 2 do s = tick(s, desert); eq(s.stage, 0, "desert grace"); end
for turn = 3, 4 do s = tick(s, desert); eq(s.stage, 1, "desert strain"); end
s = tick(s, desert); eq(s.stage, 2, "desert exhaustion");
local duplicate, advanced = tick(s, desert, nil, s.lastTurn);
eq(duplicate.heat, s.heat, "duplicate callback"); eq(advanced, false);
eq(R.Damage(2, 0, 100, C, false), 5, "damage starts");
eq(R.Damage(2, 73, 100, C, false), 2, "damage clamp");
eq(R.Damage(2, 80, 100, C, false), 0, "never heal wounded unit");
eq(R.Damage(2, 145, 200, C, false), 5, "nonstandard maximum HP");
eq(R.Damage(2, 7, 10, C, false), 0, "ceil health floor");
eq(R.Damage(1, 0, 100, C, false), 0, "strained no damage");
eq(R.Damage(2, 0, 100, C, true), 0, "embarked no damage");

local copy = tick(s, { safe = true });
eq(copy.heat, 0, "home clears"); eq(copy.stage, 0); eq(s.heat, 5, "rules do not mutate input");
copy = tick(s, { water = true }); eq(copy.heat, 0, "oasis reset");
copy = tick(s, { paused = true }); eq(copy.heat, 5, "embarked retains exposure");
copy = tick(s, {}); eq(copy.heat, 3, "safe recovery"); eq(copy.stage, 1);
copy = tick(copy, {}); eq(copy.heat, 1); eq(copy.stage, 0);
copy = tick(s, { hazard = "jungle" }); eq(copy.heat, 5, "changing climate retains old counter"); eq(copy.jungle, 1);
copy.jungle = 9;
copy = tick(copy, { water = true, hazard = "jungle" });
eq(copy.heat, 0); eq(copy.jungle, 10, "water does not cure jungle exposure"); eq(copy.stage, 2);

s = R.NewState();
for turn = 1, 3 do s = tick(s, { hazard = "cold", coldBase = 3 }); eq(s.stage, 0, "tundra grace"); end
s = tick(s, { hazard = "cold", coldBase = 3 }); eq(s.stage, 1);
s = R.NewState();
s = tick(s, { hazard = "cold", coldBase = 1 }, grace(1)); eq(s.stage, 0, "snow grace");
s = tick(s, { hazard = "cold", coldBase = 1 }, grace(1)); eq(s.stage, 1); eq(s.coldGrace, 1);
s = tick(s, { hazard = "cold", coldBase = 1 }, grace(1)); eq(s.stage, 1);
s = tick(s, { hazard = "cold", coldBase = 1 }, grace(1)); eq(s.stage, 2);
s = R.NewState();
for turn = 1, 6 do s = tick(s, { hazard = "cold", rate = 0.5 }, grace()); eq(s.stage, 0, "forest shelter"); end
s = tick(s, { hazard = "cold", rate = 0.5 }); eq(s.stage, 1);
s = R.NewState();
for turn = 1, 4 do s = tick(s, { hazard = "jungle" }); eq(s.stage, 0, "jungle grace"); end
s = tick(s, { hazard = "jungle" }); eq(s.stage, 1);
for turn = 1, 100 do s = tick(s, { hazard = "jungle" }); end
eq(s.jungle, C.MAX_EXPOSURE, "bounded counters");
s.birth, s.unitType, s.originalOwner, s.x, s.y = 4, 12, 0, 10, 11;
local decoded = R.Decode(R.Encode(s));
for k, v in pairs(s) do eq(decoded[k], v, "save round trip " .. k); end
eq(R.Decode("bad"), nil); eq(R.Decode(nil), nil); eq(R.Decode("2|4|12|0|10|0|0|0|3|0|1|1"), nil);
print("Rules: " .. count .. " assertions passed");
