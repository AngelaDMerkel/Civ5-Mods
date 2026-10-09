# Development and coordination

## Canonical ownership

| Existing chat | Working directory | Scope |
| --- | --- | --- |
| Terrain Mod | `mods/realistic-terrain/` | Exposure, supply, Caravansaries, Ministry, trade and current combined UI |
| Resource Outpost | `mods/resource-outposts/` | Claims, upkeep, garrisons, management UI and outpost AI |
| Irrigated Farm | `mods/irrigated-farm/` | Water connectivity, farms, irrigation AI and terrain-compatible agricultural art |
| Climate Change Mod | `mods/climate-change/` | Climate requirements, experiments and future implementation |

Each mod keeps `src/`, `docs/`, `tests/`, a README and local agent instructions.
Empty climate/irrigation directories are intentional scaffolding, not evidence of
a completed implementation. Builders, review viewers and exporters live in
`tools/`; common requirements and reference material live in `shared/`.

## Working together

Use one writer per shared file. Inspect the latest state before editing package
composition, common requirements or a companion's integration hooks. Coordinate
only the overlap; continue independent work. Direct user authorization is needed
to message another chat. The user authorized migration notifications to the four
chats on 2026-10-09; this is not standing authorization for unrelated messaging.

Keep a handoff in the owning mod's docs when work crosses a boundary: purpose,
affected paths, interface/identifier changes, tests run, and the next owner/action.
Use a dedicated branch/worktree for future concurrent work on the same files.
Do not switch branches or broadly stage/reset files in a shared checkout.

## Commit cadence and format

The user requires semantic commits as work is done across all repositories.
Commit each coherent unit after its relevant checks pass: a bug fix with its
regression coverage, one feature increment, or a focused documentation update.
For longer tasks, use working milestones instead of waiting for the entire feature
to finish. Avoid empty checkpoints and unrelated changes in the same commit.

Use Conventional Commits with an imperative summary:

```text
feat(irrigation): add connected terrace eligibility
fix(outposts): prevent duplicate resource grants after reload
test(terrain): cover interrupted supply routes
docs(climate): record tile refresh experiment results
build(tools): validate assembled package sources
chore(repo): define semantic commits and mod branches
```

These are examples, not statements that those features are implemented. Supported
types are `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`, `perf`, `style`
and `chore`; use a meaningful mod or shared-area scope. Explain a real breaking
change with `!` and a `BREAKING CHANGE:` body/footer. Include useful test evidence
in the body. Preserve the two initial commits and any published history.

Review `git status` and the staged diff immediately before committing. Stage only
owned paths/hunks. A shared checkout has one index: do not include or unstage
another chat's staged work. Local incremental commits are expected without a new
confirmation each time; this does not imply publishing or merging permission.

## Per-mod branches and worktrees

| Mod | Reserved development branch |
| --- | --- |
| Realistic Terrain | `mod/realistic-terrain` |
| Resource Outposts | `mod/resource-outposts` |
| Irrigated Farm | `mod/irrigated-farm` |
| Climate Change | `mod/climate-change` |

`main` is the integration branch. Shared tooling/rules can use focused topic
branches when concurrent work warrants it. Each mod branch needs a separate
worktree, with its chat actually operating in that worktree. Every branch contains
the full repository, so builds can test all consumers; branch names do not change
directory ownership or create separate repositories.

The mod branch references are prepared at the workflow-policy commit. Active chats
still share the original `main` checkout; they have not been moved automatically.
At a safe checkpoint, each owner commits its own current changes, then continues
in a dedicated worktree based on current integrated history. Carry over only the
necessary commits and verify they are present before editing. Avoid reapplying a
commit that is already in the target branch. Do not copy another chat's dirty
working tree, switch the shared checkout, or force-reset an existing branch.

