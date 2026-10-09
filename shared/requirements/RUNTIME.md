# Common runtime requirements

Baseline: Civilization V: Brave New World, single player, Lua 5.1, SQL/XML mods,
and macOS support without a custom gameplay DLL. Existing packages do not claim
multiplayer, hotseat, vanilla/Gods & Kings, or overhaul compatibility.

Native-edition direction, 2026-10-09: one project-owned GameCore with optional
modules for the four repository mods. Reuse existing gameplay/platform work;
do not require WSDLC or an overhaul. This does not change the stock-core baseline
of the current packages. See [shared architecture](../../docs/SHARED-GAMECORE.md).

- Preserve stable package UUIDs, save keys, database types, localization tags and
  public Lua/event names. Describe migrations before changing saved state.
- Keep companion integrations optional. Test a mod alone and with each currently
  supported companion; SQL load order must not decide correctness.
- Save persistent gameplay state. Make turn processing safe against duplicate
  events and reloads. UI refreshes must not advance gameplay or grant benefits.
- Apply the relevant rules to human and AI players. Check player/turn ownership,
  current eligibility and visibility again when an action executes.
- Keep hidden-map and other-player information out of UI and AI decisions that
  should use the player's knowledge.
- Keep source ownership separate from release composition. Add runtime files only
  through registered `src/` roots, without copies in sibling mods.
- Keep stock references, development tools, tests and generated previews out of
  playable packages. Game databases are read-only validation inputs.

Existing intentional boundaries: Resource Outposts extraction has no road, supply,
trade-agreement or Ministry requirement; optional Terrain shelter is a separate
effect. Irrigation's present Terrain coupling is documented in
`docs/DEVELOPMENT.md` and is not a standalone release dependency contract.
