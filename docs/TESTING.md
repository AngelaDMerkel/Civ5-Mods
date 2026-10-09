# Verification and manual play-test

## Completed automatically

- Execute the real rules and game adapter in Lua 5.1, with mocked game APIs.
- Check threshold boundaries for all four environments, half-turn forest shelter,
  independent counters, safe recovery, water relief, and no stacking.
- Check the 25% health floor, damaged units below it, and nonstandard maximum HP.
- Check duplicate events, context reloads, persisted counters, and no repeated damage.
- Check owner-relative protection, team supply, hostile occupants at oases,
  open-border access, rivers, lakes, flood plains, and saltwater rejection.
- Check scout/medic/technology support, embarkation, AI parity, exemptions,
  outside-territory upgrade transfer, home upgrades, and reused unit IDs.
- Verify Caravansary road connectivity, including the station tile's road,
  mixed roads/railroads, gaps, pillage, water/mountain rejection, enemy blockades,
  alternate routes, loops, capture, neutral builder persistence, own-city endpoints,
  one-tile radius, AI parity, and clearing actual combat promotions at the next turn.
- Run the actual UI bootstrap and selection/city-screen handlers against mock
  controls; verify that UI callbacks do not advance gameplay.
- Check the Ministry construction gate, technology, turn ownership, terrain,
  competing orders, worker movement, speed modifiers, partial progress after Lua
  reload, loss/rebuilding of the Ministry, and neutral-land builder attribution.
- Validate the Ministry's one-per-player class, national-wonder flags and costs,
  and exact preservation of native city trade modifiers.
- Validate SQL promotions, text XML, atlas references, and package hashes against
  read-only copies of the installed Brave New World databases.
- Decode all eleven selected DDS exports without pixel loss; validate atlas
  dimensions, legacy alpha format, VFS paths, database bindings and ZIP inclusion.
- Check the Ministry completion-art trigger: local human only, setup/other
  buildings ignored, duplicate events and reloads suppressed, later rebuild allowed.
- Check eight source map meshes in OBJ, GLB and BR2: nondegenerate triangles,
  normals, UVs, rigid weights, embedded texture bounds and source-archive parity.
  These checks do not establish GR2 compatibility or in-game model rendering.
- Check the 24 outpost era/state meshes mapped to approved concepts with
  `tools/validate_outpost_era_models.py`: approval mapping, finite geometry,
  triangle winding, atlas UVs, orthogonal tangent frames, rigid weights, exact
  OBJ/GLB/BR2 geometry agreement, embedded texture, empty central garrison square,
  footprint limits, distinct state geometry, per-mesh baked diffuse textures,
  legacy DXT1 headers/full mip chains, and source archive parity.
  GR2 conversion and automatic claimant-era visual switching remain pending.

These checks validate logic and data compatibility. They do not replace an actual
game launch. Native UI layout, engine event ordering, and AI behavior are still
pending.

## Manual acceptance checklist

Connected irrigation has additional automated coverage and a native acceptance
checklist in [IRRIGATION.md](IRRIGATION.md). Its turn-boundary hooks must be checked
against actual city food processing, including an unseen enemy pillage.

Use a new disposable single-player BNW game. For deterministic terrain placement,
a WorldBuilder test map or a separately installed editor can help; neither is
required by this mod. Enable Lua and database logging in `config.ini` if desired,
then inspect `Logs/Lua.log` and `Logs/Database.log` after loading.

- [ ] The mod appears in Mods and can be enabled with BNW active.
- [ ] Logistics displays Mountain passage in the tech tree and Civilopedia.
      Ministry uses Counting house in city production and the Wonders category.
      Caravansary uses Roadside gateway in the Civilopedia improvement entry.
- [ ] Build Caravansary shows the Well and shelter glyph, with readable text in
      enabled, disabled and Cancel construction states; native Fort art is unchanged.
- [ ] Completing the Ministry displays Treasury arrival with the correct title,
      bonuses and portrait. Closing works; AI completions, captures and save loads
      do not show the painting again. No missing DDS or atlas errors appear.
- [ ] Start a new game; find `Realistic Terrain v2 initialized` in Lua.log with no
      runtime errors. No `PROMOTION_RT_*` or `TXT_KEY_RT_*` database errors.
- [ ] The Environment panel fits at the chosen resolution, shows only for the
      active player's land military selection, hides in cities, and has a tooltip.
- [ ] A non-scout unit on unsupported desert is ready after checks 1–2,
      strained after 3–4, and exhausted with damage after check 5.
- [ ] Tundra is ready for 3 checks; jungle for 4; snow for 1. Account for technology
      and medic bonuses before comparing results.
