# Developer core validation

Latest native evidence: **2026-10-20**. The original build checks below were
completed on 2026-10-09.

Version 0.1.0 was compiled locally from all **166 translation units** (160 BNW
engine/Lua files plus the shared compatibility and project host sources) with
Apple Clang 21 for `x86_64-apple-macos10.11.6`.

The resulting `libCvGameCoreDLL_Expansion2_DLL.dylib` is 6,911,240 bytes.
SHA-256: `87864edd7523978b571dc27f80d0029177cdbfdc39190cf004ccbbc2a866ea5c`.
The generated build report and developer archive record the exact source and
compatibility revisions. The original build checks did not modify or launch the
installed game. The subsequent explicit native test is recorded below.

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

## Native baseline — 2026-10-20

The developer binary above, built from `65b2f17`, passed the first bounded
background test using the runner committed in `2f39e2f`. It was temporarily
activated directly in the installed stock Mac game, without WSDLC or any Lekmod
gameplay/content. The external test helper revision was
`181b7232160a5661424c275f2a62deb5c56a7a34`.

- Actual game initialization passed: version 0.1.0, frozen/ready configuration,
  only `c5m.core` active, introspection available and no native trade capability.
- A new BNW duel/Continents game initialized at turn 0 with a 40×24 map, a human
  Rome player, two starting units and a living Greek opponent.
- The captured window was visually inspected: the map, starting Settler/Warrior
  and normal game controls rendered. This is baseline rendering only, not review
  of Terrain's custom artwork or UI.
- The host executable was unchanged. The optional host-stat startup correction
  was **disabled**. The process used the existing background/capture helper;
  this does not establish ordinary Steam-launch behavior without test hooks.
- Restoration verified 155 original data entries, four app files and the
  fullscreen preference. Civ V was closed and the native lease released.
- All 19 disposable recovery tests passed, as did the registry/RNG/lifecycle,
  SQL adapter, allocator and real Lua binding checks. These accompany, rather
  than replace, the native run.

Evidence is retained locally in ignored `output/native-tests/baseline-01/`:
`session.json`, backups, `after/Logs/`, `process.log`, and `game.png`.
Run ID: `7ec47f9bfe8545f9a616591d397a4cd5`.
The Lua log contains the matching `status=PASS version=0.1.0 turn=0 units=2
width=40 height=24` record. Capture SHA-256:
`8d3fdae3f1fd7797f3d0ec38fb0aee21604d0a19313474c67f9c100b752f4bfc`.

The restored stock core SHA-256 is
`0da6a5ffc283c3f147b20a7ec426e4ed85a6838ab891faf61b50af4e25c4a09c`;
the unchanged host SHA-256 is
`d56d6bfbc0ef517fcb7cbaff46c42d1bdfab809c084684045761bd9d85807ee9`.

## Not established by these checks

Gameplay over multiple turns, save/load compatibility, each playable mod
combination, a permanent player installation, ordinary Steam launch, and custom
art/UI acceptance remain unverified. Temporary developer activation, startup and
restoration now have the specific passing evidence above.
Windows has no compiled/validated target. The module-selector fixtures and SDK
adapter tests do not substitute for running the game.

Only `c5m.core-introspection` is advertised. Terrain native trade, additional
Outpost/Irrigation services, Climate terrain/rendering work and versioned native
simulation saves remain unimplemented. Current Lua content remains authoritative;
the presence of this binary must not switch it to a native trade backend.
