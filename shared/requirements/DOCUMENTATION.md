# Player documentation requirements

The repository README is the home of **AngelaDMerkel's custom Civilization V mods**.
Give each mod its own brief overview with a relevant image, a modest amount of
gameplay information, current availability and a direct link to its detailed guide.
Name the author and collection clearly; do not reduce the page to a generic theme
description or a directory table. A collection overview can be longer than an
individual mod's introduction while remaining easy to scan.

Every mod README is also for potential players. Keep these introductions short:
explain the gameplay purpose, principal features, requirements, current availability,
and links to the guide and installation instructions. Keep chat ownership, source
folders, build commands, IDs and test reports in contributor documentation.

Each mod has **one public documentation page**, `mods/<mod>/docs/GUIDE.md`.
Begin with the mod's goals, explain what it adds, then give the technical gameplay
details of how its features work. Keep Terrain's trade system within that same
page. Use section links to help readers navigate longer guides. Shared installation
and compatibility information belongs in `docs/GAMEPLAY.md`, which links to the
four guides. Contributor notes are separate from these public guides.

Write in Civilization V terms: technologies, production, gold, tiles, units,
orders, yields and turns. Explain mechanics thoroughly without turning the player
guide into source-code or development-tool documentation.

For each applicable unit, building and worker action, explain its purpose, unlock,
cost/upkeep, valid location, how to use it, result and important failure cases.
Use short tables and worked examples where they help. Distinguish base costs,
improvement yields and total tile yields. Preserve player-relevant limits such as
save compatibility, absent standard trade effects and unsupported game modes.

Include original project images with alt text and nearby captions. A simple
explanatory diagram can illustrate a planned feature when project artwork is not
available; identify it as a diagram rather than a screenshot or approved art.
Clearly label concept art, model previews and actual in-game screenshots; never
imply a planned model or terrain type is already playable. Reuse approved originals
without changing their approval status. New art follows the established selection process.
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
