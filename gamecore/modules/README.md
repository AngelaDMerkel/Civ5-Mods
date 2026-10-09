# Native feature ownership

These directories reserve native implementations for the four existing owners:

| Directory | Implementation contract |
| --- | --- |
| `realistic-terrain/` | Genuine native trade and logistics; see the Terrain native trade contract. |
| `resource-outposts/` | Only engine hooks required by confirmed Outpost rules; claims/upkeep/AI remain with its Lua owner. |
| `irrigated-farm/` | Narrow native services if required; preserve existing connectivity, identifiers and Terrain packaging. |
| `climate-change/` | Terrain mutation/cache refresh research; graphics refresh and climate rules require further implementation and acceptance. |

No gameplay provider is registered in version 0.1.0. `C5M_CoreContext.cpp` registers
only `c5m.core`, with the implemented `c5m.core-introspection` capability. Requests
for unfinished modules fail. Do not add a descriptor just to make a request pass.

For each future provider: implement its typed engine service here, add it to the
single platform build, register its exact-version capability in the common
catalog, add the necessary small engine call sites, and implement its state/save
contract before allowing activation. Content selects compiled modules through
`C5M_EnabledModules`; it cannot load another DLL or register C++ implementations.
One binary serves all tested combinations. Never switch a simulation from Lua to
native merely because the shared core is installed.
