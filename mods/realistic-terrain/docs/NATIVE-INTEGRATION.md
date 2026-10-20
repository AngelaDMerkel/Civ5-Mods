# Standalone distribution and native trade integration

Updated on 2026-10-09 following the user's distribution decision: make Terrain
as standalone as possible, preferably a standard Steam Workshop mod. If required
features exceed that boundary, write the necessary support for Terrain itself.
This supersedes the earlier proposal to make WSDLC the full-integration path.

The user subsequently requested one shared GameCore for the four repository
mods, with modular features and reuse of existing porting work. That decision
supersedes a Terrain-only native binary; see [SHARED-GAMECORE.md](../../../docs/SHARED-GAMECORE.md).
Terrain retains ownership of its trade rules. The full shared Mac core now builds
and has passed a native BNW startup test with temporary direct activation and
verified restoration (2026-10-20). Native trade remains unimplemented; see the
[exact evidence](../../../gamecore/VALIDATION.md).

## Ordinary-mod startup follow-up — 2026-10-20

The Outposts owner's combined ordinary-mod probe activated both real package
UUIDs, but Terrain stopped at `RT_Irrigation.Initialize()` because
`RT_Irrigation` was nil. Its reported evidence is
`output/gr2-research/outpost-integration-native-01/after/Logs/Lua.log` in that
owner's worktree. Both irrigation scripts were present with VFS import enabled.

Terrain now uses exact `.lua` filenames for all 19 private includes in
`RT_Environment.lua` and `RT_TradeBootstrap.lua`. This removes name ambiguity
between Irrigation/IrrigationAI, Construction/ConstructionOrders and the Trade
module family. The package regression check requires every private include to
identify exactly one imported filename, independent of file enumeration order;
the UI mock also loads exact filenames. Gameplay, package and database tests pass.

The native lookup collision is **confirmed**. The repeated probe's retained log,
`output/gr2-research/outpost-integration-native-02/after/Logs/Lua.log` lines 59–66,
shows the same startup failure, followed by a separate diagnostic context:
`include-prefix RT_Irrigation=nil RT_IrrigationAI=table`, then
`include-exact RT_Irrigation=table`. The Outposts owner also corrected the fixture
to use the builder's sorted file order before that run. The exact-filename fix
is commit `4f94732`. No installation files were changed by this branch's fix.

The follow-up `outpost-integration-native-04` passed **43 assertions through nine
real turns** on the stock GameCore. Its retained Lua log and restored session
journal were inspected. Both ordinary mod UUIDs/entrypoints loaded; the real
Terrain context initialized exposure and replacement trade and answered the
Outposts shelter queries. On desert tiles:

- An intact, owned, roadless outpost protected its stationed garrison from heat
  and damage; an adjacent unsheltered unit accumulated heat and took damage.
- Pillage removed shelter and the garrison began accumulating heat. Native
  repair restored shelter and cleared its heat counter over subsequent turns.
- Terrain introduced no extraction prerequisite or additional Outposts upkeep;
  repair restored the independent resource extraction at the original upkeep.

This tests the Outposts branch's older Terrain content with `cb1c7cd` integrated
as `c079adb` and the exact-include fix adapted as `8fd67da`. That branch lacks
the newer trade markers, so this is **not** full validation of this branch's
current Terrain package. It also does not establish native-engine trade parity,
Terrain trade save/load, other exposure environments, UI layout or custom art.
The evidence directory is `output/gr2-research/outpost-integration-native-04/`
in the Outposts worktree; `session.json` reports restored originals.

## Worker build binding follow-up — 2026-10-20

Outposts' native AI repair test exposed another stock binding mismatch.
`CvLuaUnit::lCanBuild` reads its optional visibility and gold flags with
`luaL_optint`, so callers must pass `0, 1` for actual eligibility with a gold
check. Terrain's trade infrastructure AI and bundled irrigation repair AI now
use those numeric flags. `Plot:CanBuild` has a different binding; its existing
boolean arguments remain unchanged.

Both affected Lua tests failed under stricter unit mocks before the correction
and passed afterward. The full Lua 5.1 suite, eight Python package tests, package
build and all four database combinations passed against the preserved stock
cache at `output/native-tests/baseline-01/data-backup/cache`. This verifies the
calling convention and existing AI decisions offline; a native Terrain worker
construction/repair run remains necessary.

Ownership handoff: only `RT_IrrigationAI.lua` and its worker mock changed in
Irrigated Farm. The Terrain change is in `RT_TradeAI.lua` and its worker mock.
Eligibility policy, save keys, database IDs and package versions are unchanged.
The Outposts owner supplied its independent equivalent fix as `4d316c6`.
No installed game files or user data were changed for this correction.

## Confirmed distribution requirements

- The standard package uses Civ V's ordinary mod format and requires BNW only.
  WSDLC, Lekmod, Vox Populi and companion mods are not required installations.
- Use supported Lua, SQL, XML and art first. Custom map models do not by
  themselves justify a custom gameplay core, though conversion and native visual
  acceptance remain necessary and deferred.
- WSDLC can optionally distribute compatible content later. Its SQL/UI
  translation work is not on the standard Workshop release's critical path.
- Do not quietly replace required native behavior with superficially similar
  effects to claim completeness. Fractional follower conversion is not native
  religious pressure; influence rewards are not native quest completion.
