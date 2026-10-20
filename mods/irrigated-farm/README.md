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

**Current art direction (2026-10-20):** the user selected the v3 mesh study as
the structural approach and reaffirmed the native-overlay concept as the visual
target, asking for real workable models. Use v3's terrain and hydraulic work
with recognizable Civ V fields, regular Farm buildings and sparse irrigation.
The [selection record](../../shared/art/irrigated-farm/v3-civ5-direction/selection.json)
preserves both statements and their scope. The chronology below records earlier
decisions; statements that v3 was superseded are historical, not current policy.
This selection does not certify revised exports or in-game behavior.

**Current model approval (2026-10-20):** the user approved the R5 source-model
collection. [The approval record](../../shared/art/irrigated-farm/v3-civ5-direction/model-approval-r5.json)
fixes all 24 models at 72 GLB/OBJ/BR2 hashes and the existing atlas hash. The model
review prerequisite is satisfied; native conversion, terrain fit, dynamic
connections and game acceptance remain pending. Earlier hold statements below
record the review history. The runtime Farm-art fallback remains in place.

The approved v6 concept and prompts are versioned in
`shared/art/irrigated-farm/`. Mesh support is in `tools/build_irrigation_meshes.py`
and the newer `tools/irrigation_v2/`; generated kits and previews stay in
`output/models/irrigated-farm-v1/` and `irrigated-farm-v2/`.
Current detail/density refinement, native conversion and in-game terrain fitting
require their own verification and acceptance.

The **v3 mesh review, now selected as the structural approach,** is built by
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


An earlier user instruction explicitly selected the **regular resource-free farm
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


All saved art is indexed by `tools/irrigation_native/build_review_library.py` in
`output/models/irrigated-farm-native-fit/index.html`. This restores discoverability
of the earlier terrace, floodplain, transition, aqueduct, channel, edge, concept
and v1–v3 mesh studies alongside the regular farm candidates. The narrow
`regular-farm-review` page now links back to this full library. Historical meshes,
illustrations, native comparisons and current candidates retain distinct status;
the recovery changes navigation only and does not approve or modify their art.
See the native tooling README for the historical-output checkout argument and
local server command.


The 2026-10-20 implementation of the selected concept is now in
`tools/irrigation_native/build_concept_models.py`, with its own validator and
`concept-models/review.html` in the local library. It exports 24 editable models
and 23 experimental native GR2/FXSXML candidates: four terrain forms, wet/dry,
lower-detail variants, source/connector parts and a connected assembly. Genuine
regular Farm1 geometry and native crop/masonry/terrain pixels replace the generic
farmstead/material treatment; v3 terrain and rigid aqueduct structure are retained.
Flat carriers are sparse, contour outlets close inside fields, and hill feeders
remain level or descending. The earlier concept and v3 output are preserved.

These are actual mesh exports, not new generated mockups. They are local native-
derived review candidates, not completed playable art. The shared crop-family
selection on desert, foliage refinement, construction/pillaged conversions,
floodplain transition updates, dynamic adjacency and native loading/terrain tests
remain unfinished. Production gameplay and Farm-art fallback remain unchanged.
See the native tooling README for reproducible commands and format/scale limits.
No game or user-data files were changed; Irrigation holds no native-test session.


User review checkpoint (2026-10-20): the user explicitly reminded us that the new
models have not been approved. The concept/direction selection does not approve
these candidates. Further conversion, native testing and runtime integration are
on hold pending user model review. `shared/art/irrigated-farm/v3-civ5-direction/model-review.json`
records their exact hashes. Native probe preparation failed at an import before
creating a fixture; no game launch, installation or user-data change occurred.
The unused preparation script was removed. The existing library now prominently
labels the candidates as unapproved and links to the visual review first.


Geometry revision requested after that checkpoint (2026-10-20):
`tools/irrigation_native/build_concept_revision.py` creates a separate, unapproved
`concept-models-r2/` collection of 24 GLB/OBJ/BR2 models. Flat canals now follow
long parcel boundaries through rounded geometric turns, with one branch instead
of a comb. Three broad cultivated benches have continuous, joined masonry wall
fronts. Shallow curved aqueduct approaches feed separate supported receiving
chutes; height changes no longer tilt the long bridge decks. The regular Farm1
geometry and native-pixel atlas are retained. These are authored review terrains,
not captures of stock engine-generated desert farms.

The revision validator measures the exported water geometry as well as the
route graph: 12 spans, maximum 0.8% grade (about 0.46 degrees), 12 aligned receiving
joins, 109 level/falling routes, 15,786 terrain-clearance samples and 166 crop-seam
samples. Its design limits are 2% grade and 15 degrees between adjacent approach
segments. These normalized source limits do not establish native terrain fit.
The previous 71 recorded GLB/BR2/GR2 hashes remain unchanged. No GR2, DDS or
FXSXML was generated for this revision, and no game/user-data files changed.

The R2 review is `concept-models-r2/review.html`; the old
`concept-models/review.html` URL also shows the revision after rebuilding the
library. `concept-models/previous-review.html` preserves the previous review.
Close, map-scale and low-angle GLB renders accompany the selected concept and
real game references. `shared/art/irrigated-farm/v3-civ5-direction/model-review-r2.json`
records this unapproved revision separately. Native conversion, testing and
integration remain on hold; previous floodplain and other transition studies
remain available but have not been rebuilt in this pass.


