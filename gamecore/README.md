# Shared Civ V GameCore foundation

The user requested a shared GameCore for **Realistic Terrain, Resource Outposts,
Irrigated Farm and Climate Change**, with optional modules, on 2026-10-09.
Lekmod/VP gameplay integration is outside this initial scope. Existing gameplay
and Mac porting work should be reused. WSDLC is not a player dependency.

**This is a compiled foundation, not a loadable Civ V GameCore.** The BNW host
adapter, gameplay modules, Lua/database bindings, engine save integration and
platform binaries are not implemented here yet. No production capabilities are
advertised, and none of the current Workshop packages have changed backend.

## Implemented foundation

`include/C5M_ModuleRegistry.h` and `src/C5M_ModuleRegistry.cpp` provide a C++03
registry for compiled modules and exact-version capability contracts. Resolution:

- Enables only explicitly requested modules; unused modules have no capabilities.
- Rejects unavailable modules, wrong API versions, conflicting modules, duplicate
  providers, missing dependencies and cycles before producing an activation.
- Produces deterministic dependency order independent of registration/request order.
- Returns an immutable selection snapshot with a canonical module/API/state key.
  This key is only one part of future save validation, not a Civ V save format.
- Clears the output on failure so callers cannot reuse an earlier valid selection.

The registry performs no game mutations and loads no external binary plugins.
Descriptors are registered by compiled code; a mod cannot manufacture native
capabilities by adding database rows. The future host must freeze the resolved
selection before game initialization and dispatch only active modules.

Run its compiled checks with a C++ compiler and Python:

```sh
python3 gamecore/tests/run.py
```

Tests include all 16 combinations of four **fixture** providers. These are checks
of module selection, not claims that four gameplay modules work in Civ V.

Verification on 2026-10-09: 236 registry checks passed on the local arm64 compiler
target and on `x86_64-apple-macos10.11.6`; all five pinned compatibility tests
passed, including their Mac ABI/binary checks. Existing Lua, seven package tests,
package builds and installed-BNW database validation also passed. Windows builds
and native Civ V startup/gameplay/save acceptance have not been performed.

## Reusing the existing Mac platform work

`compat.lock.json` pins the same shared compatibility revision inspected in
Lekmod's Mac consumer. `tools/bootstrap_compat.py` is an unchanged copy of that
project's bootstrap, with its MIT notice retained under `third_party/`.
It fetches the exact revision into ignored `.compat/` and rejects a dirty cache:

```sh
python3 gamecore/tools/bootstrap_compat.py gamecore/compat.lock.json
```

This is an explicit developer dependency fetch; it does not run during mod
packaging or install anything into Civ V. The existing platform build, ABI
validation and provenance tools should be consumed from this dependency, not
reimplemented here. A full native build configuration still needs an audited
BNW source baseline with the consumer-side Mac ABI adjustments applied.

See [the shared architecture](../docs/SHARED-GAMECORE.md),
[reuse inventory](REUSE.md), and
[Terrain's first native feature contract](../mods/realistic-terrain/docs/NATIVE-TRADE-CONTRACT.md).
