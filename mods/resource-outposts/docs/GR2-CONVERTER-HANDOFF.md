# Shared native GR2 converter handoff

The converter belongs to **all mods** in `tools/civ5_gr2/`. Resource Outposts is
the first consumer. See [CLI/setup/validation](../../../tools/civ5_gr2/README.md)
and [measured format/dependency findings](../../../tools/civ5_gr2/RESEARCH.md).

## Confirmed state

- The locally owned Fort container, rigid vertex stream, bindings, shader records
  and hashed texture/string references have been inspected. Extracts stay ignored.
- The approved `RO_Ancient.br2` converts to an uncompressed GR2, FXSXML and two
  unchanged DDS files. Its 7,212 vertices / 2,404 triangles pass the internal
  source comparison and independent native OpenGR2 geometry check.
- The converter requires no Windows, Wine, Nexus Buddy or proprietary DLL at
  runtime. Native Python 3.10+ is enough; optional research tools use Apple clang.
- A generic hash-pinned batch interface and manifest for the 24 approved source
  states are available. Candidate generation does not establish rendering.
- A disposable native fixture uses unique `CG2_` identifiers and a stock Fort
  control. It is separate from registered releases and every mod's runtime.

**Native rendering remains unverified.** Do not replace production Fort bindings
with these candidates yet. Geometry approval, structural validation, conversion,
game load and visual acceptance are distinct. Approved source meshes, textures,
selection records and the source archive have not been redesigned or overwritten.

## Integration contract

The authoritative era-selection work is already committed on
`mod/resource-outposts` at `6efac5d`. Its `docs/ERA-VISUALS.md` supersedes the old
generated conversion notes that call selection unfinished. This tooling work does
not reimplement or replace that integration. Atomic/Information use Civ V's
`ERA_POSTMODERN` / `ERA_FUTURE` identifiers; the selected art rows use `Era='Any'`.

After native acceptance, bring the shared tooling commits from `main` into the
mod's worktree, run the pinned batch from the repository root, and integrate only
the accepted GR2/FXSXML/DDS runtime files into `src/Art/`. Use the existing era/state
art definitions and unique `RO_` names. Keep conversion manifests, reference
extracts, source models and test harness files out of playable packages. Rebuild
through `tools/build.py`, validate the package and run the mod's current era tests.

The initial BuildingShader profile uses one diffuse plus one explicit SREF for
every mesh. `RO_Era_BlackSpec.dds` is an unverified SREF candidate; the flat-normal
export is not consumed by this profile. Landmark scale is separate from preserved
source geometry. The fixture starts at scale 6 for measurement, not final approval.
Texture orientation, SREF response, lighting, shadows, fog, terrain contact,
construction/pillage states and all eight era selections need native review.

Other mod owners can supply their own pinned batch manifests and namespace. The
current profile requires a single identity bone with full root weights and rejects
unsupported rigs. It must not silently flatten a more complex Terrain or
Irrigation model. Add another tested shared profile if its measured needs differ.
