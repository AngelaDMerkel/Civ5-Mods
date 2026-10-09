-- Enforce the Ministry gate on actual construction, not only on button visibility.
local count = 0;
local function eq(actual, expected, label)
    count = count + 1;
    assert(actual == expected, label .. ": expected " .. tostring(expected) .. ", got " .. tostring(actual));
end
GameInfoTypes = { BUILD_RT_RELIEF_STATION = 10, BUILDING_CARAVANSARY = 20,
    TECH_ENGINEERING = 30, TECH_BRONZE_WORKING = 31, UNIT_WORKER = 40, FEATURE_JUNGLE = 50 };
local I = GameInfoTypes;
local function rows(list)
    return function() local n = 0; return function() n = n + 1; return list[n]; end; end;
end
GameInfo = {
    Builds = { [10] = { Type = "BUILD_RT_RELIEF_STATION", PrereqTech = "TECH_ENGINEERING" } },
    Unit_Builds = rows({ { UnitType = "UNIT_WORKER" } }),
    BuildFeatures = rows({ { FeatureType = "FEATURE_JUNGLE", PrereqTech = "TECH_BRONZE_WORKING" } }),
};
DomainTypes = { DOMAIN_LAND = 0 };
local active = 0;
Game = { GetActivePlayer = function() return active; end };
local techs = {};
Teams = { [7] = { GetTeamTechs = function() return {
    HasTech = function(_, id) return techs[id] or false; end,
}; end } };
local player = { ministry = 0, active = true };
function player:IsTurnActive() return self.active; end
function player:CountNumBuildings(id) assert(id == 20); return self.ministry; end
function player:GetTeam() return 7; end -- ensure build progress receives player, not team
Players = { [0] = player, [1] = player };
local p = { owner = -1, progress = 0, total = 300, valid = true, feature = -1, units = {} };
function p:GetOwner() return self.owner; end
function p:IsWater() return self.water or false; end
function p:IsMountain() return self.mountain or false; end
function p:CanBuild(id, owner, visible, testOwner)
    assert(id == 10 and owner == 0 and not visible and testOwner);
    return self.valid and self.improvement ~= 99;
end
function p:GetFeatureType() return self.feature; end
function p:GetBuildProgress(id) assert(id == 10); return self.progress; end
function p:GetBuildTime(id, owner) assert(id == 10 and owner == 0); return self.total; end
function p:ChangeBuildProgress(id, rate, owner)
    assert(id == 10 and owner == 0);
    self.progress = self.progress + rate;
    if self.progress >= self.total then self.improvement = 99; self.progress = 0; return true; end
    return false;
end
function p:GetImprovementType() return self.improvement or -1; end
function p:GetX() return 4; end
function p:GetY() return 5; end
function p:GetNumUnits() return #self.units; end
function p:GetUnit(i) return self.units[i + 1]; end
local worker = { owner = 0, unitType = 40, moves = 120, rate = 100, domain = 0, build = -1 };
function worker:GetOwner() return self.owner; end
function worker:GetUnitType() return self.unitType; end
function worker:GetDomainType() return self.domain; end
function worker:IsDelayedDeath() return self.dead or false; end
function worker:GetPlot() return p; end
function worker:IsEmbarked() return self.embarked or false; end
function worker:IsAutomated() return self.automated or false; end
function worker:IsBusy() return self.busy or false; end
function worker:GetBuildType() return self.build; end
function worker:GetMoves() return self.moves; end
function worker:WorkRate(max) return (max or self.moves > 0) and self.rate or 0; end
function worker:FinishMoves() self.moves = 0; end
p.units = { worker };
local builderRecords = 0;
RT_Supply = { OnBuildFinished = function(owner, x, y, improvement)
    assert(owner == 0 and x == 4 and y == 5 and improvement == 99);
    builderRecords = builderRecords + 1;
end };
dofile(TEST_ROOT .. "/mod/Lua/RT_Construction.lua");
local B = RT_Construction;
local function blocked(reason)
    local progress, moves = p.progress, worker.moves;
    local ok, key = B.Status(worker);
    eq(ok, false, "action blocked"); eq(key, reason, "explanation");
    eq(B.Work(worker), false, "action itself enforces gate");
    eq(p.progress, progress, "rejected action preserves progress");
    eq(worker.moves, moves, "rejected action preserves movement");
