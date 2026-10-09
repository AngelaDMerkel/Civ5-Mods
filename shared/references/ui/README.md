# UI reference map

Current project references, inspected during the repository migration:

| Purpose | Source |
| --- | --- |
| Exposure/construction/irrigation/trade panels | [RT_Environment.xml](../../../mods/realistic-terrain/src/UI/RT_Environment.xml) and [callbacks](../../../mods/realistic-terrain/src/UI/RT_Environment.lua) |
| Outpost construction/overview/management | [RO_UI.xml](../../../mods/resource-outposts/src/UI/RO_UI.xml) and [callbacks](../../../mods/resource-outposts/src/UI/RO_UI.lua) |
| Runtime icon atlas bindings | [RT_Art.sql](../../../mods/realistic-terrain/src/SQL/RT_Art.sql) |
| Approved icon crops, options and painting | [selection manifest](../../art/terrain-icons-round-3/selections.json) |

Both existing contexts use `Beige_Black`, `TwCenMT16`, `FontStyle="Shadow"`,
`Grid9DetailFive140`, `BaseButton`, native scrolling controls, and 18/22-point
title variants. Use those definitions as project references while checking
native controls in the installed game's `Assets/UI/` tree when needed.

The portrait atlas exports cover 32, 45, 64, 80, 128, 214 and 256 pixels. Worker
action icons cover 32, 45 and 64; the wonder splash is 976×576. These dimensions
describe the current exporter, not a rule that every future asset uses all sizes.

Reference-only native atlas decodes used in prior comparisons remain in ignored
`output/art-concepts/2026-10-09/round-3/references/`. Do not copy them into runtime
art or the repository. Add new reference provenance to the parent index.
