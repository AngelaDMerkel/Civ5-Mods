# Resource Outposts

An independent stock Brave New World Lua/database mod. Source: `mods/resource-outposts/src/`.
Release: `dist/Resource-Outposts-v1.zip`. Requires a new single-player game.
Automated tests and installed-database checks pass. Focused native construction,
resource/upkeep lifecycle and save/reload checks also pass; see
[native gameplay evidence](NATIVE-GAMEPLAY-TESTS.md). Broader UI interaction and
long-game AI balance remain separate acceptance work.

## Independence and optional shelter

Resource Outposts and Realistic Terrain v2 each work alone. Their mod identities,
Lua filenames/globals, save keys, database actions and UI contexts are separate.
The Resource Outposts manifest references Realistic Terrain as an optional load
order preference, not a dependency. It blocks RT v1, which bundled outpost data.
Both packages require BNW; saves from the bundled alpha are not migrated.

`RO_Integration` detects Realistic Terrain in `Modding.GetActivatedMods()`. The
mods communicate through synchronous `LuaEvents` request tables; neither includes
the other's files or expects its Lua globals to be accessible. Empty queries are
harmless without a companion listener. Event requests also coordinate worker
orders and AI reservations so the two planners do not reassign outpost personnel.

The only additional gameplay effect when both are enabled is **shelter**: a
military unit on its own intact outpost clears environmental exposure at the
next owner-turn check. It does not heal HP or shelter adjacent tiles. Pillage
removes shelter. **Roads and supply connections are never needed for building,
extracting resources or shelter.** Outposts add no trade relays, patrol corridors
or Caravansary supply services. Installed but disabled mods have no effect.

## Construction, defense and abandonment

Select a worker on an unimproved neutral land strategic/luxury deposit and choose
Build Resource Outpost. Engineering, visibility and the resource's ordinary
extraction technology are required. No Ministry, road, agreement or garrison is
required. Uses stock fort work time, +50% defense and feature prerequisites;
approved custom models follow the claimant's era. Normal worker speed and
game-speed modifiers apply. Forest/jungle/marsh are retained.

An outpost replaces the mine/plantation/etc. on that deposit. A military unit
occupies and fortifies on the ordinary tile. It is not a city and grants no city
hit points, bombardment or city-garrison policy benefits.

`RO_Orders` persists construction assignments and per-worker turn stamps under
`ResourceOutposts.v1.Construction.*`. Native progress remains on the plot. Changing
custom orders cancels the other mod's order; cross-context work-stamp checks prevent
two contributions in the same turn. No native `Unit_Builds` action bypasses the
gates. The AI uses the same construction path and worker turns as humans.

The Resource Outposts control opens a scrollable overview of every owned site:
coordinates, resource and deposit quantity, extraction status, defender and health,
and base upkeep. It also shows total base upkeep. Each row has Locate and Manage
actions. Management works without a selected unit or stationed garrison.

Before abandonment, the detail card shows resource loss, available quantity before
and after, and base upkeep removed. It highlights a last available luxury copy or
a strategic shortage. Read-only predictions include current imports, exports,
consumption, active strategic-resource policies, and stock local trait/city bonuses
on annexed tiles. Unusual multiplier rounding is explicitly marked as estimated.
Custom DLL or scripted resource modifiers outside the stock data are not supported.
Upkeep is stated as base gold, since treasury maintenance modifiers still apply.

Abandonment takes two clicks during the owner's active turn. If the quoted effects
change between clicks, confirmation must be renewed. It removes the improvement,
resource contribution and upkeep. Cultural ownership of an annexed tile remains.

**Optional conversion after annexation:** an intact outpost inside your borders
can be converted instantly into the ordinary Mine, Quarry, Pasture, Camp,
Plantation or Well for its resource. The appropriate build and feature-clearing
technologies and native build legality must be satisfied. Hostile occupation or
pillage blocks conversion. A separate confirmation explains the loss of +50%
fort defense and the end of outpost upkeep. Declining conversion retains the fort.

Conversion completes the normal native build, including any feature clearing and
normal construction effects. It retains resource access and territorial ownership,
removes the site from outpost management, and withdraws its upkeep once. It does
not grant a free repair or issue a false resource-loss notice. The UI rechecks
ownership, turn, legality and the selected conversion before performing it.

## Resource and upkeep accounting