The next review revision (2026-10-20) addresses the rounded gentle hill and missing
channels between flat crop textures. R3 replaces the radial gentle-hill crown
with three staggered, mostly straight retaining fronts, broad cultivated benches
and a planted upper terrace. Flat crop polygons and ditches now share one rotated,
staggered parcel partition: every shared plot boundary has a narrow ditch, with
wider row carriers. Clipped corner seams join along field margins, exposed ends
are capped, and neighboring flat plots retain matching open connections. Regular
Farm1 props and tree trunks are moved clear of these channels. The district's
low connector skirts the new terrace shoulder; high aqueducts retain shallow
approaches and separate receiving drops.

Build with `build_concept_revision.py --revision 3`; validate with
`validate_concept_parcels.py`. The 24 editable GLB/OBJ/BR2 candidates reuse the
native-pixel atlas and native regular Farm1 building. Steep and rocky forms stay
at R2 geometry. The validator checks the actual crop triangles, plot-edge ditch
alignment, building clearance, cultivated upper bench, flow and export parity;
all 71 R1 and 72 R2 recorded export hashes remain unchanged. This is an authored
terrain fixture, not proof of native Civ V terrain fit or hydraulic behavior.

`concept-models-r3/review.html` preserves the R3 review; rebuilding the library also
updates the existing `concept-models/review.html` URL. It includes a near-overhead
parcel view, close and reduced-size renders, and the connected assembly. R3 hashes
and verification are recorded separately in
`shared/art/irrigated-farm/v3-civ5-direction/model-review-r3.json` as **unapproved**.
Native conversion, game testing and runtime integration remain on hold. No game,
user-data, playable-art or runtime-source files were changed.


The following R4 review implements angular geometry and cascading water across
**all three hill forms**, rather than leaving the steep and rocky hills at R2.
Three straight trapezoidal benches rise at different heights for gentle, steep
and rocky terrain. Each has two crop plots shaped and textured within that bench,
with a central dividing channel and a front header. The water descends through
actual gaps in the retaining walls over short supported masonry steps, feeding
the next tier and finally the ground collector. There is no radial crown, and no
crop polygon spans a terrace riser. The regular Farm1 building remains genuine
source geometry; hill farmsteads are placed clear of connecting channels.

`build_concept_revision.py --revision 4` writes 24 separate GLB/OBJ/BR2 review
candidates. R3 flat model vertex/normal/UV buffers are unchanged. The new
`validate_concept_cascades.py` measures actual tier-crop containment, exported
cascade water vertices, level treads and falling steps, open wall notches, crop
and building clearance, and the inherited flow/terrain/export checks. It verifies
all recorded R1-R3 exports are unchanged. Close, overhead, front and reduced-size
renders of the actual GLBs were inspected; browser rendering remains unverified.

The preserved R4 review is `concept-models-r4/review.html`. The R4 hash
record is `shared/art/irrigated-farm/v3-civ5-direction/model-review-r4.json`.
These models remain **unapproved**. Cascades are static modeled water surfaces,
not an in-game fluid simulation or animated effect. Native conversion, terrain
placement, dynamic connections and game acceptance remain pending. This pass
makes no native/game/user-data or runtime changes.


The user found R4 improved but unnatural and unrealistic. R5 responds by keeping
angular terraces while reducing their symmetry and masonry mass. Each front has
a deliberate angular bend; widths, offsets and rises differ across the three
benches. The lowest bench holds three unequal plots and the upper benches two
each. Narrow soil margins replace the broad frames. Native masonry repeats at a
fixed physical scale instead of stretching across an entire wall. Channels sit
closer to the soil, run along upper plot edges and descend at different parcel
divisions on successive tiers. They remain connected, level or falling.

The original regular Farm1 building and native atlas are retained. R3 flat source
buffers remain identical, and all R1-R4 recorded exports are preserved. R5's
24 GLB/OBJ/BR2 candidates are generated with `build_concept_revision.py --revision 5`
and checked with `validate_concept_hillsides.py`. The assembly helper accepts the
new hill geometry while its default R4 assembly was reproduced in memory and
compared with the frozen position, normal and GLB UV buffers.

This response is a design interpretation of the realism feedback, not an
approved historic reconstruction. [Reference notes](../../shared/references/irrigation-hillside-realism.md)
record the native Civ V comparison and a real-world gravity-irrigation reference.
The current review is `concept-models-r5/review.html`, also shown by the existing
`concept-models/review.html` alias after rebuilding the library. Close, distance,
front, overhead and assembly renders show actual exported geometry. The initial
unapproved checkpoint remains in
`shared/art/irrigated-farm/v3-civ5-direction/model-review-r5.json`. The subsequent
“Approved.” response is recorded separately in `model-approval-r5.json`, lifting
the model-review hold for those exact R5 exports. Native conversion and game
validation are pending; no game, user-data or runtime files changed while recording
this approval. The modeled water surfaces are static.
