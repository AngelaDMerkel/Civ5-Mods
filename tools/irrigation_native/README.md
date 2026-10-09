# Native farm irrigation overlays

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