`RO_Outposts` saves each site's owner, last reported status, aggregate resource
contributions, maintenance contribution and AI assignments under
`ResourceOutposts.v1.State`. Reconciliation applies only differences to native
resource totals through `ChangeNumResourceTotal`; it never overwrites totals or
confuses consumption/exports with production.

- Intact unblocked neutral sites supply the deposit's base quantity. Resources
  do not accumulate. Ordinary use, luxury happiness and trade apply, but city
  yields, local building prerequisites and city/terrain extraction bonuses do not.
- Pillage, blockade, removal, loss of extraction eligibility or elimination
  withdraws only this mod's contribution; recovery restores it.
- A non-embarked land combat unit entering at war takes ownership. Capture does
  not repair ruins or waive technology. Barbarians blockade but cannot own claims.
  Peaceful military units and civilians do not capture the improvement.
- Territorial annexation supersedes the claimant. Native `ResourceTrade` takes
  over extraction and Lua withdraws the neutral credit. If the tile later becomes
  neutral, the last territorial owner remains the claimant.
- Every standing outpost adds **2 base gold/turn** via
  `ChangeBaseBuildingGoldMaintenance`. Normal treasury timing, maintenance modifiers
  and handicap discounts apply; the expense appears under building maintenance.
  Pillaged, blockaded and annexed sites still cost upkeep. Capture moves the charge;
  removal or owner elimination releases it. SQL improvement upkeep is zero to
  avoid a duplicate native charge after annexation.
- Saves persist both native totals and the contribution ledger. Repeated events
  and reloads apply zero differences to resources and upkeep. Unrelated building
  maintenance is retained.

Human notifications include the affected resource and signed access delta for
pillage/recovery, capture, absorption by city borders, removal and abandonment.
Absorption by your own borders correctly reports zero net change. A saved status
snapshot suppresses repeated notices when nothing changed, including after reload.

Reconciliation runs on turns, movement, builds, city/border/technology changes,
war changes, load completion and game-data dirty hints. Reentrant engine callbacks
are guarded. Unseen changes are caught by the next turn check.

Neutral land has native access and pillaging rules: a peaceful foreigner may enter
and pillage an undefended neutral improvement. Station a defender when protection
matters. Peaceful repair alone never transfers ownership.

## AI behavior

`RO_AI` keeps persistent worker, guard, escort and recovering assignments with
unit ID, birth turn, original owner and type. Stale/reused IDs do not inherit jobs.
Realistic Terrain's trade planner first invokes the turn-guarded outpost planner
and then respects its reservations.

Repairs take priority, then scarce strategic resources, scarce luxuries, surplus
resources and proximity. Scarce-resource sites receive first choice of available
defenders. Existing healthy guard assignments are retained. One worker stays for
domestic use; at most two expedition workers operate within twelve hexes of a city.
The maximum planned site count is the lesser of:

- `1 + floor(land combat units / 2)`;
- `floor(max(0, income before outpost upkeep + treasury / 40) / 8)`.

The economy term uses displayed income plus this mod's base maintenance ledger,
so maintenance discounts may make the estimate slightly generous. It can be zero,
or grow beyond three sites. Repairs are allowed over budget; inherited/captured
sites are not automatically destroyed. These planning limits do not restrict humans.

Workers take safe revealed land routes when possible. If visible enemy adjacency
makes every route unsafe, they wait for a healthy escort. The escort rendezvous
first, moves ahead one tile and holds while work proceeds. Automatic construction
pauses without a healthy colocated escort when the site is threatened. Even an
escorted path rejects a tile occupied by a visible hostile unit. Water, impassable,
unrevealed and foreign-owned transit tiles are excluded; searches are bounded.
Native missions enforce movement cost and stacking.

Assignments track the best remaining path distance, build progress and escort
rendezvous progress. Five turns without progress release the stalled worker or
defender, cancel its custom construction, and release a worker's escort. The
failed destination is avoided for five more turns; another destination can be
chosen immediately. Both progress and cooldowns persist across reloads. Productive
long builds and guards already at their posts do not time out. Defaults are in
`RO_AI.STALL_TURNS` and `RO_AI.RETRY_TURNS`.

