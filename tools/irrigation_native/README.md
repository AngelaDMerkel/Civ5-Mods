# Native farm irrigation overlays

Current clarification: the native terrace mesh may be modified to make irrigation
obvious. The unchanged source is a provenance/comparison reference, not an art
constraint. The existing preservation validators describe the current comparison
exports; they do not prohibit deliberately revised native-derived candidates.
The flat fixture is not a verified standard desert-farm tile set.

The user redirected the design on 2026-10-09: retain the default flat and hill
farm artwork and add conspicuous irrigation. The v1–v3 replacement fields and
terrain are historical studies, not the current art direction. The earlier v6
concept approval is preserved. The user subsequently selected this native-art
approach as preferred on 2026-10-09: “This direction is much better and should be
the preferred approach.” This selects the design direction; final mesh acceptance
and native validation remain pending. The exact scope is recorded in
`shared/art/irrigated-farm/native-overlay-study/direction-selection.json`.

Use the installed `ART_DEF_IMPROVEMENT_FARM` artwork for ordinary fields and the
installed `ART_DEF_IMPROVEMENT_TERRACE_FARM` / `Incan_Terrace_Farm.fxsxml` artwork
for the requested terraced hills. The latter is the native Incan improvement,
not an ordinary Farm hill texture. Preserve native crop UVs, field parcels,
retaining walls, props, terrain blending and exposed field boundaries. Do not
map a native atlas onto our rejected procedural farm geometry and call it native.

This source prototype contains **only irrigation additions**:

- A gently bending primary channel and two unequal side branches for a flat
  field layout, with earth-bank and low-stone-bank alternatives. Small furrows
  are left to the existing farm texture rather than additional tiny mesh lines.
- One contour-header component for fitting to an existing native terrace bench.
- Open shared-edge joints and closed, tapered field outlets set back from the
  edge. An absent irrigated neighbor cannot select an open water joint.
- The v3 aqueduct and mountain intake source geometry, reused unchanged.

Neighbor presence and hydraulic connections are different inputs. A neighbor
alone does not add a channel; selected water links must be a subset of irrigated
neighbors. The source selector covers all 64 neighbor masks and their 729 valid
water-link subsets. This is a component-selection contract, **not native runtime
adjacency**. Ports also require matching elevation and level/falling grade.
An open segment at an incoming source socket is intentional; downstream exposed
field ends use the closed component. Native field boundaries remain native.

OBJ/MTL, GLB and rigid BR2 exports are in
`output/models/irrigated-farm-native-overlay/`, with an offline viewer. The original
v3 material atlas supplies irrigation surfaces; native textures are not copied
into these outputs. The source importer/exporter and aqueduct builder are reused
from `tools/irrigation_v3/`. This directory is not a standalone source bundle.

The visual study in `shared/art/irrigated-farm/native-overlay-study/` was generated
with built-in imagegen using actual game screenshots as references. It illustrates
the proposed composition; its reconstructed scenery is not pixel-identical native
art or evidence of the exported mesh fitted to the game. Its little rounded
outlets and stepped water are illustrative; the actual source outlets are closed
earth ends, and no white waterfall effects are included in the meshes.

Native GR2 conversion, matching actual native mesh/UV geometry, terrain fitting,
material binding, overlay placement and in-game distance review are still pending.
The terrace header is an adjustable component, not a claim of native hill fit.
The earlier overlay pass did not decode the native base. The native importer
described below now supplies actual geometry for fitting. The earlier source
validator still checks only its original component geometry and connectivity. Current playable
flat-desert irrigation still uses the existing ordinary Farm art reference.

Run from the repository root with Python, NumPy and Pillow:

```sh
python tools/irrigation_native/build_overlays.py
python tools/irrigation_native/validate_overlays.py
```

Use `--quick` to omit preview renders or `--output PATH` to choose an output.


## Native asset pipeline — 2026-10-09

