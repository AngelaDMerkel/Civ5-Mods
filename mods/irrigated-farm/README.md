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
`tools/irrigation_native/import_native_farms.py`. Eleven installed Farm/Terrace Farm
assets now export to editable GLBs and experimental GR2 files with verified vertex,
UV, index, transform and complete decoded-graph parity. Local extracts and renders
are ignored; they are not distributable mod assets. Ordinary farm crop decals are
separate from their GR2 props, as recorded in the installed `farm_types.xml`.
`build_native_fit.py` now adds original wet/dry header channels and an aqueduct to
the actual constructed Terrace Farm source mesh, keeping its native crop geometry
and UVs unchanged. The first fitting exports GLB/OBJ/BR2 plus experimental GR2,
DDS and FXSXML candidates, with gravity, clearance and export checks. Native
engine loading and terrain/adjacency integration are still pending; this is one
constructed-terrace fitting, not the full flat/hill/mountain or HB/PL variant set.

See the [development guide](../../docs/DEVELOPMENT.md) for the remaining standalone
packaging work and the [tool catalog](../../tools/README.md) for validation.

The subsequent terrain review expands this to seven authored fitting cases:
terraced hill, flat desert, flat grassland, river-fed floodplain, terrace-to-flat,
floodplain-to-desert and mountain-to-terrace. `build_terrain_cases.py` makes the
terrace carrier twice as wide, enlarges the reused aqueduct and gives sparse flat
channels broader pale banks. It preserves native terrace geometry and uses actual
regional crop textures in clearly labeled authored flat parcel layouts. The real
mountain heightmap and floodplain materials supply local reference context.
`validate_terrain_cases.py` checks fourteen wet/dry exports, source connections,
falling grades, shared ports and exported water clearance. These proposed meshes
remain offline review candidates; native flat placement, dynamic terrain art and
in-game acceptance are still pending. No new runtime eligibility is implied.

The subsequent user review identifies the seven authored terrain/parcel fixtures
as insufficiently faithful to the original models. They are diagnostic geometry,
not the accepted art baseline. The viewer now defaults to unchanged native
terrace source, that same source with irrigation, and irrigation alone, without
authored terrain. `audit_native_layout.py` confirms that ordinary farms depend on
the FARM layout handler and terrain contouring, while terraces use SNAPSHOT with
terrain contouring. Exact regular Farm1/2/3 variants differ from the wheat-resource
Farm prop used in the fixtures. In-game baselines and preserving those placement
systems are required before further native-art acceptance.


The user clarified that the native terrace source **may be modified** and the
irrigation should be obvious. Untouched source geometry is retained for comparison
and provenance, not as a requirement on the finished design. Future revisions may
change the native-derived terrace to integrate readable channels and aqueducts,
while retaining recognizable Civ V farm character. This is design direction,
not acceptance of a particular revised model.

The earlier reference files are genuine installed game assets, but the assembled
flat examples are not a verified standard desert-farm tile set. The terrace is
the Incan Terrace Farm improvement. Flat examples use native `Crops_Africa`
textures and `afri_desert_d.dds` with authored parcel placement; the prop reference
was the wheat-resource variant (corrected to regular Farm1 in the current diagnostics). The inspected farm definitions separate regional
crop families and era/resource model bindings, with no dedicated desert-farm row.
Exact farm texture selection and placement on a desert tile remain unverified
in-game; do not infer that `Crops_Africa` means a desert-specific farm asset.


The latest user instruction explicitly selects the **regular resource-free farm
building variant and the regular farm texture used on desert**. The importer now
includes all six stock Farm1/2/3 files (Ancient and Industrial bindings). It retains
the full three-state native graphs, while its visible exports select only the
constructed model. All eleven imports pass native graph and GLB buffer parity.
The six ordinary variants use the installed farmstead decals/materials; the
unsuffixed wheat Farm files are retained only as historical references. All four
regular regional crop families are recorded without treating Africa as a
terrain-specific selection. Native `FARM` placement must supply the actual fields.


`build_regular_farms.py` now produces twelve local native-derived regular farm
candidates: three variants in both era groups, wet and dry. The constructed stock
mesh receives only the new irrigation material group; original building and
farmstead-decal textures, geometry and all construction states remain intact.
Six proposed art rows keep the native `FARM` layout and terrain contouring so the
game can retain the regular crop textures and field arrangement on desert.
No crop replacement is generated. The regular-farm viewer shows actual asset
changes, with surrounding engine-generated fields explicitly absent.

Validation covers original native-graph preservation, GR2/GLB geometry and UV
parity, building clearance, descending water routes, capped outlets and bindings.
The channels are a farmstead candidate; alignment with actual crop parcel seams,
native terrain/lighting and runtime source connections still need in-game work.
This turn stayed offline while Resource Outpost held the native-test session.
Production fallback, approval records and gameplay remain unchanged.


Regular-farm correction verification (2026-10-10): eleven native imports passed
source graph and GLB parity; twelve regular wet/dry candidates passed their export,
preservation and water-route validator; all fourteen rebuilt terrain diagnostics
passed. Repository build, package validation, Lua 5.1 tests, Python syntax and
viewer JavaScript syntax passed. Actual close/distance renders and browser layer
controls were inspected. No game was launched or installed/user data changed by
this chat; it holds no native-test lock or restoration journal. The independent
Outpost native test work remains the current slot owner pending its release notice.
