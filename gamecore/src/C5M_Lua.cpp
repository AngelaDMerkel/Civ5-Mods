#include "../include/C5M_CoreContext.h"
#include "../include/C5M_Host.h"
extern "C" {
#include <lua.h>
#include <lauxlib.h>
}

namespace C5M {
namespace {
void StringField(lua_State* L, const char* name, const char* value) {
    lua_pushstring(L, value);
    lua_setfield(L, -2, name);
}

int GetCoreInfo(lua_State* L) {
    const CoreContext& core = Core();
    lua_createtable(L, 0, 7);
    StringField(L, "Version", CoreVersion());
    StringField(L, "Phase", core.PhaseName());
    StringField(L, "SelectionKey", core.Active().SelectionKey().c_str());
    StringField(L, "Error", core.Error().c_str());
    lua_pushinteger(L, 1);
    lua_setfield(L, -2, "APIVersion");
    lua_pushboolean(L, core.Ready());
    lua_setfield(L, -2, "Ready");
    lua_pushboolean(L, 0);
    lua_setfield(L, -2, "OwnsModSimulation");
    return 1;
}

int HasCapability(lua_State* L) {
    const char* id = luaL_checkstring(L, 1);
    const lua_Number version = luaL_checknumber(L, 2);
    // Do not truncate negative, fractional, NaN or out-of-range versions.
    if (!(version >= 1 && version <= 2147483647) ||
        version != static_cast<unsigned int>(version))
        return luaL_error(L, "C5M capability version must be a positive integer");
    lua_pushboolean(L, Core().Ready() && Core().Active().HasCapability(id, static_cast<unsigned int>(version)));
    return 1;
}

int GetModules(lua_State* L) {
    const std::vector<std::string>& modules = Core().Active().Order();
    lua_createtable(L, static_cast<int>(modules.size()), 0);
    for (size_t i = 0; i < modules.size(); ++i) {
        lua_pushstring(L, modules[i].c_str());
        lua_rawseti(L, -2, static_cast<int>(i + 1));
    }
    return 1;
}
}

void RegisterLuaMembers(lua_State* L) {
    // CvLuaGame owns the Game table already on the stack. Never replace it.
    lua_pushcfunction(L, GetCoreInfo);
    lua_setfield(L, -2, "C5MGetCoreInfo");
    lua_pushcfunction(L, HasCapability);
    lua_setfield(L, -2, "C5MHasCapability");
    lua_pushcfunction(L, GetModules);
    lua_setfield(L, -2, "C5MGetModules");
}
}
