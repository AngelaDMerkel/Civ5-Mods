# Irrigated Farm instructions

Apply root instructions and shared requirements. Own irrigation connectivity,
farm rules, irrigation AI and agricultural art. Preserve current `RT_` identifiers
and save behavior during source organization; new names are not a reason to
break the current Terrain release.

The builder includes this `src/` in Terrain v2. UI/localization/construction-order
hooks still belong to Terrain; coordinate interface changes and run all gameplay
tests. Do not create a second copy of the feature or claim a standalone release.

Distinguish current flat-desert gameplay eligibility from approved terraced-hill
and tile-compatibility visual requirements. Record unimplemented differences.
Use the 2026-10-20 selected direction in
`shared/art/irrigated-farm/v3-civ5-direction/selection.json`: the v3 mesh study is
the structural baseline, and the selected native-overlay concept defines the
Civ V visual treatment. Realize these as editable geometry and native export
candidates. Use recognizable regular Farm buildings, crop materials, subdued
terrain and masonry. Native source geometry may be modified; original references
remain available for comparison. Do not present authored parcels as captured
engine-generated desert farms or regional crop families as desert-specific.

Keep irrigation legible between crop parcels. The latest review request places
channels between each flat-field plot texture: use narrow dividing ditches and
wider carriers, derived from the same parcel map, rather than extra crop-interior
channels. The earlier mostly-dry-seam layout remains design history.
Preserve terraces, consistent tile seams, finished exposed edges, height
transitions and source-connected, level or descending water flow. Reuse the
selected aqueduct design. V1/v2 and earlier selections remain historical records;
v3 is now selected as an approach, not a final accepted model.
Keep mesh tools in `tools/` and generated previews under `output/`. Proprietary
reference-derived candidates remain local. Design selection, geometry/export
checks, native conversion and in-game acceptance are separate states. Preserve
the current runtime Farm-art fallback until replacements pass native tests.

Historical R1 review hold (superseded for the exact R5 models by the approval below):
the user had not approved the new concept-model candidates. The 2026-10-20
checkpoint in `shared/art/irrigated-farm/v3-civ5-direction/model-review.json`
freezes their hashes. Hold further conversion, native testing and integration
until the user reviews them. Do not interpret concept approval as model approval.

The subsequent 2026-10-20 user request authorizes offline mesh revisions toward
geometric canals, flowing continuous walls and shallow aqueduct connections.
Use `tools/irrigation_native/build_concept_revision.py` for revision 2; it exports
only GLB/OBJ/BR2 into a separate folder. Keep the original checkpoint unchanged
and record the new unapproved hashes in `model-review-r2.json`. This request does
not lift the hold on native conversion, testing or integration.

The next 2026-10-20 review rejects the rounded gentle hill and requests ground
channels between the plot textures. R3 uses staggered straight retaining fronts,
a planted upper bench, and a common crop/ditch parcel partition. Run
`build_concept_revision.py --revision 3` and `validate_concept_parcels.py`.
Keep R1/R2 outputs and checkpoints intact. R3 remains an offline, unapproved
candidate; its review record is `model-review-r3.json`.


The subsequent review requests clearly geometric, angular hills, irrigation that
cascades down each step, and crops fitted within each elevated tier. R4 applies
this to GentleHill, SteepHill and RockyFoothill with straight trapezoidal benches,
two fitted crop parcels per tier and a central stepped channel through real
retaining-wall notches. R3 flat geometry stays unchanged. Build with
`build_concept_revision.py --revision 4`; run `validate_concept_cascades.py`.
Preserve R1-R3 checkpoints. Record R4 as unapproved in `model-review-r4.json`;
the native conversion/testing/integration hold still applies.


R4 was described as improved but unnatural/unrealistic. The R5 response keeps
angular terraces, fitted crops and cascading flow, while reducing the monument-
like symmetry: unequal bent fronts, lower exposed walls, finer native masonry,
narrower bare margins, and staggered drops on parcel divisions. These are design
proposals in response to the feedback, not new user approval. Build with
`build_concept_revision.py --revision 5`; validate with `validate_concept_hillsides.py`.
Preserve R1-R4 exports; record R5 as unapproved in `model-review-r5.json`.


On 2026-10-20 the user explicitly replied “Approved.” to the R5 review.
`shared/art/irrigated-farm/v3-civ5-direction/model-approval-r5.json` records the
approved source design and its exact 72 export hashes plus atlas hash. Preserve
`model-review-r5.json` and R1-R4 checkpoints as historical review records. The
model-review hold is lifted for these R5 models; native conversion, terrain fit,
dynamic placement and in-game acceptance remain pending. Keep the runtime Farm
fallback until native checks pass. Changed source geometry needs its own review.