- [ ] Combat preview reflects exactly one environmental modifier: -10% or -20%.
      Include a ranged unit as well as a melee unit.
- [ ] An adjacent unoccupied oasis clears heat at the next turn check. Passing it
      and leaving during one turn does not clear heat.
- [ ] River, lake, floodplain, closed-border oasis, and enemy-held oasis cases agree
      with README rules; no unrevealed enemy information leaks through the panel.
- [ ] Entering home territory immediately clears the status, without healing HP.
      Capturing a city or acquiring a tile also protects stationary friendly units.
- [ ] Embarking pauses exposure/damage and removes land modifiers. Landing restores
      retained exposure. Include a save/reload while embarked.
- [ ] Safe recovery eventually clears status; repeated damage cannot pass the 25%
      health floor. Compare ordinary healing and Medic-assisted healing.
- [ ] Save on an exhausted unit's turn, reload, and verify no second damage tick.
- [ ] Upgrade at home; try an ancient-ruins upgrade outside home; verify state transfer.
      Capture/conversion to another owner intentionally begins fresh exposure.
- [ ] Play at least 50 turns with AI opponents on a harsh map. Check exploration,
      invasions, city-state units, notification frequency, and turn-processing time.
- [ ] Re-test Quick and Marathon operational pacing; neither scales grace periods.
- [ ] At Horseback Riding, find Ministry of Coin in the national-wonder list.
      The former ordinary city Caravansary must not remain available separately.
      Build the Ministry; a second city must not be able to build a second copy.
- [ ] Compare routes originating in the Ministry city and another city: only the
      Ministry city receives the original +50% land range and +2 land-route gold.
- [ ] At Engineering without a Ministry, select a worker: the top-center Build
      Caravansary control is disabled with a clear prerequisite tooltip. Ordinary
      worker actions must not offer an ungated way to build the improvement.
- [ ] With both requirements, click Build Caravansary: movement is consumed and
      progress increases. Verify automatic work next turn through completion;
      cancel and move away to interrupt. Test a partial move,
      worker-speed bonuses, game speeds, save/reload and a different worker
      resuming construction. Check forest/jungle preservation and feature techs.
- [ ] Lose the Ministry city during partial construction: work is blocked until
      the Ministry is rebuilt. Existing supplied Caravansaries continue operating.
- [ ] Check the new construction panel at different resolutions, city screen
      entry/exit, worker selection, and turn changes. Tooltip explains the lock.
- [ ] Build a road on the station and along every tile to one of your cities.
      An exhausted army on or adjacent to it should clear all exposure next turn.
      Merely previewing, passing nearby, or receiving a duplicate turn event must
      not clear exposure early. Confirm HP is not restored by resupply.
- [ ] Remove/pillage a road, pillage the station, or block a segment with an enemy.
      Verify relief stops; repair or use an alternate path to restore it. Capture
      the station or endpoint city and confirm ownership changes affect supply.
- [ ] Save and reload a neutral-land station. Confirm the builder retains control.

## Implementation notes

Gameplay runs through `GameEvents.PlayerDoTurn` for every owner, with a per-unit
processed-turn guard. `UnitSetXY` updates immediate home protection and positions.
The registered city/border/technology hooks refresh protection and tolerance.
Each player's namespaced `Modding.OpenSaveData` record is saved with the game.

The state identity includes owner, unit ID, creation turn, type, and original owner.
Dead entries are pruned at the owner's turn. Stock Civ V lacks a universal upgrade
event; the adapter transfers an orphaned predecessor only when birth turn, original
owner, tile, and an actual database upgrade path match unambiguously. Conversions
implemented by other mods may need an explicit compatibility adapter.

Custom DLLs, UI overhauls, and multiplayer have not been validated. A native
single-player run must pass before calling this release verified or publishing it.

### Ministry construction implementation

Stock BNW has no building prerequisite on `Builds` and no `PlayerCanBuild` veto.
`RT_Construction.lua` checks current ownership of `BUILDING_CARAVANSARY` (now the
Ministry) and legal plot/worker/technology state on start and every automated work
step. It uses
`WorkRate(false)`, `FinishMoves()` and `ChangeBuildProgress(build, work, player)`;
the latter handles native terrain work time, game speed and improvement placement.
Because completion does not run through a native unit mission, the adapter records
the neutral-land builder explicitly. There is no custom DLL or hidden technology.

The original building and improvement identifiers stay stable, while localization
and national-wonder class data change. Existing multi-Caravansary saves are not
migrated; use a new game. Selected 2D portraits and the painting are integrated;
3D city/improvement art retains the stock fallbacks until model conversion/testing.

