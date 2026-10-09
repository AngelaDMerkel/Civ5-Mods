# Native references for the Outpost icon review

Read-only reference inspection on 2026-10-09. These locators describe proprietary
game assets used for a local style comparison; the extracted pixels must not be
committed or distributed with the mod.

Installed macOS game asset root:

`~/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization V/Civilization V.app/Contents/Assets/`

| Asset | Origin under that root | Question supported |
| --- | --- | --- |
| `terrainicons` + index texture | `Resource/DX9/UITextures.fpk` | Improvement portrait style, circular aperture and relative glyph scale |
| `unitactions` + index texture | `Resource/DX9/UITextures.fpk` | Unframed construction glyph material, perspective and small-size detail |
| `sv_fort.dds`, `sv_tradingpost.dds`, `sv_citadel.dds` | `Resource/DX9/StrategicViewTextures.fpk` | Actual strategic-map icon treatment and padding |
| Fort/Trading Post improvement records | `Assets/Gameplay/XML/Terrain/CIV5Improvements.xml` | Native portrait indices 24 and 32 in `TERRAIN_ATLAS` |

The indexed UI textures were decoded by the existing local script
`output/art-concepts/2026-10-09/round-3/decode_references.py`; the reconstructed
pixel data was copied unchanged. Strategic-view DDS files were read from the
archive and decoded directly with Pillow. No source game files were modified.

The new local cache is
`output/art-concepts/2026-10-09/resource-outposts-round-1/references/`.
The gallery crops atlas cells with CSS and labels original references separately
from generated candidates. Native artwork is never used as production icon data.

See the mod's [icon review scope](../../../mods/resource-outposts/docs/ICON-REVIEW.md)
for proposed reuse and remaining implementation work.
