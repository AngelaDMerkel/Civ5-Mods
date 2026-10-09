# Shared Civ V GameCore

This project contains the full BNW 1.0.3.279 gameplay source, Mac host adaptations,
a native build, and a versioned module/capability layer. It targets the four
repository mods without adopting Lekmod/VP gameplay or requiring WSDLC.
The first full Mac build and strict ABI/installed-host checks have passed;
see the [validation record](VALIDATION.md) for evidence and limits.

**Version 0.1.0 is a developer core, not a feature-complete native edition of the
four mods.** It implements core discovery/configuration, not Terrain's native
trade backend or Climate's native terrain/rendering work. Existing Workshop
packages keep their Lua simulation and contain no native library.

## Build and checks

From the repository root on macOS with Clang and Python:

```sh
python3 gamecore/tools/build.py --jobs 2 --incremental
python3 gamecore/tests/run.py
CXX='clang++ -target x86_64-apple-macos10.11.6' python3 gamecore/tests/run.py
.venv/bin/python gamecore/tests/test_lua_bindings.py
python3 gamecore/tests/test_batch_allocate.py
python3 gamecore/tests/test_database_adapter.py
```

The Lua binding test uses `lupa==2.8` from `tests/requirements.txt` to run production
C++ bindings against real Lua 5.1. It does not start Civ V. The build bootstraps
the exact [shared compatibility revision](compat.lock.json); it rejects a dirty
dependency checkout and validates the binary before replacing a previous output.
The database test runs production request-loading code through an SDK-shaped
SQLite adapter, including interrupted reads; it is not a native host ABI test.

Output is `build/gamecore/macos/libCvGameCoreDLL_Expansion2_DLL.dylib` with a build
report. After committing and rebuilding from a clean revision, package the
validated developer artifact with:

```sh
python3 gamecore/tools/package.py
```

That produces `dist/native/C5M-GameCore-macos-developer.zip` with file hashes,
source/compatibility revisions, ABI validation and explicit acceptance status.
Use `--app '/path/to/Civilization V.app'` for read-only host hash verification.
The archive is not an installer or Workshop content package. Native activation,
startup, save/load and gameplay acceptance remain deferred. Windows has no
validated build yet; see [its target notes](platforms/windows/README.md).

## Engine integration

`CvDllDatabaseUtility` configures the core after BNW data caching and freezes the
selection before gameplay. A database flush clears it. Missing request tables
select only core services, so ordinary BNW and current Lua mod content require
no new SQL. An optional native content edition can provide:

```sql
CREATE TABLE IF NOT EXISTS C5M_EnabledModules (
    Module TEXT NOT NULL PRIMARY KEY,
    APIVersion INTEGER NOT NULL CHECK (APIVersion > 0)
);
INSERT INTO C5M_EnabledModules VALUES ('c5m.core', 1);
```

Only compiled implementations can register providers. Unknown modules, malformed
requests, duplicates and version mismatches fail caching with a diagnostic in
the database log; they do not partially activate or reuse stale capabilities.

The `Game` Lua table retains all stock members and gains these read-only methods:

| API | Result |
| --- | --- |
| `Game.C5MGetCoreInfo()` | Version, API version, phase, ready flag, error, selection key, simulation-ownership flag |
| `Game.C5MGetModules()` | Fresh ordered array of active module IDs |
| `Game.C5MHasCapability(id, version)` | True only for an active implementation at the exact requested version |

The only current provider is `c5m.core` API 1, capability
`c5m.core-introspection` version 1. `OwnsModSimulation` is false. There are no Lua
setters, runtime binary plugins or automatic backend switches. Feature-provider
ownership and the extension process are in [modules/README.md](modules/README.md).

## Source and compatibility boundaries

- `engine/`: pinned BNW source and matching SDK headers with original hashes and
  notices. Small host integration changes remain reviewable against the import.
- `include/`, `src/`: C++03-compatible module registry/context; Lua/database host
  bridges. Registry resolution is deterministic and rejects dependency cycles,
  conflicts, missing capabilities and duplicate providers.
- `platforms/`: host ABI/build adaptations. The Mac target reuses the existing
  compatibility project and audited consumer changes from the user's port.
- `tests/`: portable module/lifecycle/RNG checks and real Lua binding tests.

The core has a unique DLL GUID. It adds no serialized gameplay state in 0.1.0.
Selection keys are configuration diagnostics, **not** save compatibility proof.
Future native gameplay providers require a versioned save identity/state contract
and actual save/load acceptance before activation. Keep initial native tests on
disposable new games; do not assume interchangeability with other cores.

See [architecture](../docs/SHARED-GAMECORE.md), [source provenance](engine/README.md),
[reuse inventory](REUSE.md), [Mac details](platforms/macos/README.md), and
[Terrain's native trade contract](../mods/realistic-terrain/docs/NATIVE-TRADE-CONTRACT.md).
