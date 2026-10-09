# Native art integration review

The user authorized native visual checks and model integration on 9 October 2026.
The shared converter is available on the Outposts branch. All 24 approved source
states have been converted again in this worktree, without changing geometry or
textures. Their complete conversion reports and output hashes exactly reproduce
the shared tooling chat's `outposts-v1` batch. All pass the independent OpenGR2
reader and source comparisons.

Batch manifest SHA-256:
`0242afa26004aeb9091fafaad002e3726c14577c6c53ab6e31f7dd7ad8e499ad`.
Profile: `civ5-building-static-v1`; 24 models, 45,080 triangles.

## Review preparation

`tools/outpost_native_review.py` prepares eight isolated native scenes from the
converted batch. Each uses actual construction progress and native pillage state,
an intact outpost with a warrior, and a stock Fort for scale comparison. The Lua
fixture is owned under `tests/native/`, outside the playable source tree. Guards
reject ordinary maps, later saves and multiplayer, and prevent duplicate setup.

```sh
python3 tools/outpost_native_review.py \
  --batch output/gr2-converted/outposts-review-v1 \
  --output output/gr2-research/outpost-fixtures-v1
```

Use the pinned WSDLC packer and shared background runner described in
[the converter README](../../../tools/civ5_gr2/README.md). The eight prepared DLC
directories are under `output/gr2-research/outpost-dlc-v1/<Era>/`; they have not
been installed. Run one at a time under the shared native test lease, preserving
and restoring the installed game and user data. Use a new evidence directory per
attempt and inspect screenshots; a placement log alone is insufficient.

Scene coordinates: intact `(8,8)`, construction `(10,8)`, pillaged `(8,10)`, stock
Fort `(10,10)`. Initial display scale is 6. Visibility is increased only in the
disposable scene to keep the comparison unobscured; this is not a production fog
change. The fixture removes random goody huts before revealing the test map and
disables yield overlays for visual inspection.

## Acceptance boundary

The prior Ancient constructed probe demonstrates basic native loading. It does
not establish acceptance of all eras/states. Native review for this pass is
pending coordination with other chats using the same installation. Production
Fort placeholders remain until their replacements pass those checks.

For every era, record the exact model/texture hashes, game identity, screenshot,
state selection, scale, terrain contact, lighting, material appearance and visible
defects. Follow with terrain/fog checks and a production integration probe. Keep
local game screenshots and recovery journals ignored; record findings here.

Once accepted, integrate only GR2/FXSXML/DDS into `src/Art/`, update the existing
art rows and placeholder assertions, rebuild and validate. Preserve one public
build action. Completed and pillaged stages already follow the claimant's era;
claimant-specific construction visuals are a separate unresolved integration
detail, as explained in [ERA-VISUALS.md](ERA-VISUALS.md).

Offline checks completed: deterministic full batch, 36 Python tests including
scene guards, full Lua 5.1 suite (382 Outpost assertions), package build/hash
parity, and installed BNW database checks alone and in both Terrain load orders.
These checks do not establish native visual or gameplay acceptance.
