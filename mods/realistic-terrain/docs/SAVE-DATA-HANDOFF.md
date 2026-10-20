# Bound SaveData calls — 2026-10-20

The Outposts native gameplay run reported that stock Mac BNW's
`Modding.OpenSaveData()` returns bound `GetValue(key)` and `SetValue(key, value)`
functions. Colon calls add the userdata as the first argument and fail with
`calling 'GetValue' on bad self (string expected, got userdata)`.

Terrain's old mocks incorrectly accepted that extra argument, hiding the failure.
Fifteen calls are corrected in `RT_Gameplay`, `RT_Supply`, `RT_ConstructionOrders`,
`RT_Trade` and the bundled `RT_IrrigationAI`. `RT_Art` already used dot syntax.
The five affected test fixtures now require string keys with no implicit `self`.
Save keys, value encoding, package IDs/versions and processing guards are unchanged;
this is a calling-convention fix, not a saved-state migration.

## Ownership handoff

The focused Terrain/irrigation correction is commit **`cb1c7cd`**, on
`core/shared-gamecore` in its isolated worktree. The irrigation owner's geometry
work and other checkouts were not edited. Irrigation's only runtime change is the
two database calls in `src/Lua/RT_IrrigationAI.lua`, plus its strict test mock.
Retain this fix when integrating later irrigation work. Terrain's construction
orders also serve the combined release's irrigation.

Outposts owns its analogous correction in **`159e685`**, cherry-picked here as
`b7985c8`. Both fixes are necessary: integrating only one leaves the older
companion mock using the wrong calling convention and breaks the cross-context
worker-guard test. With both applied, the complete Lua suite passes. Do not add
a dual-convention fallback to accommodate obsolete fixtures.

## Verification

- Reproduced the failure by making the mocks strict before changing production
  calls: construction initialization failed at `GetValue` as expected.
- All production Lua syntax and the full `tools/test.py` Lua 5.1 suite pass,
  including context reloads, saved routes/exposure, station ownership,
  construction/payment guards and isolated Terrain/Outposts integration.
- `tools/build.py` rebuilt both registered packages; seven packaging tests pass.
- Package/SQL validation passes for Terrain alone, Outposts alone and both load
  orders using the preserved stock cache from the earlier baseline test. The live
  cache contained the other chat's Outposts fixture and failed the clean-baseline
  assertion, so validation used `output/native-tests/baseline-01/data-backup/cache`.
  No installed database or native test session was changed.
- The corrected Terrain package has not been run natively in this pass; Outposts
  retains the shared test reservation. The prior core-only startup acceptance
  does not validate Terrain's saved gameplay.
