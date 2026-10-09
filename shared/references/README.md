# Reference index

| Reference | Location | Use and status |
| --- | --- | --- |
| WSDLC palette and tone | [Branding reference](branding/README.md) | Exact colours verified from Wir Schaffen DLC source and README artwork |
| Existing UI styles and contexts | [UI index](ui/README.md) | Inspect working source; native acceptance still pending |
| Terrain portraits/action/wonder selections | [terrain-icons-round-3](../art/terrain-icons-round-3/selections.json) | User-selected original art; DDS source hashes in `exports.json` |
| Terrain source model approval | [rt-models](../art/rt-models/approved.json) | Exact approved hashes; native conversion pending |
| Eight Outpost eras | [outpost concepts](../art/outpost-era-concepts-v1/approved.json) | Original options plus era selections and mesh approval |
| Irrigated Farm concept | [irrigation art](../art/irrigated-farm/README.md) | Approved v6 concept; mesh refinements have separate acceptance |
| Construction and game APIs | [testing notes](../../docs/TESTING.md) and mod docs | Existing implementation evidence and manual checks |
| Climate investigation | [research status](../../mods/climate-change/docs/REQUIREMENTS.md) | Prior investigation findings, still requiring native experiments |

Legacy local reference caches remain at
`output/art-concepts/2026-10-09/round-3/references/` and in the existing `output/`
review directories. They are ignored and are not required for ordinary package
builds. New local extracts may use `shared/references/local/` (also ignored).

When adding a reference, record its origin (installed game asset path, URL or
user-provided file), the question it supports, and any redistribution restriction.
Store a description or locator for proprietary sources instead of committing the
asset. A clean clone will need locally supplied references for comparison tools
that explicitly depend on them.