The preceding generated images did **not** use native farm meshes or preserve
native UVs. `import_native_farms.py` now reads the owner's installed FPK archives,
decodes little-endian Granny 7/Oodle1 data and resolves hashed names using the
corresponding GSD database. The open-source decoder and license are in
`vendor/opengr2/`; no Granny SDK or proprietary binaries are distributed.

```sh
python tools/irrigation_native/import_native_farms.py --game-assets "/path/to/Civ V/Assets"
python tools/irrigation_native/validate_native_import.py
```

Requires Python, NumPy, Pillow and a C compiler. The Assets path must contain
`Resource/Common` and `Resource/DX9`. Output defaults to the ignored
`output/models/irrigated-farm-native-fit/`. It contains private local extracts,
editable GLBs, native mesh renders, crop-decal references and experimental
uncompressed GR2 round trips. **Do not redistribute this output directory.**

Verified against the installed macOS BNW assets:

- Medieval and modern ordinary Farm props imported with original material maps.
- Constructed, unfinished and pillaged Incan Terrace Farm meshes imported.
- Native positions, normals, tangent/binormal vectors, all three UV components,
  triangle indices, individual model placement and reflected material parameters
  survive the GR2 round trip. GLB keeps indexed vertices and native transforms;
  a separate flattened review copy packs textures only for CPU rendering.
- Tree-cut stencil helpers stay in native GR2 but are excluded from visible GLBs.
- The constructed terrace has seven visible meshes, 1,817 vertices and 1,066
  triangles. Its large downward wall skirts are actual game geometry; the game
  terrain normally hides much of them. A source render is not a terrain capture.
- Ordinary farm GR2 files supply props. `Common/MiscData.fpk: farm_types.xml`
  separately lists regional crop decals from `DX9/DecalTextures.fpk`. Preserve
  that engine field system; don't substitute an invented field mesh. The local
  contact sheet shows the eight actual `Crops_Africa` textures.

`gr2_writer.py` emits real version-7 GR2 containers, relocation tables, reflected
schemas and ordinary UTF-8 strings. Full decoded graph equality is verified after
readback without a GSD. This is an **experimental exporter**, not certification by
Granny/Nexus or Civ V. Native material rendering, terrain contouring, engine
loading, states and dynamic adjacency still require engine tests. No runtime
art definition or gameplay rule is changed by these tools.


## First actual native fitting

```sh
python tools/irrigation_native/build_native_fit.py
python tools/irrigation_native/validate_native_fit.py
```

Run after the native importer. The generated `irrigation-fit/index.html` compares
the original native terrace, the combined model and irrigation alone. The main
GLB retains the native indexed positions, crop UVs and model transforms verbatim.
Only the separate renderer copy uses a packed inspection atlas. Renders are made
from exported geometry and decoded textures, never generated concept imagery.

The original addition is a single sparse header on measured wall caps in
`Incan_Farm06` and `Incan_Farm07`, fed by the existing aqueduct design. The aqueduct
builder is reused with a uniform 2.2 scale; its pier feet sample the actual native
surface and its waterline stays on one descending grade. The source socket is
open for an upstream connection; the exposed header outlet is closed inside the
farm. Most native parcel boundaries remain dry. No native field or wall is replaced.

Outputs include wet/dry GR2, FXSXML, mipmapped BC1 diffuse/SREF DDS, indexed GLBs,
OBJ/BR2 sources, the local combined model and distance/detail renders. The original
wet overlay has 573 triangles; dry has 525. The base native mesh has 1,066 visible
triangles. The painted irrigation atlas is reused from the previous original
source kit; it is not a native crop texture. No extra farm crops are generated.

Validation checks unchanged native vertices/UVs/indices/transforms, native GR2 to
GLB parity, finite/nondegenerate triangles, unit normals, wrapper references and
complete DDS mip chains. The route checks take 1,083 samples across the channel
width and aqueduct. Another 192 samples check actual exported wet triangles. The
minimum water clearance is about 0.146 native authoring units. These are source
mesh checks; engine terrain deformation may change the result. The source PNGs
were visually inspected and viewer JavaScript syntax checked; browser automation
was unavailable for interactive verification in this pass.

