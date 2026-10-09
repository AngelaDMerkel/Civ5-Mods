# Irrigated Farm: player guide

[Mod collection](../../../README.md) · [Installation](../../../docs/GAMEPLAY.md#install-a-packaged-test-build)

## Goals

Make water access a network you can extend, maintain and defend. Irrigated Farm
lets you turn connected stretches of flat desert into farmland, while making the
position of each field matter to those farther from the water source.

## What the mod adds

- **Irrigation Works**, an Engineering-era building that permits new irrigated
  farm construction on tiles assigned to its city.
- **Connected desert farms** supplied by rivers or nearby mountains, lakes and
  oases, with additional farms carrying water across your land.
- **Changing food yields:** supplied farm improvements add +3 food; disconnected
  ones add +1. Broken links can dry out an entire branch.
- **Continuing worker orders and AI support** for extending and repairing networks.

**Status:** included with Realistic Terrain v2; no separate farm package. Requires
a new single-player Brave New World game; in-game testing is still pending.

## How it works

[Construction](#grow-your-first-network) · [Buildings and yields](#irrigation-works-and-farm-yields) ·
[Water connections](#what-carries-water) · [Maintenance](#maintain-and-repair-the-network)

### Grow your first network

1. Research **Engineering**.
2. Build or purchase **Irrigation Works** in the city assigned to the intended tile.
3. Find owned, flat desert with a river on the tile, or a mountain, lake or oasis
   next to it.
4. Select a worker there and choose **Build Irrigated Farm** in the construction
   panel. An ordinary farm can be replaced.
5. Extend the network by building on eligible desert tiles adjacent to your
   connected irrigated farms.

You do not need a Ministry of Coin or a road. Construction takes the normal Farm
work time, including worker and game-speed modifiers. One click starts continuing
work; the worker does not need a new order each turn.

### Irrigation Works and farm yields

| Building or improvement | Requirements | Effect |
| --- | --- | --- |
| Irrigation Works | Engineering; 100 base production; 1 gold maintenance | Permits new farm construction on tiles assigned to that city |
| Supplied Irrigated Farm | Eligible tile connected to a real source | +3 food from the improvement |
| Disconnected farm | A completed farm whose water path is broken | +1 food from the improvement |
| Pillaged farm | Needs the normal Repair action | No improvement yield; cannot carry water |

The food values are the improvement's contribution, not the entire tile yield.
Terrain, resources and ordinary Farm technology bonuses apply on top. The city's
citizens still need to work the tile to collect its food.

Irrigation Works can be bought normally. It does not provide the Aqueduct's food
storage benefit. A tile shared between cities must be assigned to a city with
Irrigation Works before new construction can proceed. You can reassign it in the
city screen.

Completed farms keep working if the building is sold, as long as they retain their
water connection. Selling or losing the building pauses unfinished construction
that still needs it.

### Where farms can be built now

The current gameplay supports **owned flat desert**, including flood plains and
wheat. A worker can use unimproved land or replace an ordinary Farm.

Hills, oases, other visible resources and special improvements are protected.
The action does not clear features or extract strategic or luxury resources.
Terraced hills and broader terrain compatibility are planned; their concept art
does not mean those tiles are currently eligible.

### What carries water?

| Counts as a source or connection | Does not carry irrigation |
| --- | --- |
| A river on the farm tile | Coast or ocean water |
| An adjacent mountain, lake or oasis | Ordinary Farms |
| An intact irrigated farm belonging to you, connected to a source | Roads or city centers |
| A continuous chain across your own cities' land | Foreign or teammate farms |

Natural sources can lie outside your borders. A unit standing beside or on a
source does not cut irrigation; damage to a connecting farm does.

Every branch needs a continuous path to a real source. A ring of farms cannot
keep itself watered after its final source connection is lost. An alternative
intact path does keep the network working.

**Example:** a mountain supplies Farm A, which connects to B, then C. All three
receive the supplied improvement yield. If B is pillaged, it stops carrying water,
and C drops from +3 to +1 improvement food unless it has another path. A remains
supplied. Repairing B restores the path.

Irrigation does not make every watered tile count as ordinary freshwater for other
game rules. Mountain-fed farms retain the usual dry-Farm technology progression;
naturally fresh-watered tiles keep their normal Civil Service benefits. Irrigation
does not provide desert heat relief to an army or make a city eligible for a Garden.

### Maintain and repair the network

Pillaging, replacing or capturing a connecting farm can interrupt water. Dry farms
remain in place at the lower yield. Use the normal worker **Repair** action on a
pillaged link; simply reconnecting it does not repair the pillaged improvement.

The worker panel reports water connectivity, and tile names/yields reflect whether
farms are supplied. If an unfinished job loses water or its required building,
construction pauses. Moving the worker, cancelling, or selecting another job ends
the assignment. Partial work and continuing orders survive saving and loading.

The AI can commission useful Irrigation Works and use available workers to extend
or repair networks. Its balance and timing still need in-game testing.

### Planned appearance and terraces

The image below is **approved concept art for a future appearance**, including
terraced hills and matching tile edges. It is not a screenshot or a picture of
currently playable hill farming. Current farms use Civ V's ordinary Farm graphics;
Irrigation Works uses the Aqueduct icon.

![Irrigated Farm concept showing connected fields, hill terraces and water channels descending from a mountain](../../../shared/art/irrigated-farm/irrigated-farm-adjacency-v6.png)

*Planned farm and terrace appearance. Flat-desert gameplay remains the current rule.*

### Common questions

**There is a mountain nearby, but construction is disabled.** The first farm must
be adjacent to that mountain, or have another valid source or farm connection.
Check flat desert, ownership, the tile's assigned city and Irrigation Works too.

**My farms form a loop. Why did they dry out?** A loop is a connection, not a water
source. Restore a path to a river, mountain, lake or oasis.

**Why did a neighboring civilization's farm fail to help?** Water links only pass
through farms you own, even when another civilization is a teammate or has Open Borders.

**Do I need Irrigation Works in every city?** You need it in the city assigned to
each tile while building new farms there. Existing farms may share water across
your city boundaries and keep working after a building is sold.

[Back to the mod collection](../../../README.md) · [Installation and compatibility](../../../docs/GAMEPLAY.md)
