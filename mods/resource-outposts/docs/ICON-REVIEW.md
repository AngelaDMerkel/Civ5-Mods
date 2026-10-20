# Resource Outposts icon review — 2026-10-09

Status: **B selected for both assets, exported and integrated**. Native rendering
is still unverified. The user selected the Guarded storehouse on 9 October 2026:

> Resource Outposts icon selection: main emblem B; construction glyph B. Reuse
> the selected emblem for management and strategic view.

The review followed Terrain's process: multiple alternatives beside actual Civ V
references, followed by a recorded user selection. The authoritative originals,
prompts, exact approval and hashes are in `shared/art/resource-outpost-icons-v1/`.

## Scope

“Game-wide” is being applied to Resource Outposts wherever it appears in the game.
One consistent identity is selected across all eight eras; the approved models
still change by era. This UI choice does not change the model approvals.

| Surface | Required art / treatment | Current implementation |
| --- | --- | --- |
| Civilopedia improvement entry and improvement portraits | B emblem; portrait atlas sizes 32, 45, 64, 80, 128, 214, 256 | `RO_OUTPOST_PORTRAITS`, index 0 |
| Construction action and its tooltip | B glyph, 32, 45, 64; localized build/help text remains | `RO_OUTPOST_ACTION`, index 0; custom button uses 32 px DDS |
| Management opener, overview and selected-site panel | B emblem at 32/45 px alongside labels | Static images in `RO_UI.xml`, including each overview row |
| Strategic map improvement marker | B emblem in a 256 px DDS with native-style padding | `ART_DEF_IMPROVEMENT_RO_RESOURCE_OUTPOST`; native rendering pending |
| Site state and destructive actions | Reuse native warning/action symbols with explicit localized text; identify the site with its emblem | Localized text and confirmation flows already present |
| Notifications | Reuse outpost identity if an additive notification UI is implemented; native generic notification symbol otherwise | Uses `NOTIFICATION_GENERIC`; changing the portrait atlas alone will not change this icon |
| Resource, gold, defender and shelter information | Existing native symbols, plus localized values/reasons | No new resource type, technology or city building is introduced |

Two original emblem concepts and their corresponding worker glyphs were reviewed:

- **A — Watchtower cache:** an open roofed watch platform, low enclosure and one
  prominent cargo crate.
- **B — Guarded storehouse (selected):** a low storehouse, short lookout turret and cargo
  crate, with an asymmetrical fortified silhouette.

The cargo crate denotes generic resources. No road, supply-link, caravan or
resource-specific extraction tool belongs in these symbols. Optional Terrain
integration remains shelter only, without a road requirement.

## Review and handoff

Review folder: `output/art-concepts/2026-10-09/resource-outposts-round-1/`.
Generation uses the built-in image tool. `prompts.json` records exact prompts and
reference roles. Original candidates remain unmodified in that local review
folder; the gallery uses CSS sizing to compare their silhouettes with native
assets. Local game references are excluded from Git and playable packages.

Open `index.html` through a local server for the comparison gallery. Each family
includes `identity-<a|b>.png` and `worker-<a|b>.png`. `asset-manifest.json` records
the four 1254×1254 RGBA original files, hashes and reference provenance. Alpha is
present in all four files. Preview scaling uses alpha >= 8 bounds to ignore faint
outer specks when centering; it does not change the pixels or clean their edges.
Final exports remove alpha below 8, apply the same reviewed crops, resize
proportionally and add native cell padding. Visible source pixels are preserved;
no art was regenerated. Small exported glyph edges still require native visual
acceptance. The first parallel
worker-generation calls failed with connection errors; sequential retries
succeeded with the same recorded prompts.

Review checks: browser inspection of both candidate families beside native art;
32/45/64 px previews; worker transparency on light and dark grounds; working
selection summary reset to no selection after testing. Screenshots are saved as
`review-emblems.png` and `review-workers.png`. No in-game acceptance is claimed.

## Export and integration

`tools/export_outpost_icons.py` verifies both approved source hashes and exports
eleven lossless legacy RGBA DDS files into this mod's `src/Art/`. Every DDS was
decoded and compared byte-for-byte with its export pixels. Actual DDS readback
PNGs are in the review folder's `exported/` directory. The originals remain
unchanged, and no native reference pixels enter the release.

`src/SQL/RO_Art.sql` binds both atlases and creates the outpost-specific strategic
mapping. The initial icon integration copied the native Fort landmark model rows
as a fallback; the approved native era models have since replaced those rows.
Native Fort records are unchanged. Five additive image controls cover construction,
the management opener, overview title/rows and selected-site title.

Shared tooling handoff: `tools/packages.py` loads the new SQL after the improvement
definitions and opts Outposts into strategic reload. `tools/build.py` reads this
optional package setting, leaving Terrain unchanged. `tools/validate.py` checks
the atlas files, UI references, approved hashes, strategic definition, complete
era model rows and preservation of all original Fort records. No gameplay API,
save identifier, localization tag or package version changed.

Checks completed: package build and source/ZIP parity; eleven lossless DDS
readbacks; installed BNW database validation for each mod alone and both SQL load
orders; all Lua 5.1 tests (including 275 Outpost assertions); six package tests.
The Lua suite used `/private/tmp/realistic-terrain-test-env/bin/python`, the existing
local environment with `lupa`, because this checkout has no `.venv`.

Native gameplay screenshots on 20 October 2026 show the selected B emblem in the
management opener and selected-site header with Terrain enabled. This is partial
visual evidence, not full icon/UI acceptance; see
[NATIVE-GAMEPLAY-TESTS.md](NATIVE-GAMEPLAY-TESTS.md).

Remaining native checks: icon sizing/alpha across all controls, disabled/cancel
state, tooltips, Civilopedia portraits, strategic markers, and panel
overlap at 1024×768 and widescreen with Terrain absent/present. Notifications keep
the native generic symbol. Claimant-era switching is now implemented separately
in [ERA-VISUALS.md](ERA-VISUALS.md); all eight internal variants reuse the selected
B portrait and strategic emblem. Native era-model conversion and focused visual
checks are recorded in [NATIVE-ART-REVIEW.md](NATIVE-ART-REVIEW.md).