Primary API references: [unit construction](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvUnit.cpp),
[plot build validation and progress](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvPlot.cpp).
The installed Mac BNW binary also contains `BuildFinished`, `CityConstructed`, and
`CountNumBuildings`, but no `PlayerCanBuild` event string. Actual engine/UI execution
is still subject to the native acceptance tests above.

## Resource Outpost acceptance tests

Automated tests execute resource ownership/accounting, construction orders, AI
expeditions, escorts, wounded replacement, variable budgets, production, repairs,
capture, upkeep, abandonment, notification deltas and UI handlers. Refinement tests
cover stalled expeditions/cooldowns, nearest safe healing and native rest orders,
percentage health, resource-loss previews, territorial conversion and overview actions. Isolated Lua
contexts test optional shelter and construction/AI coordination. Both packages
work alone; combined shelter never needs roads. Database validation checks all
24 land resources, package isolation and both SQL load orders. ZIPs match source.
The rules, implementation details, native limitations and remaining in-game
acceptance checklist are in [OUTPOSTS.md](OUTPOSTS.md).

## Replacement trade acceptance tests

Automated tests now cover real Lua route creation, investment and return of trade
units, movement, payment guards, save reload, agreement revocation and war, city
capture, roadless-territory death, Logistics exceptions, patrol activation and
pillage, sea/ocean access, domestic food delivery, AI worker commands, and planner
controls. Pure-rule tests cover relay reachability/caps, loop rejection, pathfinding,
80% penalties, permanent dividends, shared-cost allocation and safe serialization.
Motorized Caravan tests cover roadless travel across all four harsh environments,
terrain immunity, the 100%/60%/20% infrastructure gold rates, supplied versus
pillaged/disconnected stops, service detours, actual partner payments, full domestic
cargo, retained geography/access/range restrictions, raids, saves and returned unit
identity. AI tests preserve existing Caravans and exercise production of both types.
Database validation checks the Combustion prerequisite, both production costs,
absence of obsolescence/replacement, native movement promotion, localization,
stock art references and companion-mod isolation.

Still run inside a new disposable BNW game before release:

- [ ] Research Caravan Logistics; verify its tech-tree placement and Engineering prerequisite.
- [ ] Ordinary Caravan/Cargo Ship trade missions are absent. Idle units can move.
- [ ] Research Combustion. Verify both Caravans remain trainable at base costs
      75 and 150 (before modifiers), with no upgrade action between them. Check
      the Motorized Caravan's tech-tree entry and Civilopedia text.
- [ ] Without Caravan Logistics, send a Motorized Caravan through neutral desert,
      snow, tundra and jungle. It must survive without terrain penalties. Mountains
      and water must block land routes; agreements and range still apply.
- [ ] Compare gold against the ledger: 20% with neither roads nor a supplied stop,
      60% with one, 100% with both. Change the terrain to mild land: rates must not
      change. Pillage/disconnect/repair the station and verify live payment updates.
      Check that a useful station detour is offered even without a range shortage.
- [ ] Deliver domestic motorized food/production without roads or relief: verify
      full cargo. Compare ordinary Caravan penalties, which must remain unchanged.
- [ ] Complete and recall both route types; check returned identity, including
      routes started before Combustion. Verify native motorized idle movement
      across hills/jungle and AI production of each type on suitable corridors.
- [ ] Open the custom planner at 1024x768 and a widescreen resolution; inspect long
      city names, tooltips, scrolling, city-screen entry/exit and all four tabs.
- [ ] Sign and revoke agreements with AI majors and city-states. Check transit
      through a third party and verify military Open Borders remain separate.
- [ ] Establish land and sea routes; check capacity, native city range bonuses,
      science, and actual treasury changes against the custom ledger.
- [ ] Send a route over 30 road tiles through two supplied relays; cut a necessary
      relay or road, and check recall versus pre-Logistics caravan destruction.
- [ ] Place an enemy at a simulated caravan position: verify raid destruction and
      gold. Repeat with a mature station garrison, then move/pillage the garrison.
      Ordinary Workers and Settlers must remain capturable through normal rules.
- [ ] Save/reload mid-route, with a pending construction order and fractional gold.
      Check there is no extra payment, movement step, worker progress or returned unit.
- [ ] Share infrastructure across several routes and players; verify no duplicated
      upkeep compensation and continuing dividends across successive contracts.
- [ ] Run a long AI-heavy game. Inspect Ministry/worker/trade-unit production,
      road repairs, station placement, garrisons, sea opportunities and turn time.
- [ ] Check known native-trade differences documented in README/TRADE.md and decide
      whether those differences are acceptable before publishing.