This first fitting is **not** a finished set for every terrain configuration.
The flat Farm crop-decal layout needs a native placement hook or an established
engine-compatible overlay method. Terrace HB/PL sources have been imported but
have not received irrigation geometry. Dynamic adjacent/source selection,
aqueduct terrain-contour exclusion, native engine loading/materials and actual
hill/mountain transitions remain unverified. The open source port does not prove
an in-game water connection. Runtime stays on the current Farm-art fallback.

Do not copy the whole local review output into a release: it contains the owner's
native reference art. Original overlay exports are separate, but are still an
experimental native-format candidate requiring engine testing and design review.


## Prominence and terrain-junction review

The next user refinement requests more prominent additions, flat and terraced
farms, floodplains and the junctions between terrain types. The native-art
selection remains the governing direction; these new mesh revisions are proposed
for review, not automatically approved by that earlier selection.

Run after both the native importer and first native fitting:

```sh
python tools/irrigation_native/build_terrain_cases.py
python tools/irrigation_native/validate_terrain_cases.py
```

The local `terrain-review/index.html` offers seven cases: terraced hill, flat
desert, flat grassland, river-fed floodplain, terrace-to-flat descent,
floodplain-to-desert connection and mountain-to-terrace aqueduct. Each has a wet
and dry original irrigation export, editable GLB/OBJ/BR2, experimental GR2/FXSXML,
and detail/distance renders. Display controls independently hide irrigation,
native crops/props, terrain or water. The viewer compares the actual mesh layers.

The terrace carrier grows from 0.44 to 0.90 native authoring units; the reused
arched aqueduct grows from scale 2.2 to 4.5. Pale bank shoulders and taller relief
make the added channels more legible. Flat cases use one 1.15-unit carrier and
one 0.82-unit branch along selected parcel gaps. Most field boundaries stay dry.
Exposed downstream ends close and taper inside the farm. Open upstream sockets
represent a declared external supply, not a claim that an isolated farm produces
water. Connected cases match their inlet/outlet positions and widths; the lined
terrace descent widens gradually and clears the measured native retaining steps.

Reference and fixture boundaries:

- All seven visible constructed Terrace Farm meshes preserve native positions,
  UVs, indices and transforms. Ordinary Farm props retain native geometry/UVs;
  the fixtures translate them into a farm corner.
- Flat fields use unchanged native `Crops_Africa` decal textures. Their polygons
  and placement are authored test fixtures, **not the engine's parcel layout**.
  No replacement flat parcels are included in the original irrigation exports.
- Desert, grassland, floodplain-bank and river materials are native references.
  Terrain diffuse alpha is a blend weight, so the review treats it as opaque;
  crop/floodplain alpha remains available. The review shader approximates diffuse
  appearance and does not reproduce Civ V's terrain/river shaders.
- Mountain shape samples the real `Afri_Mountain_1_1_H.dds` heightmap, with an
  explicitly authored 24-unit height range and neighboring-hex placement. Hill
  support terrain is a smooth authored fixture beneath the native wall skirts.
  Neither terrain placement nor height calibration is an engine capture.
- The shared review atlas only repacks/downsamples inspection pixels. Editable
  combined GLBs retain original texture images and source UVs. Irrigation uses
  the existing original painted atlas; proprietary extracts remain local.

The validator reads actual GR2/GLB output, checking finite/nondegenerate triangles,
unit normals, UV areas, format parity, unchanged native farm geometry, texture
provenance, closed end geometry, source-connected acyclic routes, non-rising
water and matching shared ports. It samples exported water triangle edges and
interiors against the exported fixture terrain. The concealed rock-face intake
is the sole rock-clearance exception: it emerges from the rock, while its outgoing
span must clear it. Samples outside fixture bounds use the surrounding zero datum
and are reported separately. Centerline/width joins are not a general proof of
watertight arbitrary terrain stitching.

