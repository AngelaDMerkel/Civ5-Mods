# Player documentation requirements

The repository README and every mod README are for potential players. Keep them
short: explain the gameplay purpose, a few principal features, requirements,
current availability, and links to the player guide and installation instructions.
Do not lead with chat ownership, source folders, build commands, IDs or test reports.

`docs/GAMEPLAY.md` is the collection's player entry point. Each mod's
`docs/GUIDE.md` explains how to use its features. Terrain's separate
`docs/TRADE-GUIDE.md` covers trade in detail. Write in Civilization V terms:
technologies, production, gold, tiles, units, orders, yields and turns.

For each applicable unit, building and worker action, explain its purpose, unlock,
cost/upkeep, valid location, how to use it, result and important failure cases.
Use short tables and worked examples where they help. Distinguish base costs,
improvement yields and total tile yields. Preserve player-relevant limits such as
save compatibility, absent standard trade effects and unsupported game modes.

Include original project images with alt text and nearby captions. Clearly label
concept art, model previews and actual in-game screenshots; never imply a planned
model or terrain type is already playable. Reuse approved originals without
changing their approval status. New art follows the established selection process.
Images needed by GitHub docs must be versioned or use a stable permitted URL.

Keep source/API details, mesh formats, approval hashes, architecture and validation
procedures in development notes, technical specifications or testing documents.
Keep a discreet contributor link in the player entry points. Preserve technical
information when moving it out of a README.

Update player documentation alongside changes to gameplay. Document the currently
integrated behavior; do not advertise work that exists only on an unmerged branch.
For a planned mod, state that status and confirmed intent without inventing units,
values, controls or installation instructions. Check Markdown links, heading
anchors, image paths and factual agreement with the implemented rules before commit.
