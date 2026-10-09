# macOS GameCore build

This target uses the existing MIT compatibility project pinned by
`../../compat.lock.json`. It builds an x86-64 BNW gameplay library against the
recorded Aspyr ABI, with a minimum deployment target of macOS 10.11.6. Apple
Silicon development uses the x86-64 game target, not an arm64 replacement library.

From the repository root:

```sh
python3 gamecore/tools/build.py --jobs 2
python3 gamecore/tools/build.py --jobs 2 --incremental
```

The first build obtains the exact compatibility revision if it is not cached.
Clang/Xcode command-line tools and Python are developer requirements. No installed
game files, Steam settings or executables are modified. WSDLC is not used.
Output: `build/gamecore/macos/libCvGameCoreDLL_Expansion2_DLL.dylib` and the shared
driver's `build-report.json`. Binary validation runs before replacing a previous
good output. Limit parallel jobs on machines with little free memory.

## Consumer changes reused from the existing port

`reused-sdk.json` records the inspected source revision and SDK inputs. Retained
changes cover Aspyr's pregame vtable slot, database object layouts, LP64 integer
types, pointer-width allocation, Lua array handling and conforming C++ templates.
Unused overhaul-specific `AUI_*` branches were removed; Windows hash containers
retain the imported SDK type. Original copyright headers remain intact.

Engine adaptations cover the exported entry point and Mac singleton lifecycle,
explicit C++ string conversions, dependent types, 32-bit BNW RNG state, a pointer
return's null spelling, safe variadic string/pointer arguments, portable array
filling, const sort comparators, header function linkage, and the Lua unit
script-data temporary's lifetime. These are compatibility/correctness changes,
not adoption of another mod's gameplay. The project has its own GameCore GUID
`adba8683-1c7c-4fa9-968b-4114ff51751f` and core version `0.1.0`.

## Acceptance boundary

A passing binary validator checks architecture, load identity, deployment target,
the sole export (`DllGetGameContext`), and imports against the pinned host/system
symbol contract. `--app` on the shared validator additionally checks the installed
host's SHA-256. None of those checks starts Civ V or proves native gameplay.
All of these binary/host checks passed for the first build; see
[VALIDATION.md](../../VALIDATION.md).

Native launch, save/load, mod combinations and direct installation/restoration
remain a separate acceptance stage deferred by the user. The existing port's
experimental host SQLite stat-ABI correction acts **before** GameCore loading.
It is not transplanted into this dylib and cannot be fixed by a late-loading
GameCore constructor. If native acceptance reproduces that issue, a separately
verified direct startup correction is needed; WSDLC must remain optional.

The current core introduces no new serialized simulation state or native trade
backend. Keep initial native tests on disposable new games. A future gameplay
provider must implement save identity/schema rejection before activation. Do not
claim save interchangeability with stock, Lekmod, VP or future core editions.