This is representative terrain coverage, not every orientation, adjacency mask,
terrain deformation, construction state or pillaged state. Runtime native parcel
placement, dynamic art selection and in-game shader/distance acceptance remain
pending. Current flat-desert gameplay and Farm-art fallback are unchanged.


## Correction after native-model review

The user observed: “These seem to be very obviously not the original models with
slight modifications.” The seven terrain fixtures must not be treated as the
accepted native-art baseline. Actual native textures on invented parcel polygons
are not the original farm layout. The authored hill also changes the appearance
of the native terrace source, whose wall skirts are normally fitted by the game.

The viewer now defaults to the unchanged native Terrace Farm source, followed by
the same source plus the proposed irrigation and a view of the additions alone.
None of those three comparisons includes authored terrain or flat parcels. The
seven fixtures remain explicitly labeled diagnostics for geometric checks only.
Their source meshes are not approved artwork or proof of native game appearance.

`python tools/irrigation_native/audit_native_layout.py` reads the installed stock
art definitions and records provenance in ignored `native-layout-audit.json`.
It confirms that resource-free farms use the FARM layout handler and terrain
contouring, with Medieval_Farm1/2/3 or Modern_Farm1/2/3 wrappers. The earlier
Medieval_Farm.gr2 prop reference is used for the constructed wheat-resource farm;
it is not the exact resource-free farm variant. Terrace Farm uses SNAPSHOT with
terrain contouring enabled. The current offline viewer implements neither game
layout behavior. These are verified definition values, not inferred rendering
semantics or an in-game test.

Further design acceptance requires unmodified in-game farm baselines, followed
by irrigation-only changes retaining those placements, terrain fit and material
behavior. Do not replace that missing engine integration with more authored
field/terrain fixtures. The existing playable Farm-art fallback is unchanged.


### Regular farm selection correction

`import_native_farms.py` also imports the six resource-free Farm1/2/3 assets.
Their GR2 files bundle constructed, half-built and pillaged models. The preview
selects the constructed model by the names inspected in the file, including
Farm2's constructed `Med_Farm1` name; native round trips preserve all states.
`validate_native_import.py` verifies these selected buffers against the original
full graph. The normal farmstead decal is separate from the crop fields. The
import manifest records all four regular crop families from `farm_types.xml`;
only the game's `FARM` handler can currently provide verified parcel placement
and texture selection for a particular desert tile.


### Regular-farm irrigation candidates

After native import, run:

```sh
python3 tools/irrigation_native/build_regular_farms.py
python3 tools/irrigation_native/validate_regular_farms.py
```

Use the art Python environment with NumPy/Pillow. Outputs are in the ignored
`output/models/irrigated-farm-native-fit/regular-farm-review/`. The viewer shows
the constructed regular buildings with their original farmstead ground decals;
the irrigation checkbox reveals the unchanged underlying source. It deliberately
does not draw fabricated crop parcels. Actual stock crop textures and parcel
placement must be supplied by Civ V's `FARM` handler, which the six candidate art
rows preserve along with native scale, era/state selection and terrain contouring.
The candidate does not replace `farm_types.xml` or any crop DDS.

Twelve local source-derived GR2 files cover three ordinary variants in each of
the Ancient/Industrial bindings, wet and dry. A 418-triangle wet (348 dry) carrier
and branch append one material group to the constructed mesh in its original
local coordinate system. Native buildings, UVs, materials, stencil helpers,
skeletons, model names and HB/PL states are preserved. Actual crop seam routing,
terrain deformation, source socket connectivity, construction-state selection and
native shader/loading checks remain pending. The source socket is explicitly
unconnected in the offline candidate; this is not a finished hydraulic network.

These native-derived files are local tests, not distributable originals or a
playable mod package. Production Farm-art fallback and gameplay are unchanged.
The earlier diagnostic terrain cases now also use constructed regular Farm1 props,
but their authored field polygons remain historical fitting fixtures.


### Complete saved asset library

