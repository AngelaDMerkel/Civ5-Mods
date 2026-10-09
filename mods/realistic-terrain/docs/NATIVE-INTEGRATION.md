# Native Mac trade integration assessment

Reviewed on 2026-10-09 after the user identified their GitHub account. This is a
follow-up design, not an implemented dependency or a change to the current
standalone single-player BNW target.

## Existing work to reuse

| Project | Relevant responsibility |
| --- | --- |
| [Wir Schaffen DLC](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC) | Mod-to-DLC translation, UI addin bridge, verified installation, switching and restoration |
| [macOS GameCore compatibility](https://github.com/AngelaDMerkel/civ5-macos-gamecore-compat) | Shared Mac build/ABI support, pinned source bootstrap and binary validation |
| [macOS coordinator](https://github.com/AngelaDMerkel/civ5-macos-coordinator) | Reproducible combinations of the compatibility layer, WSDLC and separate gameplay cores |
| [Lekmod](https://github.com/AngelaDMerkel/Lekmod) / [Vox Populi Mac port](https://github.com/AngelaDMerkel/Community-Patch-DLL-macOS) | Existing native gameplay-core consumers; adopting either also adopts its gameplay baseline |

WSDLC alone cannot turn a saved Lua route into an engine trade connection. The
missing native controls belong in a gameplay GameCore, using the existing Mac
compatibility work. WSDLC would package/install the resulting supported product.
Its [current native-product contract](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC/blob/main/docs/native-gamecore.md)
recognizes Lekmod and Vox Populi only; a separate Terrain/BNW core would require
explicit product support, rather than relabeling it as an existing product.

The native-product documentation reports a pinned Lekmod Steam-startup/save-load
test, while explicitly leaving broader gameplay/platform acceptance open and the
public native release catalog empty pending validation/publication. That is useful
existing work, not evidence that Terrain's rules already work in that core.

## Proposed implementation boundary

1. Choose a supported gameplay baseline explicitly: extend one existing core, or
   build a narrow BNW-compatible core using the shared port support. Do not add an
   overhaul dependency silently. Only one gameplay core can be active at a time.
2. Expose versioned capabilities for route eligibility, authorized transit,
   chosen path/range, movement, invested unit type, yields and plunder protection.
   Agreements and infrastructure decisions must be consulted by the engine,
   including AI route creation, rather than just the planner's Launch button.
3. Make native route objects the sole owner of active routes in that edition.
   Native trade connections can then participate in pressure, tourism, quests,
   overview and GPT calculations. Retain the logistics economy but account for
   native payments exactly once. Never run both route simulations for one convoy.
4. Preserve the standalone Lua edition separately. Do not infer compatibility
   from a DLL/dylib filename or the presence of unrelated extended APIs. Require
   the exact trade capability/version contract and fail clearly on mismatch.
5. Decide save migration before enabling a new backend. Current route IDs and
   fractions belong to `RealisticTerrain.Trade.v2`; they must not be silently
   interpreted as native connections. A new-game requirement is the conservative
   initial boundary.
6. Add the chosen product to WSDLC only after validating its manifest, signed
   binary and content inventory. Its install/switch/restore tests must include
   the Terrain edition. Workshop content can carry assets/scripts, but subscribing
   must not be described as sufficient to install the native core.

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
| Moving convoy presentation | Native UI portrait anchors; 3D conversion/rigging deferred |
| Religion, tourism, native trade-route quests | Not implemented; requires the native integration above for true parity |
| WSDLC packaging of Terrain | Not tested; its structural SQL/UI translation must be checked independently |

No external repository was modified, no GameCore installed, and no new dependency
added during this assessment.
