# Local Fort GR2 reference

Purpose: measure native Civilization V static improvement records for the shared
[GR2 converter](../../tools/civ5_gr2/README.md), initially used by Resource Outposts.
No source art or runtime release ownership moves to the converter.

Origin: the user's installed macOS Civilization V app, relative archive path
`Contents/Assets/Resource/Common/ImprovementModels.fpk`. Six Fort GR2s, their
FXSXML wrappers and `improvementmodels_stringdatabase.gsd` are extracted by
`python3 -m tools.civ5_gr2 extract-fort <archive>` into ignored
`shared/references/local/fort/`. `provenance.json` there records the absolute local
origin, archive SHA-256 and all selected file hashes. No proprietary files are
versioned or included in authoring/release ZIPs.

The [research record](../../tools/civ5_gr2/RESEARCH.md) documents measured container,
vertex, rigid binding, material and wrapper interfaces, dependency licenses and
validation limits. Local decoded reports are under `output/gr2-research/`.
These references support compatibility investigation; they do not establish
visual approval or native acceptance of generated assets.
