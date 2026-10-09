# Repository instructions

## Read before working

Read this file and the root `docs/DEVELOPMENT.md`, then the owning mod's
`README.md`, `AGENTS.md` and `docs/DEVELOPMENT.md`. Also read relevant files in
`shared/requirements/`. User instructions take precedence.
Keep established decisions in the repository so another chat can continue without
reconstructing conversation history. Separate confirmed requirements from proposals.

## Ownership and layout

- Terrain Mod owns `mods/realistic-terrain/`.
- Resource Outpost owns `mods/resource-outposts/`.
- Irrigated Farm owns `mods/irrigated-farm/`.
- Climate Change Mod owns `mods/climate-change/`.
- `tools/` is shared support code, including mesh builders and viewers.
- `shared/` holds common requirements, reference indexes, original selected art
  and approval records. Runtime assets belong in their mod's `src/Art/`.
- `docs/` holds repository and release documentation. Per-mod rules/tests belong
  with that mod. Do not recreate the former `mod/`, `outposts/` or `docs/art/` roots.

Four source owners do not yet mean four releases. `tools/packages.py` is the
authoritative package registry. Irrigation currently ships inside Terrain; climate
has no package. Do not invent a release identity or alter gameplay to tidy folders.

## Concurrent work

Check `git status --short` before editing. These chats may share one checkout.
Preserve other work, including changes to generated outputs. Never reset, clean,
stash, revert, or overwrite unrelated changes. Do not change the checkout's branch
while another chat is using it. Prefer a separate worktree for future overlapping
work; keep this shared checkout on its existing branch.

Keep edits within the task's ownership where possible. For a necessary change to
shared tooling or another mod, inspect the latest files, make the smallest change,
test affected consumers, and record the handoff. Use `docs/DEVELOPMENT.md` for the
coordination rules. Do not send messages to other chats without user authorization;
repository handoff notes remain available when messaging is not authorized.

Commit explicit paths belonging to the task. Do not sweep concurrent work into a
commit with `git add .` or `git add -A`. Shared changes need one active editor;
work on independent files while overlapping edits are being coordinated.

## Semantic commits and branches

The user's standing preference across all repositories is to commit work as it
progresses. Make a local commit after each coherent, validated change and before
handing off completed work. Do not accumulate unrelated tasks into one final
commit or leave finished work uncommitted. Read-only work needs no commit.

Use Conventional Commit subjects: `type(scope): concise imperative summary`.
Types include `feat`, `fix`, `refactor`, `docs`, `test`, `build`, `ci`, `perf`,
`style` and `chore`. Scopes here are `terrain`, `outposts`, `irrigation`, `climate`,
`tools`, `shared` or `repo`. Use `!` and a breaking-change explanation only when a
change actually breaks compatibility. Record relevant verification in the body.
Keep existing published history intact; this convention applies going forward.

Inspect the staged diff before committing and include only the current task's
changes. If another chat has staged files, leave its index entries alone and
coordinate the commit; a shared checkout also shares its Git index. Local commits
are part of authorized implementation work. Publishing, merging and deployment
remain separate actions governed by the user's task.

Each mod has a reserved `mod/<directory-name>` branch. Use that branch in its own
worktree for concurrent development; see `docs/DEVELOPMENT.md`. `main` integrates
validated changes to shared code and the mods. Branch references alone do not
move a chat or transfer uncommitted work. Existing chats sharing this checkout
must checkpoint their own work before transitioning; never switch this checkout
under another active chat.

## Implementation boundaries

Target the current single-player BNW Lua 5.1/macOS-compatible baseline. Preserve
existing IDs, localization tags, global names, save keys, package versions and
optional integration behavior unless the task calls for changing them. There is
no custom DLL in the current release.

Keep optional integrations safe when a companion is disabled. Give new files,
globals, events and save keys a unique mod prefix. Existing `RT_` irrigation and
outpost database identifiers are compatibility contracts, not naming mistakes.
Document changes that affect save compatibility or another mod's runtime.

Generate manifests and complete ModBuddy staging trees with `tools/build.py`.
Never hand-edit generated hashes, copy source into a second owner directory, or
include support scripts, reference images, game databases or review galleries in
a playable package. Package sources are restricted to the registered `src/` roots.

## Art, references and UI

Follow `shared/requirements/ART.md` and `shared/requirements/UI.md`.
Preserve approved artwork, selection records and hashes. The user's existing
process for additional icons/artwork is multiple options alongside real Civ V
references, followed by a recorded user selection before integration. Do not
silently replace an approved source or call a changed model approved.

Keep proprietary reference extracts in ignored local caches. Record their origin
and intended use in `shared/references/`; do not distribute those extracts as mod
assets. Mesh design approval, export validation, native conversion and in-game
visual acceptance are distinct states.

## Player documentation

Keep the root and mod READMEs brief and player-facing. Follow
`shared/requirements/DOCUMENTATION.md`. The player entry point is
`docs/GAMEPLAY.md`; detailed mod guides are `mods/<mod>/docs/GUIDE.md`, with
Terrain's trade guide in `docs/TRADE-GUIDE.md` under that mod.

Explain game purpose, requirements, units, buildings, worker actions and results
in Civilization V terms. Update the guides alongside gameplay changes. Label
concept art and model previews, and distinguish current features from planned
ones. Keep development commands, chat ownership, source identifiers, mesh formats
and validation reports in contributor/technical notes, not the player READMEs.

## Validation and completion

- Runtime/source/packaging changes: run `python3 tools/build.py`,
  `python3 tools/validate.py`, and `.venv/bin/python tools/test.py` (or an existing
  environment with `tests/requirements.txt`).
- Packaging changes: also run `python3 -m unittest discover -s tests -p 'test_*.py'`.
- SQL/XML changes: use `tools/validate.py --cache <Civ-V-cache>` when available;
  it reads installed databases and validates copies in memory.
- Mesh/export changes: run the appropriate validator in `tools/README.md` and
  inspect its actual previews. Preserve approval boundaries when outputs change.
- Documentation-only changes: check paths and consistency; avoid unrelated rebuilds.

Report what changed, checks actually run and remaining native tests. Update the
owning mod's documentation when behavior or status changes. Do not describe a
mock test, rendered preview or source mesh as proof of native game behavior.
