# Climate requirements and research status

Captured from the Climate Change Mod discussion on 2026-10-09. No runtime code
was present during repository organization.

## Confirmed user requirements

- Terrain changes over time as a climate factor develops.
- Include natural shifts throughout history and industrial-era human activity;
  higher city populations influence the changes.
- A game has one permanent direction: continued warming or continued cooling.
  Rate may vary; the long-term direction must not reverse.
- Investigate ways to change tiles during a game.

## Proposals that still need design decisions

Local susceptibility, transition thresholds, advance warnings, industrial
emission weights, cleaner infrastructure, vegetation effects and exact terrain
transition chains were discussed as proposals. Industry slowing cooling without
reversing it was an assistant recommendation, not a separately approved rule.
Do not add these to the confirmed requirement list by inference.

## Prior investigation and next experiment

The earlier chat inspected BNW source, existing mods and installed Mac assets.
It reported that terrain properties can change at runtime, but ordinary land
texture refresh may lag until reloading. Vegetation changes had stronger visual
precedents. An installed `Ice_Reload()` debug hook was identified as an experiment
candidate, not a demonstrated gameplay solution. Land/water conversion may clear
cities, resources, improvements and units and needs explicit protection rules.

These are inherited research findings, not new verification by the repository
migration. Existing local notes/source extracts remain in the temporary directory
`/tmp/civ5-climate-investigation` and may disappear; preserve any evidence needed
for implementation in a focused research note with source provenance.

The next native experiment should compare snow-to-tundra, grassland-to-desert,
vegetation and ice changes. Record yields, passability and visible terrain before
the change, immediately after, and after save/reload. Evaluate the ice hook
separately. A climate overlay was proposed for immediate feedback; it remains a
design option. Do not claim native visual support until observed.
