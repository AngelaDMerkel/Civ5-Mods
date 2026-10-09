# Replacement trade rules and implementation

The user selected native Mac support on 2026-10-09. This implementation therefore
replaces the trade-route simulation in Lua. Stock Caravan and Cargo Ship native
trade actions are disabled; their production costs, art and idle units remain.
Launch and manage routes with **Trade and logistics**. Start a new game.

## What operates now

- Reciprocal agreements for international routes and third-party transit, separate
  from military Open Borders. AI acceptance requires peace and no denunciation.
  Agreements continue until revoked or broken by war; peace requires a new one.
- A saved route invests a real Caravan, Motorized Caravan or Cargo Ship, occupies a native-capacity slot,
  follows a revealed permitted path, and returns the unit after completion/recall.
  Destruction permanently consumes it. Active units exist as simulated positions
  in the planner, not native map units; Locate centers the map on that position.
- Ordinary Caravans need roads in neutral land until **Caravan Logistics** (Engineering
  prerequisite, Medieval, base research 275). A new invalid route is refused.
  An existing caravan dies when it enters a newly invalid neutral tile.
- Native city trade range is retained. Road edges cost 50 range hundredths and
  other steps 100. A reachable supplied Caravansary adds 500 range hundredths,
  at most twice per route. A disconnected relay cannot bootstrap itself. The
  planner searches alternate paths through relays when the direct path is too far.
- Missing a continuous road reduces payment by 40%; missing relief on harsh
  tiles adds another 40%. Full efficiency is 100%, one deficiency 60%, both 20%.
  Motorized Caravans use separate commercial deductions described below. No land penalties apply to sea
  trade. Ocean passage requires Astronomy.
- A mature garrison at a supplied station patrols road branches until the next
  station/city. It protects authorized simulated caravans from raids. It gives no
  civilian promotion or immunity. Moving resets activation; pillage/supply loss
  disables it. An enemy combat unit at an unprotected caravan position destroys
  the caravan and receives 100 gold. Raids are checked during movement and turns.
- Roads through agreement partners can connect a station to its owner's city.
  Caravans may use partner stations. Ordinary army relief remains owner-specific.
- One-click worker orders persist across saves, use real worker speed/build time,
  and cancel on movement or another construction order. Missing Ministry pauses
  work. AI uses native production, worker missions and existing troops to develop
  one cooperative corridor at a time; it receives no free infrastructure.
  Hostile AI field troops can pursue visible traffic or its defending station.
  The active-routes tab also shows foreign traffic currently in your vision.

## Motorized Caravan

**Combustion** unlocks an optional Motorized Caravan costing **150 production**
with no strategic resource requirement. The **75-production ordinary Caravan**
remains available. There is no upgrade-chain replacement, automatic conversion or
obsolescence change. The AI keeps ordinary traders in service and prefers the
cheaper unit when it can operate the planned corridor at equal or better gold
efficiency; it trains a motorized alternative when that unit opens or improves it.

The Motorized Caravan crosses roadless neutral land without Caravan Logistics.
Desert, tundra, snow and jungle impose no exposure, movement-cost or relief penalty.
It traverses all passable land; mountains, ice and water still block land routes.
Trade and transit agreements, revelation, range, capacity and enemy raids remain.

Its gold depends on commercial infrastructure, independently of terrain:

| Continuous roads | Supplied Caravansary stop | Gold efficiency |
| --- | --- | --- |
| Yes | Yes | 100% |
| Yes | No | 60% |
| No | Yes | 60% |
| No | No | 20% |

A stop must lie **on the route**, be intact and authorized, and retain its road
connection to its owner's city. An adjacent station, oasis or own-territory relief
is not a commercial stop. One qualifying stop removes the station deduction; the
separate range-relay cap remains two. On launch, the planner seeks a reachable
station detour if it improves gold efficiency, even when extra range is unnecessary.
Active routes keep their chosen path. Pillage or supply loss removes the service
discount until restored; roads and stations are evaluated again each turn.

These infrastructure deductions apply to **gold only**. Motorized domestic food
and production deliveries have 100% cargo efficiency even without infrastructure
or environmental relief. International science retains its existing calculation.
Ordinary Caravan cargo and relief rules are unchanged.

