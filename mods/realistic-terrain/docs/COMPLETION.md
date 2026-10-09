# Terrain completion branch

Work is isolated on `codex/terrain-trade-completion` in a separate worktree.
Native GR2 conversion/rigging and in-game acceptance are deferred at the user's
request. This branch addresses route presentation, stock-Lua trade integration,
UI polish and release preparation. It does not publish or merge the mod.

Use semantic, validated commits for each coherent implementation milestone.
Existing approved artwork and model designs remain unchanged. Additional artwork
must follow the recorded options, native-reference comparison and selection process.

## Congress and forecasts

Active World Congress embargoes now reject new routes and suppress payments on
existing routes immediately when quoted. Turn validation recalls the invested
unit once. Domestic routes are exempt; existing agreements survive sanctions and
can be used again after repeal. Embargoes restrict endpoints, not transit rights.
City-state and major-civilization sanctions are separate, and apply to outgoing
routes of Congress members, matching the stock SDK implementation.

The forecast adapter adds the mod's gross treasury payment to native GPT. Native
GPT already includes road and unit maintenance, so it must not use the ledger's
net figure and deduct those expenses twice. Fractional payout and the per-turn
payment guard remain unchanged.

Verified with the Lua 5.1 suite, package builder, and installed BNW database
validation (Terrain alone and both companion loading orders). Native game
acceptance remains deferred.

API evidence: stock [League bindings](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaLeague.cpp)
provide active resolution types and proposer decisions; the
[Congress implementation](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvVotingClasses.cpp)
defines member and city-state embargo semantics.

## Map display and planner

- Active convoys use moving native WorldAnchor portrait markers. No gameplay
  proxy units are spawned, so the simulation retains control of garrison
  protection and raids. These are UI markers, not converted/rigged 3D models.
- Markers replay each traversed tile, snap across wrapped map seams, hide in city
  and strategic views, and rebuild from saved route positions. Selecting a marker
  opens active routes. Stock unit atlas references are used, with the existing
  Caravan fallback for Motorized Caravans; no artwork approvals change.
- Foreign traffic, including incoming routes, requires current vision. Unknown
  endpoints remain anonymous and stale Locate callbacks recheck visibility.
- Accounts combines native GPT and gross mod payments. The native top bar and
  native trade overview remain unchanged. Route entries resize to wrapped text,
  planner labels are localizable, and Escape closes the panel.
- Terrain's worker panel reserves 112 vertical pixels for the optional Outposts
  construction panel when its database definition is present. This addresses the
  known shared top-center placement; full native layout review is still pending.

The production Lua adapter and marker module are covered by deterministic tests,
including movement events, fog transitions, player/view changes and marker cleanup.
These tests do not establish rendering quality, frame rate or native event timing.