At 50% health or less, assigned units withdraw to the nearest reachable safe tile
in their own territory. A city wins a tie at the same path distance. The search
avoids visible threats and occupied stacking slots, including intermediate steps,
and is recalculated as the map changes. If there is no reachable refuge, the unit
rests where it is and tries again next turn. Native heal missions preserve movement
on rest turns, allowing normal healing; the mod does not grant HP directly.
Recovering units remain reserved until above 75% health. Thresholds use each unit's
maximum HP. A healthy troop can replace a wounded guard immediately. City garrisons
and Caravansary patrols are excluded from reassignment.
Normal city queues commission workers or civilization-appropriate melee defenders
with a ten-turn cooldown, pending-production checks and a low-treasury deficit gate.
Newly commissioned defenders can leave their production city, including as escorts.

This planner does not replace tactical combat AI or conduct overseas expeditions.
Native AI may issue competing orders; congestion, healing and long-game balance
still require playtesting.

## Selected UI icons

The user selected **Guarded storehouse B** for both the main emblem and worker
construction glyph on 9 October 2026, explicitly reusing the emblem for management
and strategic view. `shared/art/resource-outpost-icons-v1/` preserves the exact
original PNGs, prompts, selection, hashes and DDS export report. See
[ICON-REVIEW.md](ICON-REVIEW.md) for coverage and provenance.

The package includes eleven original-art DDS textures: seven portrait sizes,
three worker-action sizes, and a strategic-view icon. `SQL/RO_Art.sql` binds them
to the existing improvement/build records and a new outpost-only art definition.
That definition clones the native Fort model rows for every era/state as a
fallback, while using the selected outpost strategic icon. Ordinary Fort data,
models and icons remain unchanged. Management and construction controls use the
same chosen art. Notifications still use the native generic symbol.

`ReloadStrategicViewSystem` is enabled for Resource Outposts; Terrain's setting
is unchanged. All existing gameplay/save identifiers and resource accounting are
preserved. Native UI and strategic rendering still require a game check.

## Approved era concepts and source models

The user approved these concepts on 9 October 2026:

| Era | Choice | Design |
| --- | --- | --- |
| Ancient | A | Timber Watchpost |
| Classical | B | Frontier Fortlet |
| Medieval | B | Fortified Courtyard |
| Renaissance | A | Bastioned Watchtower |
| Industrial | B | Brick Blockhouse |
| Modern | A | Radio Watchpost |
| Atomic | A | Radar Sentry Post |
| Information | A | Sensor Mast Outpost |

The canonical choices are in `shared/art/outpost-era-concepts-v1/approved.json`.
Editable meshes and actual source-geometry previews are in
`output/models/outpost-eras-v1/`; its `index.html` compares each approved concept
with architectural revision 2 of its mesh, plus construction and pillaged states. `dist/Outpost-Era-Model-Sources-v1.zip` contains 24 OBJ/MTL, GLB and BR2
sources, original weathered materials with baked per-mesh diffuse textures,
mipmapped DXT1 exports and conversion notes. These
supersede the older generic outpost source mesh, without changing the other
Realistic Terrain models. The revised geometry restores projecting defenses,
substantial walls and gatehouses, walks/stairs, distinctive roof profiles and
open supply shelters. Approved concept images are included unchanged. The user
approved architectural revision 2 on 9 October 2026; this is recorded in the
`meshApproval` entry of the canonical approval file.

Each mesh has an open central garrison square, a common origin and no terrain
plinth or connecting road. Construction and pillage use separate geometry.
Native GR2 conversion and scoped visual review are complete for all 24 states;
the runtime package includes their GR2/FXSXML/DDS at scale 6. The mod selects eight internal variants using the
claimant's current era on neutral plots and the territorial owner's era after
annexation. Capture can move a site to an earlier or later stage. The approved
models replace Fort placeholders. See [NATIVE-ART-REVIEW.md](NATIVE-ART-REVIEW.md)
for native evidence and its limits. Full campaign acceptance remains pending.

`RO_Eras` synchronizes completed and pillaged sites inside the existing guarded
reconciliation. AI, management and optional shelter recognize every variant.
Resource accounting, upkeep, pillage status, upgrade progress and stationed units
are preserved in regression tests. Construction retains its existing build ID and
work progress, applying the current stage on completion. The public build uses
one shared Ancient scaffold across eras. There is one public build
action and one Civilopedia entry. See [ERA-VISUALS.md](ERA-VISUALS.md) for the native
resource-link safeguard, old-save migration limit, event timing and mesh handoff.

## Verification