Range and route speed are unchanged. Roads still halve range cost; supplied
Caravansaries still extend range and support road patrols. Useful infrastructure
continues earning compensation and dividends, including motorized service stops.
The idle native unit has two moves, ignores terrain movement costs, has no combat
capability and inherits the Caravan's maintenance exemption.

Researching Combustion does not change existing routes or units. Saves retain the
invested unit type, and completion or recall returns that same type. Native Caravan
art, portrait and flag are reused until dedicated vehicle artwork is available.

## Continuing income

For each participant:

`payment = (commerce + distance + allocated upkeep + infrastructure dividend) × efficiency`

`net = payment − allocated actual expenses`

The game still charges road/unit maintenance. The mod credits payment to the
treasury once per owner-turn, preserving fractional gold in the save. It does not
subtract those expenses a second time. A route preview reports the change in net
income compared with the existing network, so shared assets are not billed twice.

Initial tunable values in `mod/Lua/RT_TradeEconomy.lua`:

| Component | Initial value |
| --- | --- |
| Commerce | 2× each participant's native gold quote, including city bonuses |
| Distance | 0.2 gold per straight-line hex, capped at 40 hexes, divided between participants |
| Road capital value | 12 gold per useful road tile; 18 for railroad |
| Caravansary capital value | 40 gold per useful outpost |
| Infrastructure dividend | 2% of standardized capital per active turn, indefinitely |
| Extra route utilization | +25% dividend per extra route, capped at twice the base dividend |
| Garrison reimbursement | At most 2 gold per required garrison per turn; no capital dividend |

The capital values represent worker effort; they are not additional construction
charges. Only infrastructure used by an active valid route earns. A station must
provide relief, a range extension, or patrol support to qualify. Road and station
IDs are stable map positions. Repairing, rebuilding, transferring ownership or
restarting a route grants no new upfront payment and resets no repayment timer:
there is no repayment deadline. Loops are rejected. Distance rewards exclude
artificial detours. Shared upkeep is divided across operating routes once.

Road reimbursement allocates the player's actual aggregate improvement maintenance
in proportion to standard asset costs, accounting approximately for maintenance
discounts. Neutral road builders are recorded from build events. Unattributable
pre-existing neutral roads do not earn reimbursement. Garrison expense is an
empire-average estimate because stock Lua does not expose an individual unit bill.
These are allocated cost estimates, not exact marginal maintenance calculations.

Domestic routes require the origin's Granary (food) or Workshop (production).
Their per-turn base delivery is `3 + current era index`, doubled at sea, multiplied
by cargo efficiency (100% for Motorized Caravans) and rounded down with a minimum of one. They do not
pay commercial subsidies or dividends. International science uses native quote
functions and credits research progress, with fractional beakers retained.

## Native-game differences and release limits

- The native trade overview and top-bar GPT forecast do not know these routes;
  use the custom ledger. The treasury receives their income each owner-turn.
- Active caravans have no animated native unit or native plunder command. The
  mod performs raid detection against their simulated positions instead.
- Religious pressure, tourism connections, World Congress trade embargo
  enforcement, trade-route quests and every civilization/policy interaction that
  depends on native route objects are not reproduced. Native gold/science quote
  functions preserve many baseline bonuses but cannot provide complete parity.
- Recall returns a trade unit immediately to the origin, or its capital if the
  origin was lost. This is an initial balance rule, not a simulated return trip.
- AI planning, native event ordering, tech-tree placement, UI layout, turn time,
  and economic balance have not been tested inside the game. Automated tests use
  real Lua 5.1 with mocked engine boundaries. Publication remains deferred.
- No migration from old alpha/native-route saves; no multiplayer or overhaul
  compatibility is claimed. English UI text only.

These limits must accompany the Workshop listing. This is an implementation of
the requested logistics rules, not a claim of full replacement of every BNW
trade-related subsystem.

## Source evidence

The stock [trade engine](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvTradeClasses.cpp)
owns route creation, paths and movement. Its
[Lua player bindings](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp)
expose quotes and summaries, not the mutation controls needed by these rules.
The installed Mac game binary was inspected read-only for matching event/API
names. No executable or game installation files were modified.
