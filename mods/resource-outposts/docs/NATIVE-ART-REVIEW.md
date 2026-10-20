# Native art integration review

Updated 20 October 2026. The user authorized native visual checks and integration.
All 24 approved source states have been converted and packaged without changing
their geometry or textures. Conversion reports and hashes reproduce the original
shared-tooling batch; all pass source comparisons and the independent OpenGR2
reader. The production art definitions now reference these native assets.

Batch manifest SHA-256:
`0242afa26004aeb9091fafaad002e3726c14577c6c53ab6e31f7dd7ad8e499ad`.
Profile: `civ5-building-static-v1`; 24 models, 45,080 triangles.
Runtime payload: 24 GR2, 24 FXSXML, 24 diffuse DDS and one shared SREF DDS.

## Native visual findings

All eight era sets passed flat-ground visual review: Ancient, Classical, Medieval,
Renaissance, Industrial, Modern, Atomic and Information. At scale 6, intact,
actual under-construction and actual pillaged models render distinctly with their
authored textures. Their footprints are comparable to the stock Fort. No obvious
missing textures, detached geometry or excessive gloss appeared in these views.
The native multi-figure warrior formation can overlap walls/roofs; the open center
does not change Civ V's unit formation.

Ancient and Information also passed mixed-terrain scenes: the intact model on a
hill, construction on a desert transition, a ruin in preserved forest and a
remembered intact site under fog. Terrain contact was stable in the tested views.
Forest naturally obscures much of the low ruin; this is an artificial stress
scene, not proof of normal build eligibility or feature clearing. Fog darkens the
remembered model. Native assertions verify that site is revealed but not visible.
These checks do not cover every terrain shape, camera angle or lighting condition.

[Review evidence](native-art-review.json) records game, model, texture and screenshot
hashes, observations and limits. [Conversion provenance](native-art-manifest.json)
retains the converter's original `native_game: unverified` field deliberately:
structural conversion and subsequent manual native review are separate evidence.
Screenshots, stock extracts and recovery backups remain in ignored local output.

## Production integration

`src/Art/Models/` contains only the 73 original native runtime files. The eight
hidden improvement art definitions use `Era=Any`, scale 6, `SNAPSHOT` and
`TerrainContour=0`. `RO_Eras` selects the claimant's stage. The public canonical
improvement uses the three Ancient states; its single build action uses shared
Ancient scaffolding in every era, then switches to the claimant's stage on
completion. The seven later scaffolds are packaged and reviewed, but are not
selected by separate worker actions. Native Fort definitions remain unchanged.

The production binding probe passed using actual SQL results, packaged art and
unchanged `RO_Eras.lua` with native engine objects. It advanced another claimant
through all eight eras while the active player stayed Ancient. Native assertions
verified the expected improvement types, intact/pillaged state, upgrade progress,
unchanged incomplete construction, neutral ownership, garrison position/damage/
movement, repeated-call idempotence and backwards claimant selection. The final
capture shows Information intact/pillaged art, Ancient public scaffolding and the
stock Fort completion sentinel. All runtime source hashes match the tested fixture.

This proves direct neutral-site era transitions and art binding. It excludes the
full claims ledger and automatic event chain, management UI, annexed city resource
links, economy and save/load lifecycle. WSDLC serialized the actual SQL results;
ordinary mod-menu activation was not exercised by this probe.

## Reproducing the scenes

`tools/outpost_native_review.py` prepares disposable native scenes from verified
conversions. Each includes an intact site with a warrior, actual build progress,
actual pillage and a stock Fort. Its Lua is under `tests/native/`, outside the
playable source tree. Guards reject ordinary maps, later saves and multiplayer,
and prevent duplicate setup.

```sh
python3 tools/outpost_native_review.py \
  --batch output/gr2-converted/outposts-review-v1 \
  --output output/gr2-research/outpost-fixtures-next
```

Use `--terrain mixed --era Ancient` (or `Information`) for terrain/fog review.
Terrain is set during map generation. A temporary observing unit reveals and then
leaves the fog site through native sight accounting. Do not use a negative delta
to `ChangeVisibilityCount`: the stock Lua binding converts it to a boolean, so
`-1` increases visibility. This was confirmed by an assertion failure in the old
fixture, corrected in `c2c934a`, and covered by a regression test.

Flat DLC fixtures: `output/gr2-research/outpost-dlc-v2/<Era>/`.
Corrected mixed DLC: `output/gr2-research/outpost-mixed-dlc-v4/<Era>/`.
Coordinates: intact `(8,8)`, construction `(10,8)`, pillaged `(8,10)`, Fort `(10,10)`
and remembered fogged site `(12,10)`. These visibility changes are fixture-only.

For the production binding probe:

```sh
python3 tools/outpost_native_production.py \
  --database <clean-BNW-database> --output <new-fixture-directory>
```

This serializes actual production SQL results into GameData XML for WSDLC and
copies the production art and `RO_Eras.lua`. The Fort is placed only after all
native assertions pass, providing a visible completion sentinel. Package fixtures
with the pinned WSDLC packer and run through the locked background harness in
[the converter README](../../../tools/civ5_gr2/README.md). Coordinate the shared
slot first; use a fresh evidence directory and verify restoration after each run.

## Attempts and verification limits

The first Ancient capture was obscured by first-contact diplomacy; limiting
fixture visibility fixed it. Information initially captured a loading screen,
and one later startup exited with code 255 before the scene. Its next run passed.
Earlier mixed-terrain runs were interrupted by desktop lock/capture failure and
restored. Steam readiness was reconfirmed on resumption; sign-in is not a blocker.
The first mixed fog fixture failed its native visibility assertion; the corrected
fixture passed for both tested eras. No failed or loading capture counts as visual
acceptance. All completed sessions restored the original game and user data.

Several flat captures used activation-only logging and a bounded timeout because
logs were buffered. Their images were inspected directly. Later mixed scenes used
the full diagnostic helper, reported `scene-ready`, captured and restored normally.
The game host and stock GameCore hashes are recorded in each review. No custom
GameCore, Windows, Wine or proprietary converter DLL is required for this mod art.
The final production run restored successfully; Civ V is closed, the shared lease
is released and both coordinated mod chats have received the release notice.

Offline checks passed: all 24 source mesh/archive checks, 37 Python tests, the full
Lua 5.1 suite (382 Outpost assertions), package build/hash/ZIP parity and installed
BNW database checks alone and in both Terrain load orders. The package validator
also checks all native asset hashes, FXSXML references, BuildingShader texture
bindings, DDS data and VFS imports against versioned conversion provenance.

Remaining campaign, UI, resource accounting, capture/annexation and save/load
acceptance is listed in [ERA-VISUALS.md](ERA-VISUALS.md) and
[OUTPOSTS.md](OUTPOSTS.md). These focused scenes do not replace those tests.
