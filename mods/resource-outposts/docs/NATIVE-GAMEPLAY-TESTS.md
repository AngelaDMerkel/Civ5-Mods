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
| `outpost-ordinary-native-01` | Ordinary activation and UI entry verified; 48 lifecycle assertions passed; restored | Real package UUID, production SQL database actions, VFS imports and declared `UI/RO_UI.xml` entrypoint loaded through `Modding.ActivateEnabledMods`; the temporary DLC carried only the map/diagnostics |
| `outpost-integration-native-04` | 43 native assertions passed across nine real turns; restored | Both real mod UUIDs and ordinary UI entrypoints; roadless garrison shelter prevents heat damage, adjacent units remain exposed, pillage removes shelter, repair restores it, and extraction/upkeep remain independent |
| `outpost-ai-native-07` | 37 native assertions passed through turn 22; restored | Production AI reserves an expedition worker while retaining a domestic worker, completes and claims the site on turn seven, places a guard by turn 13, repairs and reconnects by turn 21, and withdraws a wounded guard on turn 22 |
| `outpost-integration-native-05` | 43 native assertions passed again; screenshots inspected; restored | Final UI revision through ordinary mod activation: selected-site header has no pink background, B emblem displays, before/after abandonment quantities are readable, and nine-turn shelter sequence still passes |

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
bounded unattended turns. Informational technology, era and ranking popups are
dequeued through their normal UI path so their turn semaphore cannot stall the
driver. The AI scenario disables wars and barbarians to isolate its planner
lifecycle; it does not establish contested-expedition or campaign balance.

## Native defects found and fixed

The first native run failed before gameplay initialization because
`Modding.OpenSaveData()` exposes bound `GetValue`/`SetValue` functions. Colon calls
passed an extra `self` argument and stock BNW rejected the key. Commit `159e685`
uses dot calls in Outposts and makes its mock reject the invalid convention. Save
keys and encodings are unchanged. The coordinated Terrain/irrigation correction
was integrated as `c079adb` (original Terrain commit `cb1c7cd`); the full combined
Lua suite then passed, including all 382 Outpost assertions.

The ordinary combined-mod probe then found that extensionless
`include("RT_Irrigation")` selected `RT_IrrigationAI.lua` in stock BNW. A separate
empty diagnostic context compared that call with `include("RT_Irrigation.lua")`;
only the full filename created `RT_Irrigation`. This reproduced with the sorted
production manifest order. Commit `8fd67da` adapts Terrain owner's `4f94732` fix
to this branch's module set, using exact filenames in Terrain startup. The
passing combined shelter run uses this correction. It introduces no mod
dependency, resource gate or saved-state change.

The native AI repair sequence reached its pillaged site but failed in
`Unit:CanBuild`: that stock binding reads its optional flags as integers, unlike
`Plot:CanBuild`. The AI now passes `0, 1` for actual eligibility and gold checks,
and the Lua mock rejects boolean flags. Evidence of the original failure is
`outpost-ai-native-06`; commit `4d316c6` fixes it and the passing native retry is
`outpost-ai-native-07`.

Inspection of the combined screenshot also found unstyled header grids rendered
pink and an unsupported arrow glyph omitted from the abandonment preview.
Commit `ef29bdf` uses transparent layout containers; the preview states the quantities
before and after abandonment in words. Selected icons and mesh artwork are
unchanged.

Two early reload-fixture attempts were corrected without gameplay changes: a
one-population city could not train its queued settler, and `WorkRate(false)`
returned zero after movement had been spent. The passing retry queues valid
production and uses the full work rate for its expectation.
Early AI fixture runs also corrected a total-maintenance expectation (ordinary
AI buildings can add upkeep), popup handling, and stale unit userdata after
uncontrolled combat. The final fixture resolves live unit IDs each turn, checks
the Outpost ledger separately, and uses the peaceful scenario described above.
One AI launch exited before map initialization; the runner restored its files
before retrying. An incomplete temporary shelter transport was stopped and
restored before using a newly packed fixture. None of these failed/interrupted
runs are counted as passing evidence.

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
imports the other's Lua. File entries are sorted exactly as in the production
builder. The separate include-comparison probe runs in its own context and does
not initialize Terrain or register its gameplay hooks.

## Validation and remaining acceptance

The final source/UI changes pass `python3 tools/build.py`, `python3 tools/validate.py`
with the clean stock BNW cache snapshot, the complete Lua suite (including 382
Outpost assertions), and all 44 Python tests. Database validation covers each mod
alone and both load orders. No diagnostic scripts enter either playable package.

Final restoration audit verified all 156 original user-data files against their
saved hashes, both stock executable/library hashes and original UI files. The
temporary DLC and mod stages are absent, no extra diagnostic files remain in
the backed-up user-data folders, Civ V is closed, and the native lease is free.
All 20 gameplay test journals, including failed and interrupted attempts, report
restoration. The pinned external harness remains clean. Passing runs above have
neither a Lua runtime error nor a failed assertion in their retained logs.

Long campaigns, varied maps, contested AI expeditions, guard healing through
release/reassignment, competitive AI balance, full mouse-driven UI interaction,
diplomatic exports and all cultural annexation triggers still need broader
playtesting. Native retreat is verified; full recovery is not. A fixture success
marker never substitutes for inspecting errors and restoration records.
