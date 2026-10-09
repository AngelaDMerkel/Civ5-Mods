# Irrigated Farm — development notes

For player instructions, read [the mod introduction](../README.md).

Owned by the **Irrigated Farm** chat. Dedicated gameplay code now lives in
`src/Lua/RT_Irrigation.lua`, `src/Lua/RT_IrrigationAI.lua` and
`src/SQL/RT_Irrigation.sql`; tests live in `tests/`.

The existing implementation remains part of Realistic Terrain v2. It has no
independent `.modinfo` or release UUID yet. Construction orders, startup/UI hooks
and localization remain in Terrain. The shared package builder assembles both
source roots into the same release without changing installed filenames.

[IRRIGATION.md](IRRIGATION.md) describes the currently implemented connected
desert irrigation rules. The user's newer design direction includes terraced
hills and compatible tile transitions; those visual requirements must not be
mistaken for completed expansion of the gameplay eligibility rules.

The approved v6 concept and prompts are versioned in
`shared/art/irrigated-farm/`. Mesh support is in `tools/build_irrigation_meshes.py`
and the newer `tools/irrigation_v2/`; generated kits and previews stay in
`output/models/irrigated-farm-v1/` and `irrigated-farm-v2/`.
Current detail/density refinement, native conversion and in-game terrain fitting
require their own verification and acceptance.

The current **unapproved v3 mesh review** is built by
`tools/irrigation_v3/build_irrigation_meshes.py`. It replaces complete terrace
rings with partial benches and sloping shoulders, adds original painted alpha
foliage, and models a source-connected distribution network with contour
channels, bed branches and short aqueducts across dry gullies. Its validator
checks branch connections and downhill grade, including clearance against the
actual exported terrain triangles. `render_flow_review.py` annotates those
exported routes for inspection. Outputs remain in
`output/models/irrigated-farm-v3/`; they are not playable assets.

Original v3 texture input, its built-in imagegen prompt and provenance are in
`shared/art/irrigated-farm/mesh-v3-review/`. The source image is 1254 square and
packed to 2048 for export; this does not imply additional source detail or native
material compatibility. The v6 approval record is unchanged. Native conversion,
dynamic adjacency, terrain fitting and in-game visual acceptance remain pending;
the existing flat-desert gameplay and Farm-art fallback are unchanged.

See the [development guide](../../../docs/DEVELOPMENT.md) for the remaining standalone
packaging work and the [tool catalog](../../../tools/README.md) for validation.
