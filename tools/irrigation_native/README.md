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
No native base mesh has been decoded/imported in this pass. Source validation
checks exported geometry, grade, junctions, edge closure and aqueduct preservation;
it cannot validate terrain clearance without the native base. Current playable
flat-desert irrigation still uses the existing ordinary Farm art reference.

Run from the repository root with Python, NumPy and Pillow:

```sh
python tools/irrigation_native/build_overlays.py
python tools/irrigation_native/validate_overlays.py
```

Use `--quick` to omit preview renders or `--output PATH` to choose an output.
