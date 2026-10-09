# Irrigated Farm

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

The historical **unapproved v3 mesh review** is built by
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

The user selected the **native Farm and Incan Terrace Farm artwork with readable
irrigation additions** as the preferred approach on 2026-10-09. Preserve native
textures, parcels and boundaries. This supersedes the replacement-field approach
of the earlier mesh studies. The [direction selection](../../shared/art/irrigated-farm/native-overlay-study/direction-selection.json)
records the exact confirmation and its scope.
`tools/irrigation_native/build_overlays.py` builds irrigation-only source pieces:
curved earth/stone channels, closed field outlets, open shared-edge joints and
the unchanged v3 aqueducts. Neighbor presence and actual water links are separate;
unused exposed route ends close inside the field. Native field boundaries and
textures remain the intended base. The local selector supports 64 neighbor masks,
but runtime dynamic selection and native mesh fitting are still pending.

The new [source study notes](../../tools/irrigation_native/README.md) distinguish
the exported overlay components from the generated visual study in
`shared/art/irrigated-farm/native-overlay-study/`. Neither is a verified in-game
capture or a converted native model. Previous studies and approval records remain
intact. No gameplay/source art references changed in this design pass.

The [plot-channel samples](../../shared/art/irrigated-farm/plot-channel-samples-v1/README.md)
show the requested sparse routing between crop parcels for flat, gentle-hill,
steep-hill and rocky-foothill terrain. Channels follow selected parcel boundaries;
most seams stay dry. Each sheet includes exposed/source and connected views.
These are generated visual samples, not native mesh/UV fitting evidence.

Actual native import is now implemented in
`tools/irrigation_native/import_native_farms.py`. Five installed Farm/Terrace Farm
assets export to editable GLBs and experimental GR2 files with verified vertex,
UV, index, transform and complete decoded-graph parity. Local extracts and renders
are ignored; they are not distributable mod assets. Ordinary farm crop decals are
separate from their GR2 props, as recorded in the installed `farm_types.xml`.
Native engine loading and terrain/adjacency integration are still pending.

See the [development guide](../../docs/DEVELOPMENT.md) for the remaining standalone
packaging work and the [tool catalog](../../tools/README.md) for validation.
