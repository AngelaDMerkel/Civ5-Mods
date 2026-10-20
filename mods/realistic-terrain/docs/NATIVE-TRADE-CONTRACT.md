# Terrain module: native trade requirements

Status: implementation specification. No APIs or native binary described here
are implemented by the current Lua package. This records the minimum work needed
if native trade parity cannot be delivered through the standard mod interface.
No WSDLC runtime or installer dependency is permitted.

The subsequent user decision places this module in one project-owned GameCore
shared by the four repository mods. See [the shared architecture](../../../docs/SHARED-GAMECORE.md).
The trade rules below remain Terrain-owned; other mods do not acquire them just
because their native capabilities share the same binary.

## Why native work remains relevant

The inspected stock SDK player bindings expose trade summaries/quotes but no
interface for registering the current saved Lua routes as native connections.
City bindings expose religious follower conversion, not insertion of normal
trade pressure. Tourism and quest readers do not supply the native route objects
that those systems inspect. Exact parity requires the engine to know the route.

Evidence: [player bindings](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp),
[city bindings](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaCity.cpp),
and [trade implementation](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvTradeClasses.cpp).
These are the inspected source boundaries; target-binary behavior still requires
native testing. Do not infer an API's availability from an unrelated overhaul.

## Minimum engine responsibilities

| Area | Required behavior |
| --- | --- |
| Eligibility | All launch paths, including AI and native missions, require current endpoint/transit agreements and respect embargoes |
| Path and range | Use an engine-owned legal path with road range costs and supplied Caravansary relays; prevent unauthorized detours and loops |
| Unit capability | Preserve ordinary and motorized types; motorized remains an alternative, traverses passable land, and retains infrastructure gold deductions |
| Movement | Ordinary pre-Logistics caravans are lost on newly roadless neutral territory; required range loss recalls the correct invested unit |
| Protection | Mature supplied garrisons protect only authorized land trade convoys on connected roads; every native plunder path honors this rule |
| Native effects | Create real engine trade connections used by religion, tourism, quests, overview and native yield reporting |
| Economy | Preserve sustained infrastructure returns and shared expense allocation, while accounting for native gold/science/cargo exactly once |
| Save/load | Persist route identity, invested type and agreements; load without duplicate movement, rewards, pressure or returned units |

Keep game rules and state authoritative in the engine for the native edition.
Lua can retain presentation and planning support, but UI callbacks must not be
the only gate for creation, path selection, yields or protection. Engine hooks
must work with no planner open and for AI turns. Calls must use current facts,
not accept arbitrary gold, immunity or path data from an unvalidated UI quote.

## Backend selection and compatibility

- Identify the Terrain trade capability and version explicitly before game
  initialization. Report absence or a mismatch clearly for the native edition.
- Do not switch an existing save between native and Lua route ownership.
  Initially require a new game for the native edition. A later migration would
  need separate handling of every invested unit, route, fractional balance and
  ongoing construction order.
- In the native edition, disable the replacement route simulator and its payment
  loop before enabling native trade. Never create a hidden parallel native route
  merely to acquire tourism or quest rewards for a Lua route.
- Keep original database IDs and approved assets shared where possible, but use
  an explicit edition/build boundary. Current `Trade=0` unit definitions and
  `RealisticTerrain.Trade.v2` state must not silently become a native backend.
- Mod-only installation must keep working without any native component. Do not
  add a required native library or external installer to its manifest.

## Build and direct installation

Keep native source, build inputs, dependency revisions and licenses under the
shared `gamecore/` project, with Terrain's feature contract here. Reuse the existing
Mac build/ABI work as recorded in [the reuse inventory](../../../gamecore/REUSE.md).
The player download contains
the resulting component and matching mod content, not a requirement to build
the Mac compatibility repository or install another gameplay overhaul.

Before providing an installer, prove that the minimal core can build and load
on the supported Civ V version. Use the ordinary mod loader where supported.
If Mac requires replacing its gameplay library, supply a narrow shared-core
installer or documented direct process with exact version checks, a verified
original backup and restoration. WSDLC integration must remain optional.

Do not add a speculative launcher, executable patch, dependency download or
automatic core installation to the current Workshop package. Model conversion
and normal mod installation should not be conflated with engine replacement.

## Acceptance evidence

1. Build the unmodified BNW baseline with pinned compatibility dependencies and
   verify it loads, starts a game and restores cleanly before adding trade hooks.
2. Test each route rule from both native/AI creation and Terrain's planner.
3. Confirm pressure, tourism connections and city-state quests using actual game
   state, including route termination and duplicate-event/save-load cases.
4. Compare native and custom accounting through a long corridor, shared assets,
   sanctions, pillage/repair, raids, domestic delivery and successive contracts.
5. Confirm ordinary civilian capture remains unchanged; garrison protection must
   neither apply to workers nor depend on a decorative map unit.
6. Test the direct player installation, version mismatch, restoration and save
   boundary without WSDLC installed. The user subsequently authorized native
   tests when the shared game slot is free. The baseline startup and temporary
   restoration test passed on 2026-10-20; the remaining trade/save acceptance
   above is still pending. Specification is not acceptance.
