# WSDLC identity reference

WSDLC is [AngelaDMerkel/Wir-Schaffen-DLC](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC).
The user requested that the mod collection build on its tone and colours.
Verified on 2026-10-09 at commit `950a329f57074dfd762e9c32aea7a67a3704b643`.

## Primary evidence

- [Main-menu artwork used by its README](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC/blob/950a329f57074dfd762e9c32aea7a67a3704b643/assets/wir-schaffen-dlc-main.svg).
- [Palette constants and Bauhaus light-theme description](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC/blob/950a329f57074dfd762e9c32aea7a67a3704b643/civ5_dlc_installer.py#L258).
- [SVG renderer](https://github.com/AngelaDMerkel/Wir-Schaffen-DLC/blob/950a329f57074dfd762e9c32aea7a67a3704b643/scripts/render_main_menu.py), which converts the application's RGB terminal colours into SVG fills.

The main-menu SVG uses Menlo, DejaVu Sans Mono, monospace; ochre ASCII lettering;
a warm cream surface; dark text; and bright yellow selection bars with teal and
coral labels. The collection adapts this light palette and straightforward,
playful geometric tone. It does not reuse the installer name or slogan.

## Exact colours

| Role | Source token | Hex |
| --- | --- | --- |
| Cream surface | `TUI_BACKGROUND` | `#FBF4DD` |
| Indigo text | `TUI_FOREGROUND` | `#1F263C` |
| Muted text | `TUI_MUTED` | `#56617F` |
| Ochre title | `TUI_YELLOW` | `#8C6900` |
| Yellow highlight | `TUI_YELLOW_BACKGROUND` | `#FFDD45` |
| Text on yellow | `TUI_SELECTED_FOREGROUND` | `#151720` |
| Teal accent | `TUI_CYAN` | `#216F82` |
| Coral accent | `TUI_RED` | `#D64B40` |

The machine-readable [palette record](wsdlc-palette.json) preserves source blob
hashes. These values agree between the application constants and README SVG.

The source SVG and its local render are cached in ignored
`output/branding-review/round-3/`. The comparison also uses the existing genuine
Civ V icon-design sheet credited to Russell Vaccaro, retained in the ignored
review cache. Game reference pixels are comparison material only and must not
be distributed with the collection. Original collection icons are separate SVG
geometry. The user identified E — Living Map as the preferred direction; see
[the current identity and selection record](../../art/collection-identity/README.md).
