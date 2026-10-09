# Terrain v2 release preparation

Local alpha package only. Workshop publication, native model conversion and
in-game acceptance remain deferred. UUID and integer mod version are unchanged.

## Workshop description draft

**Realistic Terrain — Expeditions and Trade Logistics**

Prepare your expeditions and build trade corridors worth protecting. Desert,
tundra, snow and jungle wear down military units outside friendly home territory.
Freshwater, support units, technology and road-connected Caravansaries help them
recover. Exposure penalties are gradual and environmental damage is nonlethal.

Build the Ministry of Coin to unlock worker-built Caravansaries. Connect them to
their owner's cities, use them to extend caravan range, and station military
garrisons to protect convoys on their roads. This protection does not make ordinary
civilians safe from capture.

Sign reciprocal trade agreements and develop infrastructure with your partners.
Missing infrastructure can reduce route gold by 80%. Useful roads, stations and
garrisons earn shared upkeep compensation and continuing infrastructure dividends
for as long as eligible trade uses them.

Caravan Logistics opens roadless unclaimed territory to ordinary Caravans.
Combustion adds the optional Motorized Caravan: it crosses passable land without
environmental restrictions, while missing roads and a supplied Caravansary stop
still reduce its gold. Ordinary Caravans remain available. Mountains, water,
agreements, range, embargoes and raids still matter.

Use **Trade and logistics** to plan routes, sign agreements and recall convoys.
Moving map portraits show your convoys and visible foreign traffic. **Accounts**
shows the trade breakdown and a combined empire gold forecast. World Congress
embargoes halt affected commerce and recall invested trade units.

This package also includes connected desert irrigation. Resource Outposts is an
optional, independent companion; enabling it adds shelter for its stationed
defenders without adding a road requirement to its resource claims.

**Requires Brave New World. Single-player only. Start a new game through Mods.**

This is a replacement trade system. Native trade overview and top-bar GPT do not
include its routes; use Accounts. Native trade religious pressure, tourism
connections and trade-route quests are not supplied by these convoys. Raid
detection uses the mod's route positions. Map portraits are UI markers, and stock
3D models remain in use while approved custom models await conversion. Motorized
Caravans currently reuse the Caravan portrait/model fallback. No multiplayer or
overhaul compatibility is claimed. English text only. Native playtesting and
balance acceptance are pending.

## Build and package

From the repository root:

```sh
python3 tools/build.py
python3 tools/validate.py --cache "/path/to/Civ V/cache"
python3 tools/test.py  # Python environment with tests/requirements.txt installed
python3 -m unittest discover -s tests -p 'test_*.py'
```

The builder writes `dist/Realistic-Terrain-v2.zip` and a complete ModBuddy project
under `build/realistic-terrain/`. The ZIP is a local installable folder archive,
not a `.civ5mod` file; do not rename it. Lua/UI and SQL activation are generated
from the existing package registry. No model-authoring bundle, reference extract,
test code or source-review gallery belongs in the playable ZIP.

## Evidence still required before publication

- Native model conversion/rigging and map-art integration, separately from the
  already recorded source design approvals (deferred item 1).
- A new-game Mac BNW acceptance run: save/reload, agreements, sanctions/repeal,
  a long road/relay corridor, road/station pillage, patrol activation, civilian
  capture, both caravan types, land/sea routes and shared income. Compare treasury
  changes against the ledger over multiple owners' turns (deferred item 3).
- Native UI review at 1024×768 and widescreen: moving portraits, fog transitions,
  wrapped maps, stacked convoys, scrolling long text, Escape/city/strategic views,
  and optional Outposts worker panels. Check that markers neither block important
  native controls nor reveal hidden traffic.
- Actual gameplay screenshots for the Workshop preview: exposure, a developed
  corridor, agreements and Accounts. Do not present mockups/source renders as
  screenshots of the released game. New promotional art or a dedicated motorized
  portrait/flag still follows options → real Civ V comparison → user selection.
- Build with a compatible Civ V SDK/ModBuddy publishing environment, verify the
  resulting install, confirm author/listing details and obtain publication approval.

Full native religion/tourism/quest parity is a separate GameCore integration
decision, documented in [NATIVE-INTEGRATION.md](NATIVE-INTEGRATION.md). The current
listing must retain the standalone limitations unless that integration is built
and accepted. WSDLC packaging/installation is not yet validated for this package.

## Merge handoff

Implementation lives on `codex/terrain-trade-completion`. Its commits modify
Terrain-owned runtime/tests/docs and the existing shared player/release/testing
notes; shared packaging tools and the other mods' source are unchanged. Another
chat is developing player guides: carry the new
marker, embargo, forecast and compatibility descriptions into those guides when
combining the branches. This note does not authorize a merge or publication.
