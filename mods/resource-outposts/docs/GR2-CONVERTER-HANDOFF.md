# Shared native GR2 converter handoff

The converter belongs to **all mods** in `tools/civ5_gr2/`. Resource Outposts is
the first consumer. See [CLI/setup/validation](../../../tools/civ5_gr2/README.md)
and [measured format/dependency findings](../../../tools/civ5_gr2/RESEARCH.md).

For subsequent consumer-side results, see [native art review](NATIVE-ART-REVIEW.md):
all eight era/state sets now have native visual evidence, along with two terrain
and fog scenes. The approved native models are integrated into the Outposts package.
The historical converter findings below describe the initial converter milestone;
the linked consumer review is authoritative for current acceptance and limits.

## Initial converter milestone

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

**Minimal native rendering is demonstrated for the Ancient constructed asset.**
The uncompressed GR2 rendered as a textured palisade/tower/roof beside a stock Fort
in background Aspyr Civ V at scale 6. The precise hash and screenshot evidence are
in the research record. All 24 variants then converted successfully and passed
independent OpenGR2 geometry checks in `output/gr2-converted/outposts-v1/`.

At that initial milestone, final visual acceptance and production era/state
integration were still outstanding. That one probe alone did not accept the batch.
Approved sources, textures, selection records and the archive remain unchanged.
The native runner uses the pinned external Lekmod background harness, a shared
test lock and the stock installed GameCore; it restores all temporary game files.
Startup is intermittent (two pre-scene SIGILL exits were observed), which is
recorded separately from the successful model-rendering result.

## Integration contract

The authoritative era-selection work is already committed on
`mod/resource-outposts` at `6efac5d`. Its `docs/ERA-VISUALS.md` supersedes the old
generated conversion notes that call selection unfinished. This tooling work does
not reimplement or replace that integration. Atomic/Information use Civ V's
`ERA_POSTMODERN` / `ERA_FUTURE` identifiers; the selected art rows use `Era='Any'`.

The Outposts worktree now includes the shared tooling commits and accepted runtime
files in `src/Art/Models/`. To reproduce conversion, run the pinned batch from the
repository root. Use the existing era/state art definitions and unique `RO_` names.
Keep conversion manifests, reference
extracts, source models and test harness files out of playable packages. Rebuild
through `tools/build.py`, validate the package and run the mod's current era tests.

The initial BuildingShader profile uses one diffuse plus one explicit SREF for
every mesh. The flat-normal export is not consumed by this profile. Landmark scale
is separate from preserved source geometry. The Outpost review retained scale 6
and `RO_Era_BlackSpec.dds`; the observed views show no excessive gloss. That scoped
review does not fully characterize SREF semantics, every face's texture orientation,
all lighting/shadows or every terrain shape. Refer to its precise acceptance limits.

Other mod owners can supply their own pinned batch manifests and namespace. The
current profile requires a single identity bone with full root weights and rejects
unsupported rigs. It must not silently flatten a more complex Terrain or
Irrigation model. Add another tested shared profile if its measured needs differ.
