# One GameCore, optional mod features

Confirmed user direction, 2026-10-09: develop one project-owned GameCore for the
four repository mods, initially excluding Lekmod/Vox Populi gameplay integration.
Build on the existing gameplay and Mac porting work. WSDLC remains optional.
This supersedes the earlier assumption that native support belongs exclusively
inside Terrain. Terrain's native trade requirements still apply.

## Architecture

Maintain one BNW-derived gameplay source base and one compiled core release per
supported platform/game ABI. Compile supported native modules into that core;
activate only the capabilities requested by the selected native content edition.
The same binary can serve Terrain alone, Outposts alone, or supported combinations.
An unrelated disabled mod must not change gameplay or require its database rows.

```text
BNW gameplay + existing Mac compatibility work
                  |
       Shared core and versioned services
                  |
       +----------+----------+----------+
       |          |          |          |
     Terrain   Outposts   Irrigation   Climate
       |          |          |          |
     Separate Lua/SQL/UI/art content and optional integrations
```

This is modular **source and runtime feature selection**. It is not stacking
multiple GameCore DLLs/dylibs, nor loading arbitrary C++ plugins while a game runs.
The [existing Mac coordinator](https://github.com/AngelaDMerkel/civ5-macos-coordinator)
documents the single-active-core boundary. Database-selected compiled features
and script hooks have a precedent in
[Community Patch's CustomMods implementation](https://github.com/LoneGazebo/Community-Patch-DLL/blob/master/CvGameCoreDLL_Expansion2/CustomMods.cpp);
that is an architectural reference, not a VP gameplay dependency.

## When a new build is required

| Change | Shared core rebuild? |
| --- | --- |
| Enable/disable an already-supported mod before a new game | No |
| Change supported Lua/SQL balance, art, text or UI | Normally no; respect content/API contracts |
| Add a feature expressed entirely through existing core services | No |
| Add a new C++ hook, path rule, engine-owned state or native capability | Yes, one updated shared release per target platform |
| Combine already-supported modules | No separate binary for the combination; integration testing still required |
| Integrate an unrelated overhaul's replacement GameCore | Deliberate source integration and compatible build required; outside initial scope |

A custom binary plugin loader is possible engineering work, but introduces a
second ABI, lifecycle, dependency and save boundary. It does not remove the need
for hooks in BNW. Compiled optional modules with a stable Lua/data API are the
initial implementation choice.

## Module responsibilities and current limits

| Owner | Existing behavior to preserve | Native scope |
| --- | --- | --- |
| Terrain | Exposure, supply, agreements, relief, trade economics, UI/art | First implementation: genuine native trade routes enforcing the existing logistics rules and participating in religion/tourism/quests/accounting |
| Resource Outposts | Independent claims, upkeep, AI and optional shelter | Current gameplay remains Lua. Add narrowly required engine hooks only when a confirmed requirement needs them. |
| Irrigated Farm | Connected irrigation and current Terrain packaging | Current gameplay remains Lua. Shared tile-change notifications/cache invalidation may help future work; they are proposed interfaces, not implemented features. |
| Climate Change | Approved requirements and existing terrain-change research | Candidate native support for safe terrain changes and dependent-system updates. Rendering refresh remains unverified and may belong to the closed graphics engine. |

Supporting a mod does not require moving all its logic into C++. A native module
should own only state/operations needing engine authority or shared native
services. Existing IDs, approved assets and mod-specific rules remain with their
owners. Outpost resource extraction must never gain road/agreement prerequisites
from Terrain. Climate thresholds/transitions are not decided by this architecture.

All 16 combinations can be tested at the module-selector level; there are not
yet four standalone releases. Irrigation is still packaged in Terrain and
Climate has no runtime package. Actual playable test combinations follow
`tools/packages.py` until those release boundaries are implemented explicitly.

## Capability and simulation contract

1. Register capabilities from compiled implementations, with module API and state
   schema versions. Database requests cannot advertise that an absent feature exists.
2. After native content validation, resolve requests once, reject unavailable or
   incompatible modules/dependencies/conflicts, then freeze the selection before
   gameplay. No UI-driven registration or mid-game module toggling.
3. Expose the resulting capabilities through a namespaced Lua API. Version 0.1.0
   implements `Game.C5MGetCoreInfo`, `Game.C5MGetModules` and
   `Game.C5MHasCapability`; only core introspection is currently advertised.
4. Add narrow host call sites and typed services for actual native operations.
   Define ordering/ownership when modules affect the same tile or unit; report
   conflicts explicitly rather than letting the last handler silently win.
5. Each native simulation has one owner. In the native Terrain edition, disable
   the replacement Lua route/payment loop before native routes become active.
   No hidden parallel routes or duplicate native/Lua gold, pressure or units.
6. Save the core/content identities, active modules and versioned state. Validate
   before interpreting saved gameplay. Initially require new native games and exact
   validated content/core combinations; module selection keys alone are not a
   full compatibility check. Keep future state migrations explicit.
7. Keep disabled features inert, and test absent companion database rows as well
   as supported combinations. Human and AI creation/use paths obey the same rules.

## Reuse and delivery

The [reuse inventory](../gamecore/REUSE.md) identifies existing source, pinned
platform dependencies and trade regression cases. Reuse the shared Mac build,
ABI checks, provenance and compatibility functions. Audit consumer-side SDK
changes from the ports separately; do not transplant their balance rules or
claim a port's acceptance results validate the new core.

Existing standalone Workshop packages remain available on the stock core with
their documented feature limits. The native edition needs a shared core/content
contract and platform-specific delivery. Ordinary Workshop loading should be
used where supported; Mac native library activation needs separate verification
and a direct install/restore path. WSDLC is optional, not an activation requirement.

## Implemented milestone and next work

`gamecore/` now contains the pinned BNW 1.0.3.279 engine/SDK source, the adapted Mac
ABI layer, a full native build entry point, database lifecycle integration, and
Lua capability queries backed by the compiled registry. It has its own DLL GUID.
The first native artifact is a developer build. Its bounded native startup and
temporary activation/restoration passed on 2026-10-20; broader gameplay/save
acceptance remains open. No mod simulation provider is advertised, no new gameplay
state is serialized, and current Lua packages have not switched backends.

Remaining implementation order:

1. Extend the completed BNW startup/temporary restoration test to gameplay and
   save/load, and develop the direct player install/restore path. See the exact
   [baseline evidence](../gamecore/VALIDATION.md); other ports' acceptance is not inherited.
2. Add versioned gameplay/save state before enabling simulation providers.
   Configuration and discovery are implemented; save migration/rejection for
   additional module state is not. Add feature calls only with implementations.
3. Implement Terrain's [native trade contract](../mods/realistic-terrain/docs/NATIVE-TRADE-CONTRACT.md)
   against genuine engine routes, preserving and extending existing rule tests.
4. Integrate narrowly needed hooks for the other three owners, retaining their
   current requirements and source ownership. Do not invent unapproved mechanics.
5. Validate native effects, supported combinations, save/load and direct delivery
   during the separate in-game acceptance stage. Native GR2 work remains separate.
