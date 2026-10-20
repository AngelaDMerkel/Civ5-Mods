# Native gameplay checks

Checks use stock macOS BNW, single player, on a disposable 24 by 16 map.
The shared background runner holds the native test lease, preserves installation
and user-data hashes, and restores originals after each launch. Evidence is in
ignored `output/gr2-research/` directories; saves, game logs and screenshots are
local evidence, not package contents. Design and native art acceptance remain in
[NATIVE-ART-REVIEW.md](NATIVE-ART-REVIEW.md).

## Verified on 20 October 2026

| Evidence directory | Result | Scope |
| --- | --- | --- |
| `outpost-gameplay-native-02` | 48 native assertions passed; restored | Production UI initialization, technology gate, worker completion, neutral claim, road independence, strategic unit consumption, luxury happiness, repeated reconciliation, pillage/repair, abandonment, movement-event capture/recapture, annexation and conversion |
| `outpost-save-native-01` | 11 setup assertions passed; native save retained; restored | Active and pillaged neutral sites plus a partially built worker order saved through `UI.SaveGame` |
| `outpost-reload-native-03` | 30 native assertions passed; restored | A new game process loaded that save; claimant, pillage, resources, upkeep, assignment and work stamp survived; automatic construction advanced once per real turn and completed on turn five |

The first two types of fixture load unchanged production Lua and UI XML through a
temporary DLC transport. Their SQL results are serialized from an in-memory BNW
database copy. Only the fixture UI Lua copy receives a diagnostic include after
production initialization. This transport alone does not establish ordinary mod
activation. The separate ordinary-loader fixture preserves the real UUIDs, SQL
actions, imports and UI entrypoints and verifies `Modding.GetActivatedMods`.

Fixtures arrange cities, technologies, deposits and units with native setters.
The lifecycle test prefills build progress before the final genuine worker
contribution; the persistence test builds from zero over real turns. Capture uses
native movement setters and production movement events. Annexation uses native
ownership setters. These focused checks are not full campaigns or combat balance
tests. Human research/production choices are supplied by the fixture to allow
bounded unattended turns.

## Startup defect found and fixed

The first native run failed before gameplay initialization because
`Modding.OpenSaveData()` exposes bound `GetValue`/`SetValue` functions. Colon calls
passed an extra `self` argument and stock BNW rejected the key. Commit `159e685`
uses dot calls in Outposts and makes its mock reject the invalid convention. Save
keys and encodings are unchanged. The coordinated Terrain/irrigation correction
was integrated as `c079adb` (original Terrain commit `cb1c7cd`); the full combined
Lua suite then passed, including all 382 Outpost assertions.

Two early reload-fixture attempts were corrected without gameplay changes: a
one-population city could not train its queued settler, and `WorkRate(false)`
returned zero after movement had been spent. The passing retry queues valid
production and uses the full work rate for its expectation.

## Reproducing the checks

Coordinate the shared game reservation first. Use a clean pinned harness and
the WSDLC packer described in `tools/civ5_gr2/README.md`. Civ V must be closed,
Steam signed in and the desktop unlocked. Always use new evidence directories.

`tools/outpost_native_gameplay.py --database <stock-Civ5DebugDatabase.db>
--scenario core|persistence|ai --output <fixture>` stages a diagnostic source.
Pack that directory with WSDLC using the installed Expansion2 UI assets. Run it
with `python3 -m tools.civ5_gr2.background_test --harness <pinned-harness>
--dlc <packed-fixture> --output <evidence> --timeout 240
--fail-marker '[ROTEST] FAIL' --fail-marker 'Runtime Error:'`.

For persistence, retain the generated `after/Saves/single/
RO_NativeGameplay_Persistence.Civ5Save`, then use `--load-save <retained-save>` in
a new runner launch. Each launch restores user data before the next begins.

For ordinary activation, stage with `--ordinary-mods --scenario core|integration`.
Pack only its `transport/` directory as DLC. Pass each staged `mods/<package>`
directory to the runner with `--mod-stage`. The runner refuses existing mod UUIDs
and existing diagnostic destinations, enables only those temporary stages, checks
real activation, and removes their unchanged copies during restoration. Terrain's
fixture adds a read-only event probe to its own UI context; neither production mod
imports the other's Lua.

## Acceptance still in progress

Native AI construction/guard/repair/recovery, ordinary package activation and
combined Terrain shelter are being exercised separately. Long campaigns, varied
maps, competitive AI balance, full mouse-driven UI interaction, diplomatic exports
and all cultural annexation triggers still need broader playtesting. A fixture
success marker never substitutes for inspecting errors and restoration records.
