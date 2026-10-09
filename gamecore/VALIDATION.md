# Developer core validation — 2026-10-09

Version 0.1.0 was compiled locally from all **166 translation units** (160 BNW
engine/Lua files plus the shared compatibility and project host sources) with
Apple Clang 21 for `x86_64-apple-macos10.11.6`.

The resulting `libCvGameCoreDLL_Expansion2_DLL.dylib` is 6,911,240 bytes.
SHA-256: `87864edd7523978b571dc27f80d0029177cdbfdc39190cf004ccbbc2a866ea5c`.
The generated build report and developer archive record the exact source and
compatibility revisions. No installed game files were modified or launched.

## Checks actually run

| Check | Result |
| --- | --- |
| Full engine compile/link | Passed |
| Pinned strict ABI validator | Passed: thin x86-64, expected load identity/deployment target, one export, 471 approved imports (359 resolved by the host) |
| Validator with installed Steam Civ V app | Passed read-only host executable hash verification |
| Portable registry | 236 checks on arm64 and x86-64, including all 16 four-provider **fixture** selections |
| Core lifecycle | Configuration, freeze, reset, version/duplicate/unknown-module rejection and stale-capability removal passed on both targets |
| BNW RNG | Six million transitions match an independent uint32 reference on each target |
| Lua bindings | Production C++ bindings passed against real Lua 5.1 through Lupa; stock table preservation, copied results and invalid-version handling included |
| Database adapter | 20 production request-loader cases passed against an SDK-shaped SQLite adapter, including malformed data and partial reads |
| SDK batch allocator | Existing port's real-header regression passed ASan/UBSan for mixed and two-dimensional allocations |
| Pinned compatibility project | All five tests passed, including ABI, cache pinning, Lua array behavior and Mach-O validation |
| Existing Workshop releases | Package builds, Lua regression suite, seven packaging tests and installed-BNW database validation passed, including both SQL load orders |
| Documentation/source | Changed local links, Python syntax and Git whitespace checks passed |

The first link exposed an imported SDK header's conflicting static/external
definition. After correcting its linkage, the unchanged ABI validator rejected
SDK calls absent from Aspyr's host. The final request loader uses supported
queries plus a completion sentinel instead of unexported column/error methods.
The script-data lifetime fix uses the host's exported string API. No imports were
silently allowed or validation disabled to make the binary pass.

Compiler warnings remain in inherited BNW code (including legacy Microsoft
extensions and enum-range diagnostics); this is not a warning-free rewrite.

## Not established by these checks

Native Civ V startup, gameplay, save/load, each playable mod combination, direct
installation/restoration, and visual acceptance have **not** been performed for
this core. These remain in the separately deferred native acceptance stage.
Windows has no compiled/validated target. The module-selector fixtures and SDK
adapter tests do not substitute for running the game.

Only `c5m.core-introspection` is advertised. Terrain native trade, additional
Outpost/Irrigation services, Climate terrain/rendering work and versioned native
simulation saves remain unimplemented. Current Lua content remains authoritative;
the presence of this binary must not switch it to a native trade backend.
