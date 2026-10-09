# Existing work to reuse

Inspected 2026-10-09 following the user's request to build on the substantial
existing work. This is an inventory and selection record, not a claim that the
new core has inherited the other projects' native acceptance results.

## Reused now

Shared platform repository:
`https://github.com/AngelaDMerkel/civ5-macos-gamecore-compat.git`

Pinned revision: `1663b23bdfa0b79f431c7ff437c6851581efa219`.

| Local input | Origin | Treatment |
| --- | --- | --- |
| `compat.lock.json` | Same revision and ABI contract as the inspected Lekmod consumer | Build-time dependency only |
| `tools/bootstrap_compat.py` | `tools/bootstrap.py` at the pinned revision; upstream Git blob `0745c966222a258f84d18e21e9d3b8d2c5f30063` | Copied unchanged |
| `third_party/compat.LICENSE` | Upstream `LICENSE`; blob `2732162c8492014343d589fe55b62bd7572af59d` | MIT copyright/permission notice retained |

The shared dependency already owns Windows API compatibility headers, Mac
compatibility functions, fixed-width serialization helpers, ABI assertions,
reproducible bootstrap/build tools, binary validation and provenance/package
tools. Consume that implementation and its tests rather than clone its logic.
The existing package tool currently accepts only `lekmod` and `vox-populi` and
requires a prepared DLC payload. It is not a ready-made release path for this
shared core or the standard Workshop packages; adapt only the relevant packaging
pieces when a native artifact exists, keeping direct installation independent.

## Port-specific work to adapt after baseline selection

Lekmod inspected at `181b7232160a5661424c275f2a62deb5c56a7a34`:

- [Mac build configuration](https://github.com/AngelaDMerkel/Lekmod/blob/181b7232160a5661424c275f2a62deb5c56a7a34/LEKMOD_DLL/macos/build.json)
  uses the shared build driver and lists its consumer-specific diagnostics.
- [Trade persistence regression](https://github.com/AngelaDMerkel/Lekmod/blob/181b7232160a5661424c275f2a62deb5c56a7a34/docs/macos-trade-persistence-regression.md)
  documents a trade-building cache reconstruction fix and native save/reload
  evidence. Reuse the regression scenario; port the fix only if the selected
  source contains the affected `TRADE_REFACTOR` implementation.
- [Incoming trade validation](https://github.com/AngelaDMerkel/Lekmod/blob/181b7232160a5661424c275f2a62deb5c56a7a34/docs/macos-incoming-trade-validation.md)
  records origin-identity/tourism query fixes and native UI/save evidence. These
  are useful tests for the new route integration; they do not prove its custom
  agreements, relief, protection or economy rules.
- `LEKMOD_DLL/macos/` contains trade creation, domestic delivery, expiry, plunder,
  countdown, removal, incoming-route and save/load scenarios and native binding
  tests. Reuse applicable cases with the new core/content identity.

The [shared ABI contract](https://github.com/AngelaDMerkel/civ5-macos-gamecore-compat/blob/1663b23bdfa0b79f431c7ff437c6851581efa219/docs/abi.md)
also lists adjustments which deliberately remain in **consumer SDK source**:
the Aspyr pregame vtable slot, database object layouts, pointer-width arithmetic,
LP64 types and RNG stream representation. Fetching the compatibility library
alone does not apply these changes to a clean BNW SDK tree.

The [Vox Populi Mac port](https://github.com/AngelaDMerkel/Community-Patch-DLL-macOS)
is another implementation reference. Its balance/AI/save changes are not assumed
to be a neutral BNW base. Reuse common fixes deliberately, preserving original
licenses and attribution, without requiring its gameplay content.

## Preserve this repository's gameplay work

| Existing source | Reuse boundary |
| --- | --- |
| Terrain trade/exposure/supply and tests | Preserve rules, balance, assets and UI. Port only authoritative trade operations that need native integration; use current tests as behavioral requirements. |
| Outposts claims/upkeep/AI and tests | Remain independent of roads, agreements and Ministry. Do not rebuild these systems merely to claim a native module. |
| Irrigation connectivity and tests | Keep current rules and source ownership; native capability work does not split its current Terrain package automatically. |
| Climate requirements and research | Preserve approved direction and tile-refresh findings; no completed climate runtime exists to port yet. |

## Not reused as mandatory runtime dependencies

WSDLC's installation/switching work is useful reference and optional later
distribution support. Players must have a direct native installation/restoration
path. Neither WSDLC nor the Mac coordinator is required to run these four mods.
No remote project was edited and no installed game was modified in this work.
