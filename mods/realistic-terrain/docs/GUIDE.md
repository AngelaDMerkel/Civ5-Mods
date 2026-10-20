# Realistic Terrain: player guide

[Mod collection](../../../README.md) · [Installation](../../../docs/GAMEPLAY.md#install-a-packaged-test-build)

## Goals

Make terrain, shelter and infrastructure matter when moving beyond your borders.
Realistic Terrain asks you to plan where an army will rest and how your trade
network will support a long journey. Developing a road corridor should help both
your military expeditions and your economy.

## What the mod adds

- **Environmental exposure:** repeated nights in desert, tundra, snow or jungle
  weaken land military units until they reach suitable relief.
- **Ministry of Coin and Caravansaries:** a national wonder unlocks roadside
  stations that shelter troops, extend trade range and support patrols.
- **Trade and logistics:** commercial agreements and a route planner for Caravans,
  Motorized Caravans and Cargo Ships, with income affected by infrastructure.
- **Irrigated Farm:** the included [farm feature](../../irrigated-farm/docs/GUIDE.md)
  connects desert farmland to water sources.

**Status:** experimental v2 build for a new single-player Brave New World game;
in-game testing is still pending.

## How it works

[Exposure](#environmental-exposure) · [Ministry of Coin](#ministry-of-coin) ·
[Caravansaries](#caravansary-roadside-shelter-and-trade-support) ·
[Trade and logistics](#trade-and-logistics)

### Start with these decisions

1. Watch the **Environment** panel when selecting a land military unit. End turns
   in friendly territory or near appropriate relief when possible.
2. Research **Horseback Riding** and build the **Ministry of Coin** if you want
   a network of Caravansaries.
3. At **Engineering**, send workers to build Caravansaries and connect them by
   intact roads to one of your cities.
4. Use **Trade and logistics** to arrange agreements, inspect routes and see what
   your infrastructure earns. Ordinary trade orders are replaced by this planner.

### Environmental exposure

Exposure is checked at the start of the unit owner's turn, using the tile where
the unit ended its previous turn. Crossing a desert during one turn does not
accumulate exposure if the unit finishes somewhere safe. Newly created units get
a full turn before their first check.

| Terrain | Grace period without support | Special rule |
| --- | ---: | --- |
| Desert | 2 turns | Suitable freshwater resets heat exposure |
| Tundra | 3 turns | Forested tundra adds only half a turn of exposure per check |
| Snow | 1 turn | Shares its cold exposure with tundra |
| Jungle | 4 turns | Jungle takes precedence over the terrain beneath it |

After the grace period, a unit suffers **−10% combat strength for two turns**.
Continued exposure increases this to **−20% combat strength and 5 damage per turn**.
Environmental damage stops at **25% of maximum health**; it does not heal a unit
that is already below that level. Only the strongest exposure combat penalty applies.

For example, an unsupported ordinary soldier in desert remains ready at its first
two checks, becomes strained at checks three and four, and becomes exhausted at
check five. Scouts and other sources of extra tolerance delay those stages.
Grace periods are the same at every game speed in this build.

#### Relief and recovery

**Your territory and your team's territory** clear all exposure immediately,
including when the unit moves into them. A foreign army does not receive that
protection merely because it is inside your borders. Open Borders alone does not
make foreign land safe from exposure.

**Heat relief** comes from a riverside tile, flood plains, a lakeside tile, or
being on or adjacent to an accessible oasis. Salt water does not count. An enemy
occupying an oasis or lake source blocks its use. In peaceful foreign territory,
access to those sources requires Open Borders; uncontested enemy sources can be
used during war.

**Safe land** removes two points of accumulated exposure per turn. Heat, cold and
jungle exposure are tracked separately: an oasis clears heat, but does not instantly
cure jungle exhaustion. A badly affected unit can still suffer damage while recovering.

Embarking pauses exposure and its penalties. Landing restores any exposure the
unit was carrying. Lost health recovers through normal Civilization V healing;
clearing exposure does not restore health.

#### Which units are affected?

| Unit or support | Effect |
| --- | --- |
| Land military units | Follow the exposure rules, including AI armies and city-state troops |
| Scouts and other recon-class combat units | Two extra grace turns for every hazard |
| Workers and other civilians, ships, aircraft, barbarians | Exempt from military exposure |
| Same-team Medic I or II on the tile or adjacent land | Two extra jungle grace turns; multiple medics do not stack |
| Engineering | One extra cold grace turn |
| Biology | One extra jungle grace turn |
| Penicillin | Two more jungle grace turns |

Embarked medics do not provide the jungle benefit. Trade units have their own
[route rules](#trade-and-logistics), including infrastructure penalties.

### Ministry of Coin

The Ministry replaces the ordinary city Caravansary as a **national wonder**.
It is your empire's gateway to building roadside Caravansaries.

| Requirement or effect | Rule |
| --- | --- |
| Technology | Horseback Riding |
| Cost | 125 base production, increased by the national-wonder city-count adjustment |
| Limit | One per player |
| Maintenance | None |
| Origin-city trade benefits | +50% land trade range and +2 gold on international land routes from this city |
| Construction unlock | Allows workers to build Caravansaries once Engineering is known |

The trade benefits apply to the city containing the Ministry, not every city.
There is no prerequisite building to construct in every city. The Ministry cannot
be purchased or captured. Losing it prevents further Caravansary construction,
but does not switch off stations already completed.

![A caravan arriving at the Ministry of Coin](../../../shared/art/terrain-icons-round-3/wonder-a.png)

*The Ministry's included completion painting. This is artwork, not a screenshot.*

### Caravansary: roadside shelter and trade support

A Caravansary is a **worker-built tile improvement**. Earlier notes may call it a
Relief Station; the current player-facing name is Caravansary. It is separate from
the city building replaced by the Ministry.

| Requirement or effect | Rule |
| --- | --- |
| Unlock | Engineering and a Ministry of Coin somewhere in your empire |
| Location | Valid land in your territory or unclaimed territory |
| Construction | Normal Fort work time, adjusted for worker and game speed |
| Upkeep | No station maintenance; connected roads and a military defender retain their ordinary costs |
| Connection | The station tile and the land path to one of your cities need intact roads or railroads |
| Military relief | Clears all exposure on the station and adjacent land tiles at the next turn check |
| Defense | No defensive bonus |
| Trade | Can extend range, provide relief and support patrols |

#### Build and supply a station

1. Move an eligible worker to the chosen tile and cancel ordinary automation.
2. Choose **Build Caravansary** in the construction panel. Work continues on
   following turns; you do not need to click every turn.
3. Build a road on the station tile and connect it to any city you own. The city
   center itself does not need a separate road improvement.
4. End a military unit's turn on the supplied station or an adjacent land tile.
   Exposure clears at its next turn check. Passing through and leaving gives no reset.

Forest and jungle are preserved, subject to the normal Fort construction
requirements. Moving the worker, cancelling, or assigning a different job ends
the construction order. Loss of the Ministry pauses it; work and partial progress
survive saving and loading.

Supply can cross your land, neutral land and commercial-agreement partners' land.
Ordinary Open Borders is insufficient for commercial supply. An enemy on the
route, a pillaged road, a pillaged station or a gap in the road cuts that path.
An intact alternative path keeps supply working. Harbors and sea connections do
not supply these stations.

On neutral land, the builder owns the station. In claimed territory, the tile's
current owner controls it. Other armies cannot use your shelter; authorized partner
caravans can use your trade services. An ordinary Fort does not become a Caravansary.

![Approved Caravansary model with a gateway, courtyard and well](../../../docs/images/caravansary-preview.jpg)

*Preview of the approved custom model. It is not yet shown in the game; the current
build uses Fort graphics without the Fort's defensive bonus.*

#### Patrol a trade corridor

Station a land combat unit at a supplied Caravansary for a full turn. It then
protects authorized caravans along connected road branches up to the next city or
Caravansary. Moving the defender resets activation; pillage or loss of supply
disables the patrol. This protection applies to trade routes, not ordinary workers
or other civilians travelling nearby.

### Farms and outposts

The included [Irrigated Farm feature](../../irrigated-farm/docs/GUIDE.md) lets you
grow connected farms across flat desert. Its Irrigation Works building does not
require a Ministry of Coin.

If you also enable [Resource Outposts](../../resource-outposts/docs/GUIDE.md),
an intact outpost clears exposure for its owner's military unit on that exact tile
at the next turn check. Outpost shelter needs no road connection, has no adjacent
radius and does not heal health. It is not a trade relay or patrol station.

### Exposure and construction troubleshooting

**The army is beside a Caravansary but still exposed.** Check station ownership,
pillage and the complete road connection, including the station tile. Wait for the
next owner-turn check; relief does not occur while passing through.

**A unit is still injured after reaching safety.** Shelter clears exposure and
combat penalties. Health follows ordinary healing rules.

**A worker cannot build a Caravansary.** Check Engineering, a living Ministry,
tile ownership, normal terrain/feature requirements and worker automation. The
station's road is a separate worker action.

**The trade unit disappeared when I started a route.** Active trade is tracked in
the planner. Use **Active routes** and **Locate**; see the [trade section](#trade-and-logistics).

### Trade and logistics

Terrain v2 replaces ordinary trade orders with **Trade and logistics**, near the
upper right of the screen. Build commercial agreements, connect roads and stations,
then compare the extra income a route would add to your network.

Active routes appear in this planner rather than as animated units travelling on
the map. Your trade unit returns when the route finishes or is recalled; it is lost
if the route is destroyed. This experimental system has important
[differences from standard trade](#differences-from-standard-trade).

#### Launch your first route

1. Train a **Caravan**, **Motorized Caravan** or **Cargo Ship**. Select it in one
   of your cities while it still has movement available.
2. Open **Trade and logistics → Agreements**. Sign an agreement with the foreign
   destination and any other civilization whose territory the route must cross.
3. Open **Plan routes**. Choose a revealed destination and read the route's
   eligibility, efficiency, patrol coverage and additional net income.
4. Choose **Establish**. You need a free trade-route slot. The selected unit is
   committed to the route until it ends.
5. Use **Active routes** to locate or recall it, and **Accounts** to inspect income.

Domestic food routes need a **Granary** at the origin (Pottery; 60 base production;
1 gold maintenance). Production routes need a **Workshop** (Metal Casting;
120 base production; 2 gold maintenance). Neither needs a foreign destination
agreement, but transit through somebody else's land still requires commercial access.

#### Trade units

| Unit | Availability | What makes it useful |
| --- | --- | --- |
| Caravan | Animal Husbandry; 75 base production | The cheaper land trader for a developed route |
| Motorized Caravan | Combustion; 150 base production; no strategic resource required | Can cross roadless neutral land without Caravan Logistics and ignores environmental relief penalties |
| Cargo Ship | Sailing; 100 base production; coastal city required | Sea trade has no land-road or land-relief penalties; Astronomy is needed for ocean passage |

Researching Combustion does not replace existing Caravans or upgrade them
automatically. Both land units remain trainable. A completed or recalled route
returns the same type of unit that established it.

Land routes advance two tiles per turn; sea routes advance three. Roads improve
land **range**, not that route movement rate. Motorized Caravans are unarmed, and
their ability to ignore difficult terrain does not protect them from enemy raids.
Mountains, ice and water still block land routes.

![Covered motor truck proposed for the Motorized Caravan](../../../docs/images/motorized-caravan-preview.jpg)

*Approved custom model preview. The current build still uses ordinary Caravan
graphics; the truck is not yet an in-game model.*

#### Agreements and access

Commercial agreements are reciprocal: both partners may trade and permit transit.
They are separate from military Open Borders. AI partners accept during peace
when there are no denunciations.

War ends agreements. Peace does not renew them automatically. Revocation, lost
access or a relevant city changing hands can recall affected routes. If a route
crosses a third civilization, an agreement with the destination alone is insufficient.

#### Caravan Logistics and route range

**Caravan Logistics** is a Medieval technology following **Engineering**, with a
base research cost of 275. Before it, an ordinary Caravan needs roads through
neutral territory. The planner refuses a route that cannot meet that requirement.
If a road disappears after launch and the Caravan enters the newly roadless neutral
tile before the technology is researched, that route is destroyed.

After Caravan Logistics, ordinary Caravans can survive roadless neutral travel,
but still lose income when infrastructure or environmental relief is missing.
Motorized Caravans do not need this technology for roadless travel.

Range starts with the origin city's normal trade range and bonuses. The
**Ministry of Coin** increases land range from its own city by 50%. Each road
step costs half as much range as an ordinary land step. A reachable, supplied
Caravansary adds **five range**, up to **ten extra range per route**. The route must
be able to reach a station before using its extension; a distant disconnected
station cannot make an otherwise unreachable journey possible.

The planner can look for a route through suitable stations. Losing a station or
connection needed for range recalls the route.

#### Roads, relief and income

For an **ordinary Caravan**, two conditions affect payment:

- A break in continuous roads causes a **40% reduction**.
- Harsh terrain without suitable relief causes another **40% reduction**.

The reductions add together: payment is 100%, 60% or 20%. Mild terrain does not
need relief. Home territory, cities, freshwater heat relief and nearby supplied
Caravansaries can provide the applicable protection. Ordinary Caravan domestic
cargo is also reduced by its route efficiency.

For a **Motorized Caravan**, environmental relief is unnecessary. Its gold instead
depends on continuous roads and an actual supplied Caravansary stop:

| Continuous roads | Supplied station on the route | Gold payment |
| --- | --- | ---: |
| Yes | Yes | 100% |
| Yes | No | 60% |
| No | Yes | 60% |
| No | No | 20% |

The motorized station stop must be on the route, intact, authorized, and connected
by road to its owner's city. An adjacent station or oasis is not a commercial stop.
One qualifying stop removes that reduction. The separate range benefit can use
up to two stations. Motorized **food and production deliveries remain at 100% cargo
efficiency**, even when roads or stations are missing.

For example, a motorized route with continuous roads but no supplied station earns
60% of its full gold payment. A qualifying station stop restores it to 100%.
Pillaging that stop drops it back to 60% until service is restored.

##### Reading the income preview

**Additional net** shows what the new route adds after accounting for the existing
network. Use it to compare destinations; a longer journey is not automatically
the best investment.

Payments include commerce, a capped distance bonus, help with useful infrastructure
upkeep, and continuing income for roads and Caravansaries serving active routes.
Infrastructure shared by several routes is not charged repeatedly. Transit partners
can earn from useful infrastructure too. Extra traffic can increase that continuing
income, up to its cap.

These benefits continue while routes use the infrastructure; there is no one-time
payout for constructing and demolishing a station. Ordinary road and unit expenses
still apply. Some displayed expense allocations are estimates, so use **Accounts**
to understand the breakdown rather than treating every number as an exact cost for
one specific soldier.

Domestic routes deliver food or production instead of those commercial payments.
Their base delivery grows with era, is doubled for sea routes, and is then adjusted
by cargo efficiency. International routes can also provide science.

#### Patrols, raids and route completion

A land combat unit stationed at a supplied Caravansary for a full turn protects
authorized caravans along connected road branches until the next city or station.
Moving that unit resets the patrol; pillage or loss of supply disables it.
Ordinary civilian units do not receive patrol immunity.

An enemy combat unit at an unprotected route position can destroy the route and
gain **100 gold**. The committed trader is lost. Motorized traders still need
protection, even though they tolerate harsh terrain.

Routes run for at least the normal deal duration for the chosen game speed,
then finish their current circuit. **Recall** returns the trader immediately
to its origin, or to your capital if the origin is lost. A destroyed route returns
no unit. The active-routes list also shows foreign traffic when it is visible to you.

#### Differences from standard trade

Use **Accounts** for this system's trade income. The ordinary trade overview and
top-bar gold-per-turn forecast do not show these routes; income is paid to the
treasury on your turns.

Active routes have planner positions and **Locate** controls, but no animated
Caravan or Cargo Ship to select on the map. Raids are handled at those positions,
rather than through the normal plunder command.

The current build does **not** reproduce trade-related religious pressure, tourism
connections, World Congress embargo enforcement or trade-route quests. Some
civilization and policy interactions may differ from standard Brave New World.
Earlier alpha saves and existing native routes are not converted. Start a new game.

#### Trade troubleshooting

**Establish is disabled.** Check remaining movement, an idle trader in your own
city, a free trade slot, agreements, revealed destinations and the stated route
requirements. An identical route of the same cargo type cannot operate twice.

**The route lost income.** Look for broken roads, missing relief or—on a motorized
route—a lost station stop. Infrastructure is checked again as conditions change.

**A station did not extend range.** It must be supplied, accessible and reachable
before its bonus is used. Another player's city does not count as its owner's
road connection.

**Why does the AI still build ordinary Caravans?** They cost less. The AI can
prefer them when they can operate a route as efficiently as the motorized option.

[Back to the mod collection](../../../README.md) · [Installation and compatibility](../../../docs/GAMEPLAY.md)
