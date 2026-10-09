# Realistic Terrain and Resource Outposts

Two independent Civilization V: Brave New World mods:

| Enabled mods | Behavior |
| --- | --- |
| Realistic Terrain v2 | Environmental exposure, connected desert irrigation, Caravansaries and replacement trade |
| Resource Outposts v1 | Neutral resource claims, fort defense, upkeep, abandonment, notifications and AI expeditions |
| Both | All of the above, plus shelter for your military unit on your intact outpost's tile |

**Resource Outposts never require roads, supply connections, trade agreements or
a Ministry of Coin.** This applies to both extraction and optional shelter.
Caravansaries retain their own road-based rules within Realistic Terrain.

**Status:** single-player alpha. Automated Lua 5.1 tests and validation against
installed BNW databases pass for each mod alone and together. Actual game loading,
UI rendering and gameplay remain unverified. Neither package has been installed
into the game or published to Steam Workshop.

## Install and play

1. Extract either or both of `dist/Realistic-Terrain-v2.zip` and
   `dist/Resource-Outposts-v1.zip`.
2. Copy the resulting **Realistic Terrain (v 2)** and/or **Resource Outposts (v 1)**
   folder into Civ V's `MODS` directory. Each `.modinfo` sits directly in its folder.
3. Launch Civilization V with Brave New World. In **Mods**, enable either mod or
   both, proceed through the Mods menu, and start a **new single-player game**.
   Load subsequent saves through Mods with the same set of enabled mods.
4. Realistic Terrain shows an Environment panel for land military units.
   Resource Outposts adds a worker build control and a **Resource Outposts**
   management button for locating and abandoning owned sites.

Typical mod directories:

- Windows: `Documents\My Games\Sid Meier's Civilization 5\MODS`
- This Mac: `~/Library/Application Support/Sid Meier's Civilization 5/MODS`

Do not enable the old Realistic Terrain v1 alongside Resource Outposts: that alpha
bundled the outpost definitions. Its saves are not migrated; the companion's
manifest blocks this old combination. Realistic Terrain v2 and Resource Outposts
v1 have no mandatory dependency on each other. Merely installing a disabled mod
does not activate integration. Do not add/remove either mod mid-save.

No custom DLL, replacement game UI files or separate art downloads are required.
The selected custom portraits, worker-action icon and wonder painting are bundled.
Multiplayer, hotseat, vanilla/Gods & Kings and overhaul compatibility are untested.

## Realistic Terrain rules

| Environment | Grace period | Notes |
| --- | ---: | --- |
| Desert | 2 turns | Freshwater provides relief |
| Tundra | 3 turns | Forested tundra gains half a turn of exposure per check |
| Snow | 1 turn | Shares the cold counter with tundra |
| Jungle | 4 turns | Jungle features take precedence over underlying terrain |

Exposure is checked once at the start of each unit owner's turn, before orders,
using its current tile as the overnight position. Traversing hostile tiles during
a turn does not accumulate exposure. Newly created units get a complete turn
before their first check. Values are the same at every game speed in this release.

- The first two turns **beyond** a hazard's grace period give **-10% combat strength**.
- Further exposure gives **-20% combat strength** and **5 damage per turn**.
- Environmental damage stops at **25% of maximum HP**. A unit already below that
  floor takes no environmental damage and does not receive free healing.
- The three counters are separate; only the strongest combat penalty applies.
- **Own or same-team territory resets all exposure immediately**, including when
  moving into it. This is relative to each unit's owner; invaders remain exposed.
- Spending a turn on or adjacent to an accessible oasis, beside a lake, on a
  riverside tile, or on flood plains resets heat. Coast water does not count.
  Enemy occupation blocks an oasis/lake source. Peaceful foreign sources require
  open borders; uncontested enemy sources can be used during war.
- Safe land removes **2 exposure per turn** from every counter. An oasis clears
  heat, but other accumulated exposure only recovers gradually. Exhausted units
  can still take damage while recovering until their status improves.
- Changing directly between hostile climates retains previous exposure. Moving
  between snow and tundra changes cold tolerance to the current climate; once
  outside cold terrain, the last cold climate's base tolerance is retained.
