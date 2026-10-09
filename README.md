# Civilization V mod projects

Four projects for Civilization V: Brave New World share this repository. Start
with [AGENTS.md](AGENTS.md) and the [development guide](docs/DEVELOPMENT.md).

| Project | Directory | Current state |
| --- | --- | --- |
| Realistic Terrain | [mods/realistic-terrain](mods/realistic-terrain/README.md) | Exposure, Caravansaries and replacement trade; v2 alpha |
| Resource Outposts | [mods/resource-outposts](mods/resource-outposts/README.md) | Independent outpost package; v1 alpha |
| Irrigated Farm | [mods/irrigated-farm](mods/irrigated-farm/README.md) | Own gameplay source and art work; currently packaged inside Terrain v2 |
| Climate Change | [mods/climate-change](mods/climate-change/README.md) | Requirements and research; no playable package yet |

```text
mods/          Per-mod source, documentation, tests and agent instructions
tools/         Shared packaging, mesh builders, exporters and validators
shared/        Common requirements, reference indexes and approved art sources
docs/          Repository workflow, current gameplay guide, testing and release notes
tests/         Shared Python test dependency and repository checks
build/         Generated complete ModBuddy projects (ignored)
dist/          Generated installable folders and ZIPs (ignored)
output/        Local mesh exports, previews and research caches (ignored)
```

Build and validate the two current releases using Python's standard library:

```sh
python3 tools/build.py
python3 tools/validate.py
```

Run the existing gameplay tests in Lua 5.1:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python tools/test.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

The build combines Terrain and Irrigated Farm source without duplicating it.
It preserves existing package UUIDs, versions, filenames, database actions and
save keys. Splitting irrigation into its own playable mod remains a separate
implementation task. ModBuddy projects are generated under `build/`; edit the
authoritative files under `mods/*/src/`.

See the [current gameplay and installation guide](docs/GAMEPLAY.md),
[shared requirements and references](shared/README.md),
[tool catalog](tools/README.md), [native testing checklist](docs/TESTING.md), and
[Workshop preparation](docs/WORKSHOP.md). Automated checks do not establish native
UI rendering, model conversion or in-game behavior; those checks remain pending.

The configured GitHub remote is [Civ5-Mods](https://github.com/AngelaDMerkel/Civ5-Mods).
Use semantic commits as work progresses, with per-mod branches in separate
worktrees; the [development guide](docs/DEVELOPMENT.md) describes the transition
from the currently shared checkout.
