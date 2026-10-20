# Mac baseline acceptance

The user's instruction to continue permits native acceptance when other chats do
not need the shared Civ V installation. Check their current state first. The
runner also holds the same cross-worktree lease as the GR2 tests and refuses a
running game. Do not launch tests as an incidental build check.

`gamecore/tools/native_test.py` temporarily activates a validated developer core,
appends disposable startup/check hooks to stock front-end Lua, starts a small BNW
game in the background, and restores the original files and display preference.
It checks core identity/configuration, module selection, starting units and map
initialization. It does **not** establish native trade, long-running gameplay,
save compatibility, Workshop installation or visual acceptance.

## Prerequisites and commands

Use a locally checked-out, clean test harness from AngelaDMerkel/Lekmod at
`181b7232160a5661424c275f2a62deb5c56a7a34`. This reuses its existing background,
capture, desktop/Steam readiness and new-game startup helpers only. No Lekmod
gameplay, installer, WSDLC, DLC or permanent startup correction is used. It does
not download tools or sign into Steam. Steam must already be signed in and the
desktop unlocked.

The stock installed GameCore and host must match the pinned compatibility ABI.
The candidate binary must pass that ABI validator and match a clean build report.
Custom installed DLC directories are rejected for this baseline test.

From the repository root (replace the harness path with its actual checkout):

```sh
python3 gamecore/tests/test_native_session.py
python3 gamecore/tools/native_test.py --check --harness /path/to/Lekmod \
  --output output/native-tests/baseline-01
python3 gamecore/tools/native_test.py --run --harness /path/to/Lekmod \
  --output output/native-tests/baseline-01 --timeout 600
```

`--check` does not change game files or launch a game; the external harness may
compile its local desktop helper. Each run needs a fresh output directory.
The optional `--host-stat-compat` uses the existing verified-host SQLite stat ABI
correction in the **test process only**. First reproduce and inspect the startup
failure without it; never claim that a corrected test proves unassisted launch.

## Restoration and evidence

`session.json` and exact backup copies are written before game changes. App files
are replaced atomically. Cleanup terminates only the process launched by this
runner. It preserves changed logs/test saves under `after/`, restores original
saves, caches, settings, core/UI files and the fullscreen preference, and verifies
file hashes. The host executable is never modified. The lease is held until
cleanup finishes.

On interruption, retain the evidence directory. With Civ V closed, recover using:

```sh
python3 gamecore/tools/native_test.py --restore --harness /path/to/Lekmod \
  --output output/native-tests/baseline-01
```

Damaged backups, unexpected app edits, symlinks and unrelated replacement files
stop restoration rather than overwrite other work. A killed supervisor can leave
a journal requiring recovery even though its kernel lease is released. Check
previous native sessions across worktrees after a reboot; the temporary lock file
may no longer exist. The runner checks the last recorded lease's journal and
earlier sessions beside the selected output directory, not every other project.

Only a matching run-specific Lua PASS establishes baseline checks. Capture success
and visual review are separate. Record the exact build/hash, any startup correction,
outcome and verified restoration before advertising native acceptance.

## Current Terrain package probe

The runner also supports `--mod-stage` for temporary ordinary-mod activation.
Existing mod UUIDs or diagnostic directories are refused. The journal includes
the temporary stages and `ModUserData`; interrupted partial installation can be
recovered, and independently changed payloads stop restoration. The original mod
activation cache is restored with the other user data. No DLC translator is used.

```sh
python3 tools/terrain_native_gameplay.py --output output/native-tests/terrain-stage-01
python3 gamecore/tools/native_test.py --run --harness /path/to/Lekmod \
  --output output/native-tests/terrain-01 \
  --mod-stage output/native-tests/terrain-stage-01 --probe-event C5M_TerrainProbe
```

The core baseline must succeed before dispatching the test event. Only that
fixture's run-specific final PASS completes the run. This checks the current
production Terrain UI/Lua on the shared core, including native API calls, route
launch/recall, markers and worker AI. The fixture appends a diagnostic include to
a staged UI copy, constructs a disposable corridor and invokes production
functions; it is not a campaign or proof of the future engine-owned trade system.
It writes a diagnostic save for later process-restart testing. Writing and
reading mod save data within one process does not establish save/load acceptance.
See the owning mod's [native integration record](../../../mods/realistic-terrain/docs/NATIVE-INTEGRATION.md).