- Any unavoidable engine extension belongs to the shared project and must have a direct
  installation path. Reusable build-time Mac compatibility code is acceptable;
  players must not need to install the projects that originally developed it.
- Workshop packaging and Mac installation are separate acceptance questions.
  A valid `.modinfo` or `SupportsMac=1` declaration does not establish automatic
  Workshop installation on every Mac build. Verify the supported game's loader;
  document a direct mod-folder installation if needed, without requiring WSDLC.

The current package already follows the standalone dependency boundary. These
requirements do not make the missing native trade effects implemented.

## Existing work that can inform development

| Project | Relevant responsibility |
| --- | --- |
| [Wir Schaffen DLC](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC) | Mod-to-DLC translation, UI addin bridge, verified installation, switching and restoration |
| [macOS GameCore compatibility](https://github.com/AngelaDMerkel/civ5-macos-gamecore-compat) | Shared Mac build/ABI support, pinned source bootstrap and binary validation |
| [macOS coordinator](https://github.com/AngelaDMerkel/civ5-macos-coordinator) | Reproducible combinations of the compatibility layer, WSDLC and separate gameplay cores |
| [Lekmod](https://github.com/AngelaDMerkel/Lekmod) / [Vox Populi Mac port](https://github.com/AngelaDMerkel/Community-Patch-DLL-macOS) | Existing native gameplay-core consumers; adopting either also adopts its gameplay baseline |

WSDLC alone cannot turn a saved Lua route into an engine trade connection. The
missing native controls belong in a gameplay GameCore. Existing Mac compatibility
work is the selected build-time reuse path, without making WSDLC its installer.
Its [current native-product contract](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC/blob/main/docs/native-gamecore.md)
recognizes Lekmod and Vox Populi only; a separate Terrain/BNW core would require
explicit product support, rather than relabeling it as an existing product.

The native-product documentation reports a pinned Lekmod Steam-startup/save-load
test, while explicitly leaving broader gameplay/platform acceptance open and the
public native release catalog empty pending validation/publication. That is useful
existing work, not evidence that Terrain's rules already work in that core.

## Terrain module in the shared native core

1. Use the BNW gameplay baseline for the shared core's Terrain module; do not
   require an overhaul to obtain trade controls. Reuse validated build/ABI work
   where its licensing and interfaces permit. Only one gameplay core can be
   active at a time; the four repository mods share a build with optional native
   modules. Compatibility with an overhaul would need deliberate source integration.
2. Expose versioned capabilities for route eligibility, authorized transit,
   chosen path/range, movement, invested unit type, yields and plunder protection.
   Agreements and infrastructure decisions must be consulted by the engine,
   including AI route creation, rather than just the planner's Launch button.
3. Make native route objects the sole owner of active routes in that edition.
   Native trade connections can then participate in pressure, tourism, quests,
   overview and GPT calculations. Retain the logistics economy but account for
   native payments exactly once. Never run both route simulations for one convoy.
4. Preserve the standard Workshop/Lua package separately. Do not infer compatibility
   from a DLL/dylib filename or the presence of unrelated extended APIs. Require
   the exact trade capability/version contract and fail clearly on mismatch.
5. Decide save migration before enabling a new backend. Current route IDs and
   fractions belong to `RealisticTerrain.Trade.v2`; they must not be silently
   interpreted as native connections. A new-game requirement is the conservative
   initial boundary.
6. Deliver the shared native component with project-owned build, installation
   and restoration instructions/tools. Verify hashes, supported game versions,
   matching content, saved-game compatibility and recovery. On a platform where
   the ordinary mod loader can load the component, use that path; where it cannot,
   document the additional step explicitly. Do not assume a Mac engine library
   can be activated by a Workshop subscription. Optional WSDLC product support
   can be added independently after the direct path works.

The scoped native requirements are in [NATIVE-TRADE-CONTRACT.md](NATIVE-TRADE-CONTRACT.md).
That document is an implementation contract, not an existing API or compiled core.

Acceptance must cover native religion/tourism/quest effects exactly once,
AI/human agreement enforcement, sanctions/repeal, road and relay changes, mature
garrison protection, civilian vulnerability, both caravan types, fractional
payment, save/load and core switching. Mac runtime tests remain essential even
if a native build and ABI validation pass. DLC packaging does not establish
multiplayer support for this currently single-player mod.

## Current standalone coverage

| Concern | Current status |
| --- | --- |
| Gold, science, domestic cargo | Existing Lua settlement/delivery system |
| Congress embargoes | Implemented from active stock resolutions; tested with engine mocks |
| Combined income projection | Implemented in Accounts; stock top bar unchanged |
| Optional Outposts shelter | Bounded stock-native desert exposure/pillage/repair test passed on the older combined content described above |
| Moving convoy presentation | Native UI portrait anchors; 3D conversion/rigging deferred |
| Religion, tourism, native trade-route quests | Not implemented; requires the native integration above for true parity |
| Standard mod package | Existing ModBuddy/`.modinfo` staging and ZIP; BNW is the only required dependency |
| WSDLC packaging of Terrain | Optional, not implemented or required for the standard release |

The original distribution assessment changed no external repository, installation
or dependency. The subsequent explicit GameCore baseline test temporarily
activated the new core and restored the stock installation; it added no required
dependency to the Workshop package.
