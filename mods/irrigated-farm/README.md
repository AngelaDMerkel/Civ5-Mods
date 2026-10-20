# Irrigated Farm

SaveData compatibility update: the AI now calls the bound native functions with
dot syntax. Save keys and turn guards are unchanged; see the
[Terrain/irrigation handoff](../realistic-terrain/docs/SAVE-DATA-HANDOFF.md).
AI repair also uses the native `Unit:CanBuild` integer flags; see the
[worker binding handoff](../realistic-terrain/docs/NATIVE-INTEGRATION.md#worker-build-binding-follow-up--2026-10-20).

Owned by the **Irrigated Farm** chat. Dedicated gameplay code now lives in
`src/Lua/RT_Irrigation.lua`, `src/Lua/RT_IrrigationAI.lua` and
`src/SQL/RT_Irrigation.sql`; tests live in `tests/`.

The existing implementation remains part of Realistic Terrain v2. It has no
independent `.modinfo` or release UUID yet. Construction orders, startup/UI hooks
and localization remain in Terrain. The shared package builder assembles both
source roots into the same release without changing installed filenames.

[IRRIGATION.md](docs/IRRIGATION.md) describes the currently implemented connected
desert irrigation rules. The user's newer design direction includes terraced
hills and compatible tile transitions; those visual requirements must not be
mistaken for completed expansion of the gameplay eligibility rules.

The approved v6 concept and prompts are versioned in
`shared/art/irrigated-farm/`. Mesh support is in `tools/build_irrigation_meshes.py`
and the newer `tools/irrigation_v2/`; generated kits and previews stay in
`output/models/irrigated-farm-v1/` and `irrigated-farm-v2/`.
Current detail/density refinement, native conversion and in-game terrain fitting
require their own verification and acceptance.

See the [development guide](../../docs/DEVELOPMENT.md) for the remaining standalone
packaging work and the [tool catalog](../../tools/README.md) for validation.
