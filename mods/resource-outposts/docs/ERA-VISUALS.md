# Claimant-era outpost selection

Status, 9 October 2026: **item 2 implemented and automatically tested**. The user
has now authorized native conversion, visual checks and integration. All 24
states convert and independently verify; the native review fixtures are ready.
See [the current integration review](NATIVE-ART-REVIEW.md) for evidence and status.
The eight approved mesh designs and selected B icons are unchanged. The playable
package still displays stock Fort placeholders; eight different runtime stage
IDs do not yet mean eight different installed meshes.

## Runtime behavior

`src/Lua/RO_Eras.lua` reads `Players[claimant]:GetCurrentEra()` and chooses one of
the eight mappings in `src/SQL/RO_Eras.sql`. Neutral sites use the saved claimant;
annexed sites use the territorial owner. Human and AI sites follow the same rule.
The active player and world art era never choose another civilization's stage.
Additional eras retain the latest supported stage not after the current era ID.
Missing, dead and barbarian claimants do not trigger an art swap.

Completion, capture, city/border changes, technology, load completion and game-data
dirty events reconcile the stage. An unconditional turn check also covers unseen
sites and missed earlier hints. Capture selects the recipient's stage even when
that moves backwards. A repeated callback with the same stage does no native swap.
The engine retains its ordinary fog-of-war visibility rules; this code does not
reveal plots or force opponents' remembered art to refresh.

Construction retains `BUILD_RT_RESOURCE_OUTPOST` and its original native work
progress. An era change never replaces an in-progress build. On completion, the
site receives its claimant's current stage. The under-construction placeholder
continues to use the public improvement's stock art behavior. A future requirement
for claimant-specific construction scaffolding needs a separate implementation.

`RO_Outposts.IsOutpost(plot)` recognizes the canonical improvement and all eight
internal variants. Claims, resource notifications, AI repair/guard/capture jobs,
management, conversion and the existing shelter bridge all use that family.
There is no new road, supply or companion-mod dependency.

## Gameplay and native setter safeguards

Each internal improvement copies every stock BNW improvement property, resource
trade row and valid feature from `IMPROVEMENT_RT_RESOURCE_OUTPOST`. Only its type,
art definition and `GraphicalOnly` flag differ. Hidden variants have no build
actions and do not duplicate Civilopedia entries. All share the approved B icons.
Ordinary Fort definitions are untouched.

`CvPlot::setImprovementType` clears pillage and upgrade progress, adds the new
resource connection, then removes the old connection and city resource link.
The visual swap runs inside the ledger's reconciliation guard. It restores
upgrade progress and pillage; an intact owned site receives a balanced native
pillage/repair pair to reconnect the city resource link. The engine handles its
own quantity modifiers. No adjustment is inferred from aggregate player totals.
The code does not set plot ownership, resources, features, routes or unit state.

Passing `NO_PLAYER` to the native setter avoids assigning a new engine gift flag
on neutral sites. Claim ownership stays in the existing Lua ledger. An old save
can contain an already-annexed canonical outpost with an unreadable gift flag.
Its first visual migration waits until the territorial owner can see and trade
the resource; otherwise native removal could subtract an uncredited resource.
The site continues normal gameplay while waiting. Newly completed neutral sites
are normalized immediately, so their later variant swaps need no such delay.

Sources: Firaxis BNW mirrors for
[plot setters and resource links](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/CvPlot.cpp),
[plot Lua bindings](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaPlot.cpp)
and [player era access](https://github.com/Gedemon/Civ5-DLL/blob/master/CvGameCoreDLL_Expansion2/Lua/CvLuaPlayer.cpp).
These behaviors are modeled in the regression suite; native execution is still
unverified.

## Save and integration compatibility

The public `RT_` improvement/build IDs, package UUID/version, localization keys,
`RO_Outposts` interfaces and `ResourceOutposts.v1.State` save key remain. Existing
standalone claim records reconcile in place without receiving their resources or
maintenance a second time. A persisted variant is corrected if its claimant's era
changed before saving. Converted or removed sites are never recreated.

The release still requests a new game; this is not a claim that changing mod files
mid-campaign is officially supported. Saves from Terrain's older bundled outpost
alpha remain outside this migration. Loading a save containing the new internal
IDs with an older package that lacks them is not supported.

Shared tooling handoff: `tools/packages.py` loads `RO_Eras.sql` after `RO_Art.sql`.
`tools/validate.py` validates all eight stages, full stock property equivalence,
side-table equivalence, hidden entries, a single public action and 24 art states
against installed BNW data, alone and with Terrain in either load order.
No Terrain source or bridge change is needed.

## Native mesh integration handoff

`RO_OutpostEras` is the authoritative binding table. Internal improvement and art
names end in the corresponding engine era suffix. Atomic is `POSTMODERN` and
Information is `FUTURE`; do not substitute non-existent `ERA_ATOMIC` identifiers.

| Engine era | Approved model stem | Current Fort fallback |
| --- | --- | --- |
| `ERA_ANCIENT` | `RO_Ancient` | Ancient |
| `ERA_CLASSICAL` | `RO_Classical` | Ancient |
| `ERA_MEDIEVAL` | `RO_Medieval` | Ancient |
| `ERA_RENAISSANCE` | `RO_Renaissance` | Ancient |
| `ERA_INDUSTRIAL` | `RO_Industrial` | Industrial |
| `ERA_MODERN` | `RO_Modern` | Industrial |
| `ERA_POSTMODERN` | `RO_Atomic` | Industrial |
| `ERA_FUTURE` | `RO_Information` | Industrial |

Each art definition has `Constructed`, `UnderConstruction` and `Pillaged` rows
with `Era='Any'`. Keep that fixed selector: Lua already chooses the era, including
on unowned land. Replace the placeholder model/scale/shader bindings only after
native conversion and validation of the approved sources. The construction row
is prepared for later work but is not selected by a new era-specific build action.
Update the placeholder-specific validator assertions when genuine native assets
are integrated, retaining gameplay equivalence and unchanged native Fort checks.

## Verification and remaining native checks

Completed: full Lua 5.1 suite, including **382 Outpost assertions**; package build
and source/ZIP/hash parity; **six package unit tests**; installed BNW database
checks for each package alone and both SQL load orders. The gameplay suite uses
the existing environment with `lupa==2.8`. No in-game test or native mesh rendering
has been performed for this change.

Remaining native acceptance:

- Advance all eight eras on neutral and annexed sites, with the active player in
  a different era. Check AI sites, unseen sites and normal fog-of-war behavior.
- Capture into earlier and later eras; capture a ruin before extraction technology;
  annex through culture, purchase, founding and city capture, then save/reload.
- Verify exact resources, happiness, city resource links, upkeep, pillage, repair,
  ongoing build progress and garrison position/HP/movement across transitions.
- Check old canonical sites, including annexed sites waiting for resource tech.
- Inspect the one Civilopedia entry, normal worker action, strategic icons and AI
  repair/guard reservations. Repeat with Terrain enabled for roadless shelter.
- After conversion, inspect all approved meshes, scale, shaders and state visuals.