end
eq(B.Work(nil), false, "stale selection safe");
blocked("TXT_KEY_RT_BUILD_MINISTRY");
techs[30] = true; blocked("TXT_KEY_RT_BUILD_MINISTRY");
player.ministry = 1; techs[30] = nil; blocked("TXT_KEY_RT_BUILD_TECH");
techs[30] = true;
active = 1; blocked("TXT_KEY_RT_BUILD_TURN"); active = 0;
player.active = false; blocked("TXT_KEY_RT_BUILD_TURN"); player.active = true;
worker.dead = true; blocked("TXT_KEY_RT_BUILD_WORKER"); worker.dead = false;
worker.unitType = 41; blocked("TXT_KEY_RT_BUILD_WORKER"); worker.unitType = 40;
worker.domain = 1; blocked("TXT_KEY_RT_BUILD_WORKER"); worker.domain = 0;
worker.embarked = true; blocked("TXT_KEY_RT_BUILD_PLOT"); worker.embarked = false;
p.owner = 1; blocked("TXT_KEY_RT_BUILD_PLOT"); p.owner = -1;
p.water = true; blocked("TXT_KEY_RT_BUILD_PLOT"); p.water = false;
p.mountain = true; blocked("TXT_KEY_RT_BUILD_PLOT"); p.mountain = false;
p.valid = false; blocked("TXT_KEY_RT_BUILD_PLOT"); p.valid = true;
p.feature = 50; blocked("TXT_KEY_RT_BUILD_FEATURE_TECH"); techs[31] = true;
worker.automated = true; blocked("TXT_KEY_RT_BUILD_BUSY"); worker.automated = false;
worker.busy = true; blocked("TXT_KEY_RT_BUILD_BUSY"); worker.busy = false;
worker.build = 11; blocked("TXT_KEY_RT_BUILD_BUSY"); worker.build = -1;
p.units[2] = { GetBuildType = function() return 11; end }; blocked("TXT_KEY_RT_BUILD_BUSY"); p.units[2] = nil;
worker.moves = 0; blocked("TXT_KEY_RT_BUILD_MOVES"); worker.moves = 120;
worker.rate = 0; blocked("TXT_KEY_RT_BUILD_MOVES"); worker.rate = 100;
local allowed, finished = B.Work(worker);
eq(allowed, true, "Ministry permits construction"); eq(finished, false, "construction takes time");
eq(p.progress, 100, "one worker turn applied"); eq(worker.moves, 0, "movement consumed");
eq(builderRecords, 0, "unfinished site not an outpost");
blocked("TXT_KEY_RT_BUILD_MOVES");
-- Native progress survives a Lua context reload. Losing the Ministry stops work.
dofile(TEST_ROOT .. "/mod/Lua/RT_Construction.lua"); B = RT_Construction;
worker.moves = 120; player.ministry = 0; blocked("TXT_KEY_RT_BUILD_MINISTRY");
player.ministry = 1; worker.rate = 200; worker.moves = 1;
local done, total = B.Progress(worker);
eq(done, 100, "partial construction survives reload"); eq(total, 300, "uses native required work");
allowed, finished = B.Work(worker);
eq(allowed, true, "rebuilding Ministry resumes work"); eq(finished, true, "worker speed bonus respected");
eq(worker.moves, 0, "partly moved worker spends remaining movement");
eq(p.improvement, 99, "native completion creates improvement");
eq(builderRecords, 1, "neutral builder recorded once");
worker.moves = 120; blocked("TXT_KEY_RT_BUILD_PLOT");
player.ministry = 0;
eq(p.improvement, 99, "losing Ministry leaves existing outpost intact");
print("Caravansary construction: " .. count .. " assertions passed");

-- One-click orders persist, resume automatically, and never contribute twice.
local turn, values = 0, {};
Game.GetGameTurn = function() return turn; end;
Modding = { OpenSaveData = function() return {
    GetValue = function(_, key) return values[key]; end,
    SetValue = function(_, key, value) values[key] = value; end,
}; end };
function worker:GetID() return 1; end
function worker:GetGameTurnCreated() return self.birth or 0; end
function worker:GetOriginalOwner() return 0; end
function player:IsAlive() return true; end
function player:GetUnitByID(id) if id == 1 and not worker.dead then return worker; end end
local function resetSite()
    p.improvement, p.progress, p.total = nil, 0, 500;
    player.ministry, worker.moves, worker.rate = 1, 120, 100;
end
resetSite();
dofile(TEST_ROOT .. "/mod/Lua/RT_ConstructionOrders.lua");
local O = RT_ConstructionOrders;
eq(O.Start(worker), true, "one click starts an order");
eq(p.progress, 100, "starting order contributes work");
eq(O.IsOrdered(worker), true, "unfinished order saved");
turn = 1; worker.moves = 120; O.OnTurn(0);
eq(p.progress, 200, "next turn progresses automatically");
worker.moves = 120; O.OnTurn(0);
eq(p.progress, 200, "duplicate callback cannot repeat work");
dofile(TEST_ROOT .. "/mod/Lua/RT_ConstructionOrders.lua"); O = RT_ConstructionOrders;
eq(O.IsOrdered(worker), true, "order survives context reload");
O.OnTurn(0); eq(p.progress, 200, "reload preserves processed-turn guard");
turn = 2; player.ministry = 0; O.OnTurn(0);
eq(p.progress, 200, "losing Ministry pauses the order");
eq(O.IsOrdered(worker), true, "paused order retained");
player.ministry = 1; O.OnTurn(0);
eq(p.progress, 300, "restored Ministry resumes order");
eq(O.Toggle(worker), true, "cancel allowed after spending movement");
eq(O.IsOrdered(worker), false, "cancel removes assignment");
worker.moves = 120; eq(O.Start(worker), false, "cancel and restart cannot double work");
turn = 3; O.OnTurn(0); eq(p.progress, 300, "cancelled order stays cancelled");
eq(O.Start(worker), true, "partial work can be resumed later");
turn = 4; worker.moves = 120; O.OnTurn(0);
eq(p.improvement, 99, "order completes natively");
eq(O.IsOrdered(worker), false, "finished order removed");
eq(builderRecords, 2, "completed order records builder");
resetSite(); turn = 5; O.Start(worker);
worker.automated = true; turn = 6; worker.moves = 120; O.OnTurn(0);
eq(O.IsOrdered(worker), false, "native automation replaces custom order");
eq(p.progress, 100, "replaced order adds no work"); worker.automated = false;
O.Start(worker); worker.dead = true; turn = 7; O.OnTurn(0); worker.dead = false;
eq(O.IsOrdered(worker), false, "dead worker pruned from orders");
worker.moves = 120; O.Start(worker); worker.birth = 3;
turn = 8; O.OnTurn(0); eq(O.IsOrdered(worker), false, "reused unit ID cannot inherit order");
worker.moves = 120; O.Start(worker);
local oldX = p.GetX; p.GetX = function() return 9; end;
O.OnMoved(0, 1); p.GetX = oldX;
eq(O.IsOrdered(worker), false, "moving away and returning cancels order");
print("Caravansary construction + persistent orders: " .. count .. " assertions passed");
