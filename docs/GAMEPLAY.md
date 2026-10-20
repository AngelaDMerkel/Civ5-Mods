# Player guides

Build routes through difficult country, claim distant resources and develop
connected farms. These guides explain the current experimental **Realistic Terrain
v2** and **Resource Outposts v1** builds for Civilization V: Brave New World.

## Choose what to play

| Guide | What you will learn | Current availability |
| --- | --- | --- |
| [Realistic Terrain](../mods/realistic-terrain/docs/GUIDE.md) | Exposure, Caravansaries, Ministry of Coin, trade units and route management | Experimental Terrain v2 build |
| [Resource Outposts](../mods/resource-outposts/docs/GUIDE.md) | Claim resources, defend sites, manage upkeep and abandon or convert an outpost | Experimental Outposts v1 build |
| [Irrigated Farm](../mods/irrigated-farm/docs/GUIDE.md) | Build Irrigation Works, connect farms to water and repair broken networks | Included with Terrain v2 |
| [Climate Change](../mods/climate-change/docs/GUIDE.md) | Understand the proposed warming-or-cooling system | Planned; no playable build |

Terrain and Outposts can be enabled separately or together. With both enabled,
an intact outpost also shelters its owner's military unit on that tile. Outposts
do not need Terrain, roads, trade agreements or a Ministry of Coin to supply resources.

**These are development builds, not a finished release.** In-game testing is
still pending. Artwork and model previews are captioned below and in the guides;
they should not be mistaken for screenshots of the current game.

![A trader arriving at the Ministry of Coin beneath mountains](../shared/art/terrain-icons-round-3/wonder-a.png)

*Ministry of Coin completion artwork included with Terrain. This is an illustration,
not a gameplay screenshot.*

## Install a packaged test build

Use a packaged **Realistic-Terrain-v2.zip** or **Resource-Outposts-v1.zip** supplied
for testing. The repository's source-code download, artwork collections and model
preview kits are not installable mods. A public release download is not linked
from these guides yet.

1. Extract the package you want. It contains **Realistic Terrain (v 2)** or
   **Resource Outposts (v 1)**.
2. Copy that folder into Civilization V's **MODS** folder. Typical locations are:

   - Windows: `Documents\My Games\Sid Meier's Civilization 5\MODS`
   - macOS: `~/Library/Application Support/Sid Meier's Civilization 5/MODS`

3. Start Civilization V with **Brave New World**. Open **Mods**, enable either
   package or both, and continue through the Mods menu.
4. Start a **new single-player game**. To continue later, load the save through
   Mods with the same mods enabled.

Irrigated Farm currently comes with Realistic Terrain; there is no separate farm
package to install. Do not enable old **Realistic Terrain v1** alongside Resource
Outposts. Older alpha saves are not supported, and adding or removing these mods
mid-game is not supported.

## Your first few turns

With **Terrain**, select a land military unit and watch the **Environment** panel
when it ends turns beyond friendly borders. Plan safe stopping points rather than
assuming a long expedition can cross desert or snow without support.

For trade, use **Trade and logistics** near the upper right. Select a ready trade
unit in one of your cities, sign any required agreements, then use **Plan routes**.
The [trade section](../mods/realistic-terrain/docs/GUIDE.md#trade-and-logistics) explains the
differences from ordinary Brave New World trade.

At **Engineering**, workers can begin the new construction actions once their
other requirements are met. Caravansaries need a Ministry of Coin; irrigated farms
need Irrigation Works in the tile's city and a water connection. Resource Outposts
need a suitable neutral resource deposit and its usual extraction technology.

## Compatibility and saves

The current target is single-player Brave New World. Multiplayer, hotseat,
vanilla Civilization V, Gods & Kings without BNW, and major overhaul combinations
have not been validated. Other mods that alter trade, worker actions or the same
buildings may conflict. Start with these packages alone when testing.

Terrain changes how trade operates: active routes are managed in its planner,
and some standard trade effects are absent. Read the
[trade differences](../mods/realistic-terrain/docs/GUIDE.md#differences-from-standard-trade)
before choosing it for a game. Outposts by itself leaves standard trade unchanged.

## Common questions

**Why is a worker action unavailable?** Select your own worker during your turn,
check the technology and tile requirements, and cancel ordinary worker automation
before starting a custom job. Each mod guide lists its exact requirements.

**Do I have to order construction every turn?** No. One click starts continuing
work. Moving the worker, cancelling, or assigning a different job ends that
assignment. Temporary loss of a required building or water connection can pause it.

**Why don't the new buildings look like the illustrations?** The selected icons
and Ministry painting are included, but the custom map models are still being
prepared. Current Caravansaries and outposts use fort graphics, irrigated farms
use farm graphics, and Motorized Caravans use Caravan graphics.

**How can I report a problem?** Describe the enabled mods, game speed, action you
took, what you expected, and what happened. A screenshot and a save from just before
the problem are helpful. Mention whether the problem persists after reloading.

[Back to the mod collection](../README.md) · [Development information](DEVELOPMENT.md)
