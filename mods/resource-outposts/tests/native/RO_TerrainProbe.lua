-- This append belongs only to the disposable Terrain UI copy. It exposes
-- read-only production observations across the real UI-context event bridge.
LuaEvents.RO_NativeTerrain.Add(function(q)
    local unit = Players[q.owner] and Players[q.owner]:GetUnitByID(q.unit);
    q.loaded = true;
    if unit then q.info = RT_Gameplay.Inspect(unit); end
end);
