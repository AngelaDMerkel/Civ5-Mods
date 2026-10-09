# Connected desert irrigation

Part of Realistic Terrain v2, with no new DLL or external art. Start a new game;
earlier v2 alpha saves are not a supported migration target for the new SQL rows.

## Rules

Irrigation Works is an ordinary city building at Engineering: 100 base production,
1 gold upkeep. It gates construction in land assigned to that city through
`GetWorkingCity()`. It has no aqueduct food-storage bonus. It can be purchased
normally; there is no Ministry requirement. Completed farms need water, but not
the continued presence of the building. Moving a shared tile between cities
changes which city's building is required for unfinished construction.

Irrigated farms occupy flat desert only, including wheat and flood plains. They
replace an ordinary farm or occupy unimproved land. No oases/features are cleared,
no other visible resources are improved, and no special improvements are replaced.
Hidden deposits behave as in native builds; revealing one later does not destroy
a farm. Irrigation does not extract strategic or luxury deposits.

Sources are rivers on the farm tile and adjacent mountains, lakes or oases.
Natural sources can be outside the owner's borders. Their physical presence is
what counts; occupying them does not stop water. Pillage the canal/farm to stop
flow. Connections run through unpillaged irrigated farms of the same owner,
including across that owner's city boundaries. Foreign/team farms, ordinary
farms, cities, roads and salt water do not transmit irrigation.

The improvement adds 3 food when supplied and 1 food when dry. Native terrain,
resource and copied farm technology modifiers apply on top. In particular,
mountain irrigation does not make a plot native freshwater: it keeps the normal
dry farm Fertilizer progression. River/lake/oasis freshwater farms keep Civil
Service progression. No heat-exposure or native garden eligibility is changed.

## Implementation and timing

`RT_Irrigation.lua` flood-fills intact farm components from actual sources, with
owner boundaries enforced on every edge. Dry nodes transmit water once reconnected;
the stored wet state never counts as a water source. Alternate paths work, and
source-free cycles dry out. Build eligibility uses an independent live traversal,
so stale wet improvement state cannot allow construction from a severed branch.

Two ordinary improvement definitions hold wet/dry yields. Switching updates native
tile yields and city assignment; no food is credited directly and no extra-yield
counter accumulates across saves. Pillaged nodes are never switched because the
native `SetImprovementType` function silently repairs them. The native Repair
action is required, after which the network can switch state normally.

The native BNW source calls `PlayerDoTurn` **after** city production, so that event
alone is insufficient. Reconciliation also runs on `AIProcessingStartedForPlayer`,
`AIProcessingEndedForPlayer`, `ActivePlayerTurnEnd`, improvement display events,
build completion, border/capture events and load. Turn-boundary passes scan all
plots regardless of visibility; display events are supplemental. Reentrant
callbacks are guarded. Native event dispatch timing remains an acceptance test,
especially an unseen AI pillage immediately before its victim's food processing.

One-click custom orders reuse native build progress, work rate and farm build
time. The start and each work step check the city building, technology, tile,
ownership and live water path. Water/building loss pauses work. A shared saved
per-worker/turn stamp prevents duplicate work across station, irrigation and the
optional Resource Outposts system. Native `Unit_Builds` intentionally has no
irrigation action that could bypass these gates.

AI construction is bounded to one idle worker per owner-turn within six hexes,
using revealed owned land and avoiding visible nearby enemy troops. Repairs have
priority. Construction uses the same persistent order as humans. Building orders
append to ordinary production queues, only with a useful available water source,
an existing worker and sufficient income/reserves. Other native AI decisions can
still reprioritize production or workers; in-game tuning remains necessary.

Primary engine references: [plot build/yield and pillage behavior](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvPlot.cpp)
and [player turn ordering](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvPlayer.cpp).
The installed Mac UI registers the AI processing events in
`Assets/UI/InGame/WorldView/MPTurnPanel.lua` and `Assets/UI/InGame/TurnProcessing.lua`.

## Verification

Automated Lua 5.1 tests cover source types, chains, disconnected cycles, alternate
paths, pillage/repair, capture, source loss, coast rejection, existing farms after
building sale, duplicate/reentrant refresh, save reload, local building and tile
gates, partial work, turn guards, order cancellation, real UI button callbacks,
AI production, repairs, movement, outpost reservations and unsafe paths.

Database checks use in-memory copies of the installed BNW database to verify the
building, art atlases, desert/flatland definitions, yields, wheat, technology
bonuses and absence of ungated native worker actions. Both mod combinations and
SQL load orders remain covered, with ZIP/source/hash parity checked.

Run inside a new single-player BNW game before release:

- [ ] Build/purchase Irrigation Works; check cost, upkeep, icon and Civilopedia.
- [ ] A worker has no native ungated irrigation action. The custom button requires
      the local building, Engineering and water; no Ministry is needed.
- [ ] Start at a mountain and grow a four-farm chain into the desert. Check
      grassland/hill/oasis/resource rejection and wheat/floodplain acceptance.
- [ ] Pillage the first farm. Downstream food drops by 2 per worked farm before
      city food/growth is processed; the pillaged farm remains pillaged. Repeat
      with an AI pillaging outside the human view just before the victim's turn.
- [ ] Repair, replace, capture and reconnect individual links. A branch with an
      alternative water path stays supplied; a source-free loop becomes dry.
- [ ] Inspect tile tooltips, citizen assignment and actual food accumulation for
      wet/dry farms, Civil Service and Fertilizer. Look for stale food totals.
- [ ] Save/reload a dry loop, a pillaged connection and a half-finished order.
      No auto-repair, free work or extra food should occur.
- [ ] Sell/rebuild Works and reassign a shared tile. Unfinished construction
      pauses/resumes correctly, while existing connected farms retain their yields.
- [ ] Check worker UI at 1024x768 and widescreen, both alone and with Resource
      Outposts enabled. Irrigation and outpost panels must not overlap.
- [ ] Run AI desert cities through construction and pillage/repair on Quick and
      Marathon. Confirm worker coordination, production queues and turn time.