- Embarking pauses counters, land penalties, and environmental damage. Landing
  restores any remaining penalties. Embarkation is not a reset.
- Lost HP follows ordinary Civ V healing rules. This mod does not disable healing;
  a resting unit's normal healing can offset the environmental damage.

## Support and exceptions

- Scouts/recon combat class: **+2 grace turns** for every hazard.
- Engineering: **+1 cold grace turn**.
- Biology: **+1 jungle grace turn**.
- Penicillin: another **+2 jungle grace turns**.
- Same-team Medic I or II on the unit's tile or adjacent land: **+2 jungle grace
  turns**, once regardless of the number of medics. Embarked medics do not help.
- Civilian units, ships, aircraft, and barbarians are exempt.
- AI major civilizations and city-states follow the same military-unit rules.
- Open borders do not themselves provide full territorial protection.

There are no new terrain types, supply wagons, ordinary forts-as-supply,
training buildings, seasonal weather, or civilization immunities in version 1.
These are suitable follow-up features after the core rules are play-tested.

## Irrigation

Build **Irrigation Works** in a desert city after **Engineering** (100 production,
1 gold maintenance), then select a worker and choose **Build Irrigated Farm** in
the top-center construction panel. No Ministry of Coin is needed.

- Build on **owned flat desert**, including flood plains and wheat. The tile's
  assigned city must have Irrigation Works; overlapping tiles can be reassigned
  in the city screen. Hills, oases, other visible resources and special
  improvements are protected. An ordinary farm can be replaced.
- The first farm needs a river on its tile or an adjacent **mountain, lake or
  oasis**. Extend outward through your intact irrigated farms. Coast water,
  ordinary farms, roads, city centers and foreign farms do not carry water.
- Each connected farm supplies **+3 food from the improvement**, versus **+1**
  when disconnected. Terrain/resource yields and the ordinary farm's Civil
  Service/Fertilizer bonuses still apply. Irrigation does not mark land as native
  freshwater or grant heat relief to armies.
- Every productive branch must retain a **continuous connection to a real
  source**. Pillaging, replacing or capturing a connecting farm cuts supply.
  Loops cannot water themselves. Another intact path keeps a branch supplied.
- Disconnected farms remain in place at ordinary farm yields. Repairing the
  link with the native **Repair** action restores irrigation automatically.
  Pillaged farms produce no improvement yield and cannot carry water.
- One click starts persistent work at normal farm construction time, including
  game/worker speed modifiers. Losing water or the local building pauses work;
  movement, cancellation or a different order ends it. Orders and partial work
  survive saving/reloading. Selling the building does not disable completed farms.
- AI players commission useful Irrigation Works through ordinary production and
  use one available worker per turn to build or repair nearby networks, respecting
  existing construction and Resource Outpost assignments.

The farm uses existing farm art, and Irrigation Works uses the aqueduct icon.
Wet/dry names and native tile food yields update at turn boundaries and after
construction/repair events. The worker panel reports current water connectivity.
Native event timing and AI behavior still need an in-game play-test; start a new
game with this build. See [IRRIGATION.md](../mods/irrigated-farm/docs/IRRIGATION.md) for details and checks.

## Caravansaries

**Caravansary** is the renamed Relief Station: a worker-built tile improvement
requiring **Engineering** and a **Ministry of Coin** in one of your cities.

The Ministry of Coin replaces the original city Caravansary as a **national wonder**:

- One per player, available at **Horseback Riding**.
- Retains the original **+50% land trade range** and **+2 gold for international
  land routes originating in its city**. These bonuses apply to that city only.
- Unlocks Caravansary construction throughout your empire once Engineering is known.
- Base cost **125 production**, with the standard national-wonder city-count cost
  modifier of 30. No maintenance; cannot be purchased or captured.
- No prerequisite building in every city. The East India Company is unchanged.
- Losing the Ministry blocks further Caravansary construction; completed stations still operate.