Bring shared changes from `main` into the mod branch before relying on them. Run
the affected tests before integration, preserve semantic commits when merging,
and resolve shared-file conflicts with the relevant owner. Keep mod branches
current rather than allowing four separate versions of the common tools to drift.

## Source composition and current coupling

`tools/packages.py` registers only two releases:

| Package | Source roots | Generated ModBuddy project |
| --- | --- | --- |
| Realistic Terrain v2 | `mods/realistic-terrain/src/` + `mods/irrigated-farm/src/` | `build/realistic-terrain/Realistic Terrain.civ5proj` |
| Resource Outposts v1 | `mods/resource-outposts/src/` | `build/resource-outposts/Resource Outposts.civ5proj` |

The builder rejects duplicate package paths and VFS names within a package.
The validator checks both releases for VFS/localization collisions, manifests,
source/staging/archive parity and, with a cache argument, both database load orders.
`dist/` keeps the same package names and versions as before the directory migration.

Irrigation's dedicated Lua/SQL source and tests have moved to its own project.
The combined `RT_Environment` UI, `RT_Construction*` worker orders and irrigation
localization are still in Terrain. These are shared integration points under the
Terrain owner's care. A standalone irrigation release still needs its own startup,
UI, text/configuration and worker-order integration, a deliberate package identity,
and tests for each enabled-mod combination. Preserve the current runtime behavior
until that work is explicitly undertaken. Do not duplicate the existing feature.

Climate Change has no source implementation or release UUID yet. Its requirements
must be resolved and native tile-refresh experiments completed before a release
can be claimed.

## Migration map — 2026-10-09

| Previous path | Authoritative path |
| --- | --- |
| `mod/` | `mods/realistic-terrain/src/` except the irrigation files below |
| `mod/Lua/RT_Irrigation*.lua` | `mods/irrigated-farm/src/Lua/` |
| `mod/SQL/RT_Irrigation.sql` | `mods/irrigated-farm/src/SQL/RT_Irrigation.sql` |
| `outposts/` | `mods/resource-outposts/src/` |
| `tests/test_*.lua` | Owning `mods/<name>/tests/` |
| `docs/IRRIGATION.md`, `OUTPOSTS.md`, `TRADE.md` | Owning `mods/<name>/docs/` |
| Detailed root README | `docs/GAMEPLAY.md` |
| `docs/art/` | `shared/art/` |
| Selected Terrain 2D source files under `output/art-concepts/.../round-3/` | `shared/art/terrain-icons-round-3/` |
| Approved irrigation v6 concept and prompts under `output/art-concepts/` | `shared/art/irrigated-farm/` |
| Source `.modinfo` / `.civ5proj` | Generated `build/<package>/` |

`tools/` and `output/` paths remain stable for active mesh work. Old local concept
copies are caches; tools exporting approved Terrain art read `shared/art/`.
The selected originals, prompts and approval records are versioned. Rebuildable
ZIPs, meshes and review renders are ignored. The original pre-migration layout is
recoverable from the first local Git commit.

Migration verification: all 49 runtime source/assets and the four generated
manifest/project files matched their pre-move bytes. The existing Lua suite,
package checks and installed BNW database checks passed (each release alone and
both SQL load orders). Terrain's nine model variants and Outposts' 24 era/state
exports passed their existing validators. The Outpost source archive's approval
locator and integration note were updated without changing its models. Active
irrigation mesh refinement was kept outside the migration's edits and commit.

## Shared dependencies and release evidence

Packaging uses Python's standard library. Lua tests use `lupa==2.8` from
`tests/requirements.txt`. Art tooling uses NumPy and Pillow; its dependency file
is `tools/requirements-art.txt`. Install dependencies into a virtual environment.

Keep evidence specific: automated logic/data checks, visual design approval,
native GR2 conversion, and actual game testing have different acceptance criteria.
`docs/TESTING.md` and each mod's docs list remaining manual checks. Packaging does
not install a mod into the game or publish it to Workshop.
