#ifndef C5M_HOST_H
#define C5M_HOST_H

namespace Database { class Connection; }
struct lua_State;

namespace C5M {
bool ConfigureDatabase(Database::Connection& database);
void RegisterLuaMembers(lua_State* state);
}
#endif
