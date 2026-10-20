# Shared support tools

Run commands from the repository root. This directory is separate from all mod
runtime source; model builders/viewers are support tools even when they serve
one mod. Do not move them into a playable package.

| Task | Builder/exporter | Validation | Output |
| --- | --- | --- | --- |
| Current playable releases | `python3 tools/build.py` | `python3 tools/validate.py` | Complete projects in `build/`, packages in `dist/` |
| Gameplay tests | — | `.venv/bin/python tools/test.py` | Lua 5.1 assertions against production files |
| Selected Terrain 2D art | `tools/export_art.py` | Decodes exports; package validator checks bindings | `mods/realistic-terrain/src/Art/` |
| Selected Outpost 2D art | `tools/export_outpost_icons.py` | Verifies approved hashes and lossless DDS readback; package validator checks bindings and native Fort preservation | `mods/resource-outposts/src/Art/` |
| Historical first mesh pass | `tools/build_models.py` | `tools/validate_models.py` | `output/models/first-pass/` |
| Approved Terrain source models | `tools/build_models_v2.py` | `tools/validate_models_v2.py` | `output/models/revised-v2/` |
| Terrain comparison sheets | `tools/review_models_v2.py` | Checks original art hashes | `output/model-review/approved-art-alignment/` |
| Approved Outpost era models | `tools/build_outpost_era_models.py` | `tools/validate_outpost_era_models.py` | `output/models/outpost-eras-v1/` |
| Shared static GR2 conversion (experimental) | `python3 -m tools.civ5_gr2 convert` / `batch` | `verify`, optional independent OpenGR2 probe; native rendering is separate | `output/gr2-converted/`; [CLI and renderer fixture](civ5_gr2/README.md) |
| Irrigation mesh kit v1 | `tools/build_irrigation_meshes.py` | `tools/validate_irrigation_meshes.py` | `output/models/irrigated-farm-v1/` |
| Irrigation mesh refinement v2 | `tools/irrigation_v2/build_irrigation_meshes.py` | `tools/irrigation_v2/validate_irrigation_meshes.py` | `output/models/irrigated-farm-v2/` |
| Irrigation v3 structural study (selected approach) | `tools/irrigation_v3/build_irrigation_meshes.py` | `tools/irrigation_v3/validate_irrigation_meshes.py` | `output/models/irrigated-farm-v3/` |
| Approved R5 native conversion | `tools/irrigation_native/convert_approved_r5.py --probe /path/to/independent-probe --render` | Same tool with `--verify-only`; GR2/source parity, independent reads and actual readback previews | `output/models/irrigated-farm-native-fit/native-r5/` |
| Unequal hillside terraces (R5 source design approved) | `tools/irrigation_native/build_concept_revision.py --revision 5` | `tools/irrigation_native/validate_concept_hillsides.py` | `output/models/irrigated-farm-native-fit/concept-models-r5/` |
| Angular hill tiers and cascades (R4, unapproved) | `tools/irrigation_native/build_concept_revision.py --revision 4` | `tools/irrigation_native/validate_concept_cascades.py` | `output/models/irrigated-farm-native-fit/concept-models-r4/` |
| Straight gentle terraces and parcel channels (R3, unapproved) | `tools/irrigation_native/build_concept_revision.py --revision 3` | `tools/irrigation_native/validate_concept_parcels.py` | `output/models/irrigated-farm-native-fit/concept-models-r3/` |
| Revised irrigation geometry (offline, unapproved) | `tools/irrigation_native/build_concept_revision.py` | `tools/irrigation_native/validate_concept_revision.py` | `output/models/irrigated-farm-native-fit/concept-models-r2/` |
| Selected irrigation concept: actual mesh/native candidates | `tools/irrigation_native/build_concept_models.py` | `tools/irrigation_native/validate_concept_models.py` | `output/models/irrigated-farm-native-fit/concept-models/` |
| Native farm irrigation-only overlay study (unapproved) | `tools/irrigation_native/build_overlays.py` | `tools/irrigation_native/validate_overlays.py` | `output/models/irrigated-farm-native-overlay/` |
| Regular native farm irrigation candidates (unapproved) | `tools/irrigation_native/build_regular_farms.py` | `tools/irrigation_native/validate_regular_farms.py` | `output/models/irrigated-farm-native-fit/regular-farm-review/` |
| Native-art irrigation terrain and junction review (unapproved) | `tools/irrigation_native/build_terrain_cases.py` | `tools/irrigation_native/validate_terrain_cases.py` | `output/models/irrigated-farm-native-fit/terrain-review/` |

Python files in this table are run with the Python interpreter for the appropriate
environment. Packaging/validation use the standard library. Gameplay tests need
`tests/requirements.txt`; mesh generation and art comparisons need
`tools/requirements-art.txt`. Module files such as `model_*`, `outpost_*` and
`irrigation_mesh_io.py` support those entry points. The `irrigation_v2/refine_*`
modules are part of its active refinement pipeline; see its mesh notes before use.
The v3 pipeline adds `natural_farms.py`, a versioned original painted atlas under
`shared/art/irrigated-farm/mesh-v3-review/`, alpha-aware rendering, and
`tools/irrigation_v3/render_flow_review.py`. Run the latter after the v3 builder
to inspect annotated, source-connected water routes. Its source/export validation
also samples channel beds against the exported terrain; it does not validate
native GR2 materials, runtime art placement or fluid simulation.

Selected source art is under `shared/art/`. Review tools may additionally require
ignored, locally supplied stock references; consult `shared/references/README.md`.
Ordinary package builds use versioned DDS assets and do not need those references.
Model/source ZIPs are authoring bundles, not installable Civ V mods.

The native-farm overlay study reuses the v3 exporter and aqueduct source without
exporting replacement fields or terrain. Its validator checks closed/open edges,
neighbor-link selection, format parity and preserved aqueduct geometry. Actual
native farm mesh fitting and terrain clearance are not yet validated.


Native irrigation source work now also has `irrigation_native/import_native_farms.py`,
`validate_native_import.py`, `build_native_fit.py` and `validate_native_fit.py`.
See [the native pipeline notes](irrigation_native/README.md) for the required
installed-game path, compiler and sequence. These tools import eleven real native
Farm/Terrace Farm sources, including all six ordinary Farm1/2/3 variants, and
build the first constructed-terrace irrigation addition. All extracted art remains in ignored `output/`; the original overlay
exports are separate. Native engine acceptance is still pending.

The terrain-case builder runs after native import and first fitting. It exports
seven wet/dry fitting cases using preserved native terrace meshes and native
crop/terrain textures in authored terrain fixtures. Its validator checks actual
exported water geometry and hydraulic connections. The offline viewer exposes
separate terrain, farm and irrigation layers. These checks do not validate the
game's procedural flat-farm placement or dynamic terrain/adjacency art.

The regular-farm builder runs after native import. It adds a material group only
to the constructed stock building mesh, retaining the original farmstead decal
and all native construction states. Its twelve wet/dry GR2 candidates, wrappers,
and six FARM/terrain-contour art rows remain in ignored local output. The validator
checks complete source-graph preservation after removing the appended group,
GR2/GLB parity, building clearance, descending routes and closed outlets. It does
not establish native crop-parcel fit. No crop texture or `farm_types.xml` override
is generated; the proposed binding relies on the normal game layout.