The regular-farm page contains only the latest building candidates. To recover
all earlier work in one place, run:

```sh
python3 tools/irrigation_native/build_review_library.py --history-root /path/to/checkout-with-earlier-outputs
python3 -m http.server 18769 --bind 127.0.0.1 --directory output/models/irrigated-farm-native-fit
```

The first command writes `output/models/irrigated-farm-native-fit/index.html`.
The historical checkout supplies `output/models/irrigated-farm-v1`, `-v2` and
`-v3`; the active irrigation checkout supplies native candidates, overlays and
versioned concept sheets. Missing source collections cause an explicit failure.
The local index contains eight collections (163 saved export entries, including
states/revisions and 11 original source references) plus six concept sheets.
Each historical mesh study has 36 exports, including construction, pillaged,
wet/dry and lower-detail variants. Components include aqueducts, intakes and edge
closures. Native terrain studies include seven wet/dry cases.

The builder creates local symlinks to the exact selected source folders and
copies only the interactive viewer HTML to add model-specific links and library
navigation. It does not regenerate geometry, overwrite historical source viewers,
copy proprietary art into releases, or alter approval records. Keep serving the
native-fit folder as the HTTP root. The historical checkout must remain available
while its linked files are viewed. Re-run the library builder after regenerating
any source collection. The regular viewer generator retains the library link.

`library/catalog.json` records every entry; `library/validation.json` records file
and model-link checks. The recovery pass checked 635 links. Browser visual QA was
unavailable because the browser tool denied URL access; static link checks and
JavaScript syntax checks do not establish browser rendering or native game art.


### Selected concept as actual models (2026-10-20)

The latest selection combines v3 structure with the native-overlay concept's
Civ V treatment. This adds a separate collection and preserves all earlier
outputs. After native import, run:

```sh
python3 tools/irrigation_native/build_concept_models.py
python3 tools/irrigation_native/validate_concept_models.py
python3 tools/irrigation_native/build_review_library.py --history-root /path/to/checkout-with-earlier-outputs
```

`concept-models/review.html` shows actual exported meshes at close and reduced
size beside the selected illustration, unmodified regular Farm1 import, native
Terrace Farm import and regional crop texture references. The library includes
24 GLB/OBJ/BR2 models: four terrain forms wet/dry, four wet LOD1 versions, eleven
connector/source parts and a connected district. The 23 individual candidates
also have experimental GR2 and FXSXML exports; the district is a GLB assembly.
DDS dependencies are at the collection root. Native files use a 30-unit-apothem
fixture scale; source GLBs use v3 normalized units. Neither establishes in-game
scale or terrain fit. The FXSXML files refer to flat VFS texture filenames;
copying just a GR2 without its wrapper and root DDS files is insufficient.

The tool retains v3 terrain/terraces, supplies real regular Farm1 buildings and
native crop/masonry/terrain pixels, reduces the flat network to one carrier and
two branches, closes exposed contour ends, and keeps descending hill feeders.
The original v3 generator keeps its previous default crop spacing and geometry.
Foliage/wood remain from the original v3 art. No native crop-family choice on
desert or engine-generated parcel layout is asserted. The original concept and
source meshes retain their own approval states.

Validation checks native-source hashes and packed pixels, original building
geometry under its uniform placement transform, GLB/OBJ/BR2/GR2 buffer parity,
normal/tangent frames, FXSXML dependencies, full-resolution DDS/PNG alpha parity,
water reachability/grade, clearance against exported terrain triangles and crop
UV continuity across shared tile edges. Native loading/material behavior,
dynamic adjacency, terrain contouring and performance are still unverified.
Construction/pillaged states and floodplain transitions remain earlier studies;
this pass does not claim their conversion to the newer treatment. All native-
derived outputs are ignored local candidates, outside playable package roots.

The review library includes this ninth collection when its manifest exists,
bringing the current inventory to 187 export entries. Earlier recovery counts
above describe the library before these actual concept-model candidates.