Select an eligible worker and click **Build Caravansary** in the top-center
panel once. The worker contributes work immediately and automatically on later
turns. **Cancel construction**, moving away, or assigning another construction
order cancels the assignment. Losing the Ministry pauses it; rebuilding resumes
it. The order and partial progress survive saving/reloading. Construction uses
native worker speed and game-speed build times. Existing worker automation must
be cancelled before starting this order.

The field Caravansary uses fort graphics and fort construction times, but has no
defensive bonus.
It can be built on land in your territory or on unclaimed land; it preserves
forest and jungle and follows fort feature-work prerequisites. Build a road on
the station tile as a separate worker action.

Spend a turn **on the station or one adjacent land tile** to reset all three
exposure counters and remove both environmental combat penalties. The check
happens at the start of the owner's next turn. Passing through its radius during
a turn gives no reset. Existing HP damage still heals through normal game rules.

Relief requires an unbroken chain of **roads or railroads to any city you own**:

- The station tile and every non-city tile along the chain need an intact route.
- The city center is the endpoint and needs no separate road improvement.
- Supply may cross your territory, unclaimed land, and trade-agreement partners'
  territory. Ordinary Open Borders alone do not grant commercial supply access.
- A pillaged station, pillaged route, missing road, or enemy occupying any tile
  of the route blocks that path. An intact alternative route can still supply it.
- Water/harbor connections do not qualify. Neither do another player's cities.
- A station in unclaimed land belongs to the worker's player, recorded in the
  saved game. In claimed territory, the current tile owner controls it. Other
  armies cannot use your station. Authorized partner caravans can use it.
- Cutting supply resumes exposure from its current value; penalties already
  removed by an earlier resupply do not suddenly return. Repairing the connection
  restores relief at the next check.

Home-border protection remains unconditional. Stations are primarily useful
outside the homeland, or at its edge to support units just beyond the border.
Their connectivity is recalculated at every check, avoiding stale road or city
ownership information. The Environment tooltip reports a nearby station's status.
AI units use the same military relief rules. AI logistics now plans a cooperative
corridor, assigns workers to roads/repairs/Caravansaries, commissions trade units
and a Ministry through normal city production, and assigns spare field troops
to stations. Native AI coordination and performance still need a game play-test.

## Resource Outposts

A worker builds an outpost directly on an unimproved strategic or luxury deposit
in neutral land. It claims that deposit for its builder without expanding borders.

- Requires Engineering, resource visibility and the ordinary extraction technology
  (Mining, Calendar, Trapping, etc.). Uses fort work time and normal worker/game-speed
  modifiers. Construction continues automatically; cancelling, moving or changing
  orders ends the assignment. Partial progress survives.
- Supports the six strategic resources and ordinary land luxuries: 24 types in
  the installed BNW database. Bonus resources, artifacts and water deposits are excluded.
- Grants the deposit's base quantity, such as six iron or one silk, for use and
  trade. Resources do not accumulate. It grants no city yields, local-resource
  building prerequisites or city/terrain-specific extraction bonuses.
- Uses fort graphics and grants +50% defense. A land military unit can occupy and
  fortify on the tile. A garrison is optional for resource access.
- Base upkeep is **2 gold per turn per standing outpost**, including pillaged,
  blockaded and annexed sites. It appears under building maintenance and receives
  normal building-maintenance modifiers. Unit upkeep remains separate.
- **Resource Outposts** opens an overview of all sites, showing resource quantity,
  extraction, defender health and base upkeep. Locate or manage any site without
  selecting a garrison. Abandonment previews resource losses, upkeep savings and
  last-luxury/strategic-shortage warnings before its two-click confirmation.
- Once an intact site is inside your borders, **Convert improvement** optionally
  replaces it with the ordinary resource improvement and stops outpost upkeep.
  Resource access remains; fort defense is removed. Conversion completes the normal
  native build, including feature clearing, and requires its normal technologies.
- Pillage suspends extraction; repair restores it. A hostile land military unit
  entering a neutral outpost captures it, transferring resource access and upkeep.
  The new owner needs the appropriate extraction technology. Barbarians can
  blockade extraction but cannot own claims.
- City borders take precedence. The territorial owner receives the installation,
  and native resource accounting replaces the neutral-site contribution without
  duplication. The site carries outpost upkeep until abandoned, removed or converted.