`mods/resource-outposts/tests/test_outposts.lua` runs production construction, accounting, AI and UI code
with mock native resource and treasury ledgers. Tests cover reload/idempotence,
unrelated income/resources, capture/annexation, pillage/recovery notices, upkeep,
abandonment, escorts, wounded rotation, variable budgets and scarce-resource guards.
Additional coverage checks persistent timeout/cooldown behavior, long construction,
nearest reachable healing, stacking and percentage health, native heal orders,
resource previews with policy/trait/import/export effects, stale confirmations,
conversion gates/accounting/feature clearing/reloads, and overview row actions.
Separate Lua environments exercise actual event-based integration without shared
mod globals. The game adapter suite verifies roadless shelter and overnight
exposure/penalty clearing. RT alone and RO alone are also exercised.

Era regressions cover all eight stages, inactive/unseen claimants, technology and
turn callbacks, lower-era capture, annexation, pillaged sites, native resource/city
links, reentrant callbacks, unchanged garrisons, old-save migration, reload,
construction progress and extra future eras. The native setter mock follows BNW's
repair/add/remove order; it does not establish actual renderer acceptance.

`tools/validate.py --cache ...` clones installed BNW databases read-only into
memory. It validates each package alone and both together in either SQL load
order, resource definitions, fort work/defense, localization, isolated dependencies,
VFS names, source/ZIP equality and manifest hashes. RO alone leaves native trade,
Ministry/Caravansary data and environmental rules untouched.

Native acceptance checklist:

- [x] Convert, bind and inspect all 24 approved model states; check representative
      hill, desert/forest and remembered-fog scenes.
- [x] Run production `RO_Eras` against native neutral plots through all eight eras,
      preserving pillage, work progress, unit state and neutral ownership.
- [ ] Complete the remaining campaign-era checks in [ERA-VISUALS.md](ERA-VISUALS.md).
- [ ] Inspect the B portrait in Civilopedia, construction glyph, disabled/cancel
      states and management icons at 1024x768 and widescreen. Inspect outpost and
      ordinary Fort strategic markers, including pillage, capture and save/load.
      Check the public construction model through ordinary worker completion.
- [ ] Start separate new games with RT only, RO only and both; inspect Lua/database logs.
- [ ] Build roadless outposts on iron, silk, horses, oil and feature-covered deposits.
      Check technology, work time, cancel/resume, saves and resource use/trade/happiness.
- [ ] Confirm 2 base upkeep in building maintenance, including policy/handicap
      modifiers. Reload, capture, annex, pillage, repair and abandon without duplicates.
- [ ] With both mods, shelter a defender on a disconnected harsh-terrain outpost;
      verify next-turn relief, no HP healing, no adjacent relief and pillage removal.
- [ ] Inspect +50% fort defense and ordinary military occupancy/stacking.
- [ ] Capture before extraction technology; confirm resource loss/gain notifications.
      Test barbarian blockade, peaceful entry, repair and neutral-land pillaging.
- [ ] Absorb claims through culture, purchase, city founding and city capture; check
      both owners' resource totals and maintenance, including used/exported resources.
- [ ] Manage and abandon with no selected unit. Inspect both mods' controls at
      1024x768 and widescreen, with long names and city-screen transitions.
- [ ] Preview abandonment with used/exported iron, the last luxury, imports,
      strategic quantity policies and city/trait bonuses. Change the resource
      situation after the first click and verify renewed confirmation is required.
- [ ] Convert annexed iron and silk outposts, including feature-covered deposits.
      Inspect normal feature clearing, city resource links, yields, removed defense,
      retained resource access and removal of upkeep. Pillaged sites must be repaired.
- [ ] Block worker/escort/guard movement for five turns; verify released reservations,
      persistent cooldowns, alternate assignments, and eventual retry. Slow builds
      that continue making progress must retain their workers.
- [ ] Test nearby healing cities and friendly tiles, blocked transit and variable
      maximum HP. Verify actual native healing and return to duty above 75% health.
- [ ] Inspect overview scrolling, totals, defender HP, row actions and conversion
      confirmation with many sites and long unit/resource names at 1024x768.
- [ ] Run an AI-heavy game: escort rendezvous, wounded replacement/healing,
      production, scarce-resource defense, economy limits, repairs and turn time.

Engine references: Firaxis BNW source mirrors for
[unit Lua bindings](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaUnit.cpp),
[plot ownership](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvPlot.cpp),
[player Lua bindings](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp)
[unit healing and reset](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvPlayer.cpp),
[heal missions](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvUnitMission.cpp),
and [treasury accounting](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvTreasury.cpp).
