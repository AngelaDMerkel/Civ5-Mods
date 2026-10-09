# Workshop preparation

Realistic Terrain v2 and Resource Outposts v1 are packaged locally. Nothing has been published or uploaded.

Terrain's current [listing and release checklist](../mods/realistic-terrain/docs/RELEASE.md)
include the moving convoy markers, Congress embargoes and combined income forecast.

## Files and workflow

- `dist/Realistic-Terrain-v2.zip`: Realistic Terrain v2, UUID
  `d571e16c-bb58-40bf-a81f-a919249e7995`; source in `mods/realistic-terrain/src/`
  plus `mods/irrigated-farm/src/`; complete project in `build/realistic-terrain/`.
- `dist/Resource-Outposts-v1.zip`: Resource Outposts v1, UUID
  `4547ae42-3d17-4993-99e8-a7a5a2c1ec2c`; source in `mods/resource-outposts/src/`;
  complete project in `build/resource-outposts/`.
- Each ZIP contains its own installable folder and `.modinfo`. These are ordinary
  ZIPs, not `.civ5mod` archives; do not rename them.
- Both `.civ5proj` scaffolds are generated but have not been built in ModBuddy here.
- Publish as independent mods. Resource Outposts has an optional RT v2 reference,
  no RT dependency, and blocks the old bundled RT v1. Start new games.

After completing the native play-test, use the Civ V SDK / ModBuddy publishing
workflow in a compatible development environment. Confirm the project settings:

1. Brave New World dependency: `6DA07636-4123-4018-B643-6575B4EC336B`.
2. Single-player enabled; multiplayer and hotseat disabled; affects saved games.
3. Import each package's `Lua/*.lua` and runtime `Art/*.dds` files into VFS;
   enable landmark system reload. The generated manifests/projects do this.
4. Database activation actions: `Text/RT_Text.xml`, then `SQL/RT_Promotions.sql`,
   then `SQL/RT_ReliefStation.sql`, `SQL/RT_MinistryOfCoin.sql`, `SQL/RT_Trade.sql`,
   `SQL/RT_MotorizedCaravan.sql`, `SQL/RT_Irrigation.sql`, then `SQL/RT_Art.sql`.
   Resource Outposts uses only `Text/RO_Text.xml` and `SQL/RO_Outposts.sql`.
5. InGameUIAddin: `UI/RT_Environment.xml` for RT; `UI/RO_UI.xml` for RO, each
   with its matching Lua file.
6. Build, test the built output, add a gameplay screenshot as the preview, and
   publish using the Workshop account that will maintain the mod.

If the scaffold needs adjustment for your SDK version, create a new empty Civ V
project and add these same files/settings. Do not publish a Windows DLL: this mod
does not contain one. Keep the UUID stable for updates; increase the integer mod
version and document any save compatibility changes.

Before publication, confirm the displayed author name (currently `Duffy`), review
the description below, and add screenshots from an actual game. Selected custom
portraits, the worker-action glyph and the Ministry painting are bundled; other
icons, styles and 3D fallbacks reference stock assets. No game art is redistributed.
The real Civ V reference images under output/ are excluded from the packages.
Map-Model-Sources-v1.zip is an authoring bundle, not a Workshop-ready mod; its GR2
conversion, final texturing and game integration remain pending.

Official references:

- [Civ V SDK installation](https://support.civilization.com/hc/en-us/articles/37707596624531-Civilization-V-Where-is-the-SDK)
- [Civ V Steam Workshop](https://steamcommunity.com/workshop/about/?appid=8930)

## Listing draft

**Realistic Terrain — Environmental Exposure**

Harsh terrain now matters to military expeditions. Land military units accumulate
heat, cold, and jungle exposure when operating beyond their own borders. Prepare
with scouts and medical support, use freshwater to cross deserts, and bring your
armies home to recover.

- Desert, tundra, snow, and jungle exposure with clear grace periods.
- Gradual combat penalties and nonlethal attrition.
- Oasis, river, lake, and floodplain relief from heat.
- Automatic protection inside your own or teammate's borders.
- Irrigation Works unlock desert farms with a continuous water connection.
  Pillaging a connecting farm cuts downstream food bonuses; repairing restores them.
- Scout endurance, forest shelter, medics, and technology support.
- Ministry of Coin national wonder replacing the city Caravansary, retaining its
  local trade benefits and unlocking Caravansary outpost construction.
- Worker-built Caravansaries that clear exposure when connected by intact roads
  to one of your own cities. Pillaging or blocking the supply route cuts relief.
  Select a worker and issue Build Caravansary once; construction continues automatically.
- Mac-compatible replacement trade with bilateral agreements and transit access.
- Caravan Logistics technology, Caravansary range relays, and caravan-only patrols.
- Optional Motorized Caravan at Combustion: ordinary Caravans stay available.
  Crosses all passable land without environmental penalties; missing roads and
  a supplied Caravansary stop each reduce gold by 40%. Domestic cargo remains full.
  Mountains, water, agreements, range and raids still matter. Stock Caravan artwork
  is used for this first version.
- Up to 80% infrastructure penalties, shared cost compensation, and permanent dividends.
- Custom trade planner, moving map portrait markers, combined income forecast,
  Congress embargo enforcement, and deliberate AI logistics.
- Optional Resource Outposts companion: an intact outpost shelters its own stationed
  military unit, with no roads required. Resource claims belong to the companion mod.
- Selected-unit status panel with exposure details and a next-turn forecast.
- Same military rules for human and AI civilizations.

Requires **Brave New World**. **Single-player only. Start a new game through the
Mods menu.** Civilians, naval units, aircraft, and barbarians are exempt. No custom
DLL or new terrain assets. This is an early balance-testing release; overhaul and
multiplayer compatibility are not claimed.

Environmental damage cannot reduce a unit below 25% of maximum HP. Returning home
clears exposure but does not heal combat damage. Embarking pauses exposure rather
than resetting it.

## Replacement-trade disclosure

The Workshop listing must explain that this replaces native trade. Moving map
portraits represent simulated convoys; native animated 3D units remain deferred.
Income is credited each owner-turn and Accounts supplies a combined empire
forecast. Congress embargoes are enforced. Native trade overview/top-bar GPT,
religious pressure, tourism connections and trade-route quests do not integrate
these routes. Start a new game; earlier alpha saves are not migrated. Do not
describe native rendering, AI balance or engine timing as verified until the
native game acceptance tests pass. WSDLC/native GameCore integration is a
[separate proposed path](../mods/realistic-terrain/docs/NATIVE-INTEGRATION.md).

## Resource Outposts listing draft

Claim distant land strategic and luxury deposits without founding cities. Workers
build fortified Resource Outposts on neutral deposits after Engineering and the
normal extraction technology. Garrison a defender, repair pillaged sites, capture
wartime enemy claims, or abandon unwanted sites. Base upkeep is 2 gold per turn,
subject to building-maintenance modifiers. Notifications show resource losses
and recoveries. AI civilizations build, escort, defend and repair their claims,
replace wounded guards, recover at nearby safe locations, retry stalled expeditions
and scale expansion to their income and army. An overview lists sites, defenders,
resources and upkeep. Abandonment previews resource consequences; annexed outposts
can optionally convert into ordinary improvements and stop charging upkeep.

**No roads, supply connections, Ministry or trade agreement required.** Works
independently of Realistic Terrain. Enabling both adds shelter for your military
unit on an intact outpost tile; it adds no road requirement or trade services.
Neutral-land access and pillaging follow native rules; these claims do not expand
cultural borders. Requires Brave New World and a new single-player game. No DLL.
Native gameplay and UI testing remain pending for this alpha.