- Notifications explain resource losses/recovery, capture, annexation and abandonment,
  with the resource and change in available quantity. Unchanged status and reloads
  do not repeat notifications.

With **both mods enabled**, an intact outpost shelters its owner's military unit
on that tile only. Shelter clears exposure and environmental penalties at the
next owner-turn check, without restoring HP. There is no adjacent shelter radius.
Pillage removes shelter. No road, city connection, technology beyond construction,
or Caravansary is needed for this shelter. This is the only added gameplay feature
from combining the mods; outposts do not become trade relays or patrol stations.

Neutral land retains normal access rules: peaceful foreigners may enter an
undefended tile, and native rules allow neutral improvements to be pillaged
without declaring war. Peaceful entry or repair does not transfer the claim.
A military defender enforces ordinary stacking and combat restrictions.

The AI prioritizes repairs and scarce resources, escorts workers through visible
danger, and replaces badly wounded defenders. Recovery chooses the nearest reachable
safe friendly tile, preferring a city at equal distance, with health thresholds
scaled to maximum HP. Five turns without assignment progress trigger reassignment
and a five-turn destination cooldown. Progress and cooldowns survive reloading. Its site budget scales with income, treasury and army size instead of a
fixed three-site limit. It keeps a homeland worker and uses up to two expedition
workers within twelve hexes of a city. Production uses ordinary city queues,
costs and civilization replacements. City garrisons and Caravansary patrols stay
in place. Human players have no AI planning caps.

See [OUTPOSTS.md](../mods/resource-outposts/docs/OUTPOSTS.md) for accounting, AI scope and native acceptance tests.

## Replacement trade system

This release replaces native Caravan/Cargo Ship trade to retain **native Mac
support without a DLL**. Use the **Trade and logistics** button near the upper
right. Active caravans are simulated route entities with positions in this
planner; they are not animated, capturable native units on the map. Idle trade
units remain ordinary map units. Native trade missions are disabled so they
cannot bypass the rules.

- **Agreements:** reciprocal commercial agreements are mandatory for international
  land and sea routes and for crossing another player's territory. They do not
  grant military Open Borders. War terminates agreements; peace does not renew
  them automatically. Revocation or city capture recalls affected routes.
- **Caravan Logistics:** new Medieval technology, after Engineering, base research
  cost 275. Before it, ordinary Caravans need roads in neutral territory. The planner rejects invalid
  routes; if an operating caravan enters a newly roadless neutral tile, it dies.
  After the technology it survives, but infrastructure penalties still apply.
- **Motorized Caravan:** optional alternative at Combustion, costing 150 production.
  Ordinary Caravans remain available for 75 production; neither automatic upgrades
  nor obsolescence are applied. Motorized traders cross all passable land without
  roads or Caravan Logistics and ignore environmental exposure and relief penalties.
  Mountains, ice and water still block land routes. Missing continuous roads and
  a supplied Caravansary stop each deduct 40% gold, for 20% income with neither,
  60% with one and 100% with both. These deductions do not reduce domestic cargo.
  Dedicated vehicle art is pending; stock Caravan art is used.
- **Range:** use native origin-city base range and modifiers, including the Ministry.
  Road edges cost half a normal land step. Reachable, supplied Caravansaries add
  +5 range each, capped at +10 per route. The planner can route through relays.
  Loss of required range recalls the route.
- **Penalties:** missing continuous roads costs 40%; missing relief for harsh
  terrain costs another 40%, additive to a maximum **80% payment reduction**.
  Motorized Caravans instead use the terrain-independent gold deductions above.
  Mild terrain needs no relief. Home territory, cities, freshwater heat relief,
  and adjacent supplied Caravansaries provide the applicable protection.
- **Patrols:** a land combat unit stationed at a supplied Caravansary for a full
  turn protects authorized caravans along connected road branches up to the next
  city or Caravansary. Moving it resets activation. Pillaging or losing supply
  disables protection. Ordinary civilians receive no immunity.
