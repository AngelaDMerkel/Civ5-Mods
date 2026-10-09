# Shared art and mesh requirements

The established user direction is to match Civ V's art style and the approved
concepts closely. More polygons or larger textures alone do not establish a match.

## Selection and approval

For additional icons or artwork, present multiple options beside genuine Civ V
references, record the user's choice, and integrate the chosen source. Preserve
the original image, generation prompt, selection/crop information and hashes.
An approval applies only to its recorded scope. Layout cleanup and deterministic
exports of an already selected image do not create a new selection.

Match approved architecture: silhouette, footprint, massing, gates, roof profile,
materials and identifying details. Use actual mesh renders in comparisons. Show
normal map-scale views as well as close-ups. Do not silently simplify approved
architecture or replace it with a newly generated interpretation.

## Production and verification

Builders and mesh support code live in `tools/`. Editable/generated mesh kits and
previews live in `output/`; selected non-reproducible source images and approvals
live in `shared/art/`. Runtime-ready assets belong in the owning mod's `src/Art/`.

Check geometry, UVs, normals/tangents, texture seams, scale, state variants and
archive parity with the corresponding validator. Check tile adjacency/height
transitions for farms, garrison clearance for outposts, and rigging/animation for
units. Record measured budgets; do not invent a universal Civ V triangle target.

Keep these stages separate:

1. User approval of a concept or source model design.
2. Successful geometry/material/export validation.
3. Native GR2 conversion, engine material setup and runtime integration.
4. In-game visual review, including scale, terrain fit, state changes and lighting.

The first two stages do not establish the last two. Keep existing runtime
fallbacks until their replacements pass the relevant native checks.

## Provenance

Native textures/screenshots are reference material. Keep extracted game files in
ignored local caches, record where they came from, and exclude them from source
bundles and playable releases. Include original project art only with its source
and approval record. Do not rewrite approval hashes to make changed exports appear
approved; record the change and obtain the relevant design review.
