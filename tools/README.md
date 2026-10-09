# Shared support tools

Run commands from the repository root. This directory is separate from all mod
runtime source; model builders/viewers are support tools even when they serve
one mod. Do not move them into a playable package.

| Task | Builder/exporter | Validation | Output |
| --- | --- | --- | --- |
| Current playable releases | `python3 tools/build.py` | `python3 tools/validate.py` | Complete projects in `build/`, packages in `dist/` |
| Gameplay tests | — | `.venv/bin/python tools/test.py` | Lua 5.1 assertions against production files |
| Selected Terrain 2D art | `tools/export_art.py` | Decodes exports; package validator checks bindings | `mods/realistic-terrain/src/Art/` |
| Historical first mesh pass | `tools/build_models.py` | `tools/validate_models.py` | `output/models/first-pass/` |
| Approved Terrain source models | `tools/build_models_v2.py` | `tools/validate_models_v2.py` | `output/models/revised-v2/` |
| Terrain comparison sheets | `tools/review_models_v2.py` | Checks original art hashes | `output/model-review/approved-art-alignment/` |
| Approved Outpost era models | `tools/build_outpost_era_models.py` | `tools/validate_outpost_era_models.py` | `output/models/outpost-eras-v1/` |
| Irrigation mesh kit v1 | `tools/build_irrigation_meshes.py` | `tools/validate_irrigation_meshes.py` | `output/models/irrigated-farm-v1/` |
| Irrigation mesh refinement v2 | `tools/irrigation_v2/build_irrigation_meshes.py` | `tools/irrigation_v2/validate_irrigation_meshes.py` | `output/models/irrigated-farm-v2/` |

Python files in this table are run with the Python interpreter for the appropriate
environment. Packaging/validation use the standard library. Gameplay tests need
`tests/requirements.txt`; mesh generation and art comparisons need
`tools/requirements-art.txt`. Module files such as `model_*`, `outpost_*` and
`irrigation_mesh_io.py` support those entry points. The `irrigation_v2/refine_*`
modules are part of its active refinement pipeline; see its mesh notes before use.

Selected source art is under `shared/art/`. Review tools may additionally require
ignored, locally supplied stock references; consult `shared/references/README.md`.
Ordinary package builds use versioned DDS assets and do not need those references.
Model/source ZIPs are authoring bundles, not installable Civ V mods.