- **Trade income:** operating routes pay commerce, a capped distance bonus,
  shared upkeep compensation, and **permanent infrastructure dividends**. Shared
  assets are counted once, and payments go to their supporting players, including
  transit partners. See `mods/realistic-terrain/docs/TRADE.md` for defaults and accounting limits.
- **Lifecycle:** a route invests its Caravan, Motorized Caravan or Cargo Ship, uses a normal trade
  slot, and runs for at least the game-speed deal duration before completing a
  circuit. Completion or recall returns the unit; destruction does not. Raids
  award the enemy 100 gold. Land routes advance two tiles/turn; sea routes three.
- **Domestic cargo:** food and production routes remain available, requiring a
  Granary or Workshop at the origin. These use custom yields and infrastructure
  efficiency (always 100% for motorized cargo), but no foreign agreement. International science uses native yield
  queries and is credited through research progress.
- **Planner:** shows agreements, eligibility, penalties, marginal net income,
  patrol coverage, current positions, recall controls, and an income ledger.

**Start a new game.** Earlier alpha saves and native routes are not migrated.
This is a functional implementation with automated API-boundary tests, not a
native-tested release. The replacement does **not** participate in every stock
trade subsystem: native trade overview/GPT forecasts, religious pressure,
tourism connections, World Congress embargo enforcement, and trade-route quests
are not reproduced. Its income is credited each owner-turn and displayed in the
custom ledger. Native game testing and Workshop publication remain deferred.

## Selected artwork and map-model sources

The Realistic Terrain package now includes the selected round-three artwork:

| Asset | Selection | Runtime use |
| --- | --- | --- |
| Caravan Logistics | B: Mountain passage | Technology tree and Civilopedia |
| Ministry of Coin portrait | B: Counting house | City production, national wonder entry and Civilopedia |
| Caravansary portrait | A: Roadside gateway | Improvement portrait and Civilopedia |
| Build Caravansary | B: Well and shelter | Custom worker button and build-action definition |
| Ministry painting | A: Treasury arrival | Native wonder popup triggered on Ministry completion |

`mods/realistic-terrain/src/Art/` contains eleven legacy RGBA DDS textures. Portrait atlas sizes cover
32, 45, 64, 80, 128, 214 and 256; worker glyphs cover 32, 45 and 64. The Ministry
uses a 976x576 painting. `SQL/RT_Art.sql` connects the database definitions, while
`RT_Art.lua` triggers the standard completion popup for this national wonder
(national wonders do not normally show it). It is restricted to the local human
player and suppresses duplicate completion callbacks, including across reloads.
Only original generated assets are included; the real Civ V comparison images
remain outside both mod packages. DDS decoding, VFS paths, SQL and Lua tests pass;
actual game rendering remains unverified.

All four map structures have original, editable first-pass meshes in
`output/models/first-pass/`: Caravansary, Ministry of Coin, Resource Outpost and
Irrigation Works. Caravansary and Outpost include construction/pillaged variants.
The separate `dist/Map-Model-Sources-v1.zip` contains OBJ/MTL, embedded-texture GLB,
rigid-root BR2 transfer files, basic palette materials and previews. It is a source
bundle, not a playable mod. See its `CONVERSION.txt` for the remaining pipeline.
GR2 conversion/material binding requires the Nexus Buddy toolchain, which was not
available on this Mac. Final surface detail, scale, city placement and native
rendering are pending. The playable mods still use their existing 3D fallbacks.

The approved Resource Outpost era designs now have a separate source set in
`output/models/outpost-eras-v1/`, with previews in its `index.html`. The choices
are Ancient A, Classical B, Medieval B, Renaissance A, Industrial B, Modern A,
Atomic A and Information A, recorded in
`shared/art/outpost-era-concepts-v1/approved.json`. These eight designs supersede
the generic outpost concept above. Each includes constructed, construction and
pillaged geometry: 24 OBJ/MTL, GLB and BR2 meshes in
`dist/Outpost-Era-Model-Sources-v1.zip`, with original weathered materials,
per-mesh diffuse textures, baked cavity/ground shading and mipmapped DXT1 exports.
The installed medieval/modern fort and ancient citadel textures were inspected
as references; stock art is excluded. Architectural revision 2 restores the
approved massing, gates, wall walks, projecting bastions, roof profiles and
equipment silhouettes. The gallery includes unchanged approved artwork beside
each rebuilt source mesh. The user approved this revised geometry on 9 October 2026; exact style
parity still needs native review.
All exports and the empty central garrison area pass source checks. Native GR2
conversion, material/scale refinement, and automatic claimant-era visual updates
remain pending; the playable outpost package has not acquired those visuals yet.

