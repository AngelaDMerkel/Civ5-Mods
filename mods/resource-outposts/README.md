# Resource Outposts

Owned by the **Resource Outpost** chat. Runtime source is in `src/`, tests in
`tests/`, and detailed rules/acceptance checks in [docs/OUTPOSTS.md](docs/OUTPOSTS.md).

Current release: Resource Outposts v1, independent single-player BNW alpha; UUID
`4547ae42-3d17-4993-99e8-a7a5a2c1ec2c`. It owns resource claims, maintenance,
garrisons, management UI, abandonment/conversion and outpost AI.

Extraction and optional shelter never require roads, supply connections, trade
agreements or Ministry of Coin. Terrain integration only adds optional shelter.
The current package blocks the old Terrain v1 that bundled outposts.

The eight revised era designs are approved in
`shared/art/outpost-era-concepts-v1/approved.json`. Shared mesh builders and
validators stay in `tools/`; generated models stay in `output/models/outpost-eras-v1/`.
Automatic claimant-era selection is implemented for completed and pillaged
outposts, including capture, annexation and reload. Eight internal variants retain
one public build action and Civilopedia entry. Construction keeps its existing
progress and selects the current era on completion. All 24 approved native model
states are now packaged, replacing the Fort placeholders. They passed independent
conversion checks and [native visual review](docs/NATIVE-ART-REVIEW.md) for all
eight eras, plus Ancient/Information terrain and fog scenes. The public build uses
one shared Ancient scaffold; completed and pillaged sites use their claimant's era.
Focused native [gameplay and save/load checks](docs/NATIVE-GAMEPLAY-TESTS.md),
AI construction/guard/repair, healing and reassignment, controlled escort loss
and resumption, and optional roadless Terrain shelter now pass. Broader campaign
and mouse-driven UI acceptance remain separate. Implementation,
compatibility and conversion handoff: [docs/ERA-VISUALS.md](docs/ERA-VISUALS.md).

The user-selected **Guarded storehouse B** emblem and construction glyph are
exported and integrated into Civilopedia portraits, construction controls,
management panels and strategic view. [Icon records](docs/ICON-REVIEW.md) preserve
the originals, selection and export hashes. The management emblem has been
observed in-game; construction, Civilopedia and strategic-view icon acceptance
remains pending. Notifications retain their existing generic symbol.

Build and validation commands are in the [root README](../../README.md).
