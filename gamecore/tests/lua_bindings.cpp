// Test entry points only. Never linked into the GameCore.
#include "C5M_CoreContext.h"
#include "C5M_Host.h"
extern "C" {
#include <lua.h>
}

extern "C" int c5m_test_register(lua_State* L) {
    lua_newtable(L);
    lua_pushinteger(L, 42);
    lua_setfield(L, -2, "ExistingMember");
    const int before = lua_gettop(L);
    C5M::RegisterLuaMembers(L);
    if (lua_gettop(L) != before) return 0;
    C5M::RegisterLuaMembers(L);
    if (lua_gettop(L) != before) return 0;
    lua_setglobal(L, "Game");
    return 1;
}

extern "C" int c5m_test_configure(int unsupported) {
    C5M::Core().Reset();
    std::vector<C5M::Requirement> requests;
    if (unsupported) requests.push_back(C5M::Requirement("terrain.native-trade", 1));
    return C5M::Core().Configure(requests) && C5M::Core().Freeze();
}