Rebuild this source set with `tools/build_outpost_era_models.py` and check it with
`tools/validate_outpost_era_models.py` (both require NumPy and Pillow).

The current **Realistic Terrain model revision** is in
`output/models/revised-v2/index.html` and `dist/RT-Revised-Model-Sources-v2.zip`.
It rebuilds the Caravansary (early/industrial, each with construction and pillaged
states), Ministry of Coin, Irrigation Works building, and Motorized Caravan:
**nine textured source meshes**, including front/reverse renders and a coverage
manifest. The current alignment pass follows the approved Caravansary A gateway,
Build Caravansary B four-post flat well canopy, and Ministry B stepped counting
house with painting A's pale entrance, red banners and bronze olive-branch seal.
Each model now has its own padded UV atlas, original diffuse/normal/specular maps,
baked cavity and ground shading, and mipmapped BC1 diffuse/specular DDS. The
preview uses the same geometry, UVs and diffuse pixels as the exports. The lorry
has separate named wheel groups for rigging. There are no terrain-shaped plinths.
The user **approved all nine source model designs on 9 October 2026**, including
the industrial depot, waterworks and lorry. The exact mesh/texture hashes are
recorded in `shared/art/rt-models/approved.json` and copied into the source bundle.
Rebuilds compare against that record; changed assets require review. Any additional icons or
artwork must be presented as options beside real Civ V references, with the
user's selection recorded before integration. Existing approved 2D art is unchanged.
Comparison documents are in `output/model-review/approved-art-alignment/`;
their stock references stay outside both source and playable mod packages.
**Farms are deferred, and Resource Outposts are handled separately.** This pass
changes neither those assets nor playable model references. GR2 conversion,
engine material/scale checks and native vehicle rig/animations remain pending.
Run `tools/build_models_v2.py` and `tools/validate_models_v2.py` with NumPy/Pillow
to reproduce and validate this revision. `tools/review_models_v2.py` lays out the
comparison documents and checks the original approved-art SHA-256 hashes; it
requires the separately cached official screenshot named in the script.
The v1 bundles remain historical sources.

To reproduce the art exports, use Pillow for `tools/export_art.py`, and NumPy plus
Pillow for `tools/build_models.py`. `tools/validate_models.py` checks geometry,
normals, UVs, transfer-file structure and source-ZIP parity without those packages.
Normal packaging uses the checked-in DDS files and needs only the standard library.

## Build and verify

Source is in `mods/realistic-terrain/src/` and `mods/irrigated-farm/src/`
(combined into Realistic Terrain v2), and `mods/resource-outposts/src/`
(Resource Outposts). Complete ModBuddy projects are generated in `build/`.
The build generates both install folders and ZIPs in `dist/`.
The build uses Python's standard library:

```sh
python3 tools/build.py
python3 tools/validate.py
```

To execute the production Lua in a Lua 5.1 runtime:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python tools/test.py
```

Optional validation against copies of your actual game and localization databases:

```sh
python3 tools/validate.py --cache "/path/to/Sid Meier's Civilization 5/cache"
```

The validator opens the installed files read-only and validates in memory. It does
not modify the game's databases. Run `tools/build.py` after every source change
to refresh the `.modinfo` hashes and distributable ZIP.

Tune thresholds, damage, support, and panel position in `mods/realistic-terrain/src/Lua/RT_Config.lua`
before starting a new game. Combat modifiers are in `mods/realistic-terrain/src/SQL/RT_Promotions.sql`;
update the matching help text if changing them.

See `docs/TESTING.md` for the manual play-test checklist and
`docs/WORKSHOP.md` for release preparation and the listing draft.
