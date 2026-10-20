# Shared static Civilization V GR2 tools

Experimental converter infrastructure for **all repository mods**, maintained in
`tools/`. Outposts is the first consumer, not the owner of the serializer. The Ancient
outpost has rendered beside a stock Fort in native macOS Civ V. All 24 Outpost
variants convert and pass independent reads; their complete visual acceptance and
mod integration remain separate checks. Animated models are outside scope.

Python 3.10+ runs directly on Apple Silicon; the converter has no third-party
Python dependencies. Optional reference inspection needs Apple Command Line Tools
(`clang`) and the pinned open-source Oodle1 codec. No Windows runtime, Wine,
Nexus Buddy, proprietary DLL or SDK is loaded.

```sh
python3 -m tools.civ5_gr2 --help
python3 -m unittest discover -s tests -p 'test_civ5_gr2*.py'
python3 tools/civ5_gr2/setup_research.py
```

The setup script fetches the four exact revisions in `setup_research.py` to
ignored `output/gr2-research/upstream/`, verifies clean checkouts, and compiles an
arm64 codec and independent OpenGR2 probe. `--offline` reuses those pinned trees.
These dependencies are for research/independent verification, not conversion.
The unmodified upstream code emits two compiler warnings in unused big-endian
handling. Only little-endian 32-bit files are supported here.

To inspect locally owned references:

```sh
python3 -m tools.civ5_gr2 extract-fort '/path/to/Resource/Common/ImprovementModels.fpk'
python3 -m tools.civ5_gr2 inspect shared/references/local/fort/fort_mid.gr2 \
  --strings shared/references/local/fort/improvementmodels_stringdatabase.gsd \
  --codec output/gr2-research/libopengrn-codec.dylib \
  --json output/gr2-research/fort-mid-inspection.json
```

Extracts, decoded graphs and rewritten stock files must remain in ignored local
caches. Do not package or commit them. The optional upstream decompressor and
independent probe are for trusted local files; they are not hardened for arbitrary
hostile input. The Python uncompressed reader checks CRC, section bounds,
relocations, type records, strings and allocation limits.

See [research findings](RESEARCH.md) and [dependency notices](NOTICE).

## Convert a static model

```sh
python3 -m tools.civ5_gr2 convert \
  output/models/outpost-eras-v1/RO_Ancient/RO_Ancient.br2 \
  --diffuse output/models/outpost-eras-v1/RO_Ancient/RO_Ancient_diffuse.dds \
  --sref output/models/outpost-eras-v1/RO_Era_BlackSpec.dds \
  --output output/gr2-converted/ancient-candidate \
  --probe output/gr2-research/independent-probe
```

Omit `--probe` for dependency-free conversion. The output contains GR2, FXSXML,
unchanged input DDS files and a conversion JSON with input/output SHA-256s,
vertex/index counts and CRCs, profile identity and separate validation statuses.
Output is deterministic. Matching files allow an idempotent retry; conflicting
files fail before any writes. Use a new directory when changing parameters.

The `civ5-building-static-v1` experimental profile supports one identity root bone,
full root weights, 1–128 meshes, up to 65,536 vertices per mesh, triangle indices,
unit normals/tangents/binormals and two explicit DDS textures. Every mesh uses the
same BuildingShader material. Inputs needing several materials, nonidentity rigs,
skeletal animation or blend weights need another profile; they must not be treated
as supported static exports. BR2 vertices require all 22 fields, including tangent
and binormal. DDS support is DXT1/3/5 or 32-bit RGB(A), without cubemaps/volumes.

Conversion preserves positions, normals, tangent frame, UVs and triangle winding
at float32 precision. There is no UV flip, mesh optimization, geometry scaling or
redesign. The absent third UV component is zero; full root weights become rigid
bone bindings. `--units-per-meter` sets ArtTool metadata, not landmark display
scale. `--name` selects the model and output basename; use a unique mod prefix to
avoid Civ V's case-insensitive VFS collisions.

`--sref` is mandatory: a generic black specular map is a **candidate**, not verified
BuildingSREF semantics. The flat-normal export is not used by this measured shader
profile. Uncompressed GR2 loading and visible Ancient rendering have passed a native
probe. Detailed material appearance, UV orientation, scale, shadows and fog remain
visual-acceptance checks. The converter always marks native game
status `unverified`; structural checks and OpenGR2 reads cannot promote it.

## Verify and batch

```sh
python3 -m tools.civ5_gr2 verify \
  output/gr2-converted/ancient-candidate/RO_Ancient.conversion.json \
  --source output/models/outpost-eras-v1/RO_Ancient/RO_Ancient.br2

python3 -m tools.civ5_gr2 batch \
  tools/civ5_gr2/manifests/resource-outposts-v1.json \
  --output output/gr2-converted/outposts-candidates \
  --probe output/gr2-research/independent-probe
```

Batch output uses the profile demonstrated by the native Ancient probe. Only that
candidate has native rendering evidence so far; each consumer must review its
remaining variants and production integration.
The supplied manifest pins all 24 approved era/state BR2s and their DDS files.
Each asset has `name`, `source`, `diffuse`, `sref` and optional `units_per_meter`.
Each input is an object with `path` (relative to the manifest) and `sha256`.
Other mods can author their own manifests using the same CLI and profile.
All pins and case-insensitive VFS collisions are checked first. Conversion and
verification happen in a temporary directory; the batch appears only once every
asset succeeds. The destination must be new. Shared identical texture names are
allowed; same-name textures with different bytes are rejected.

`verify` checks all bundle hashes, FXSXML references, texture payloads and decoded
geometry/rig against the supplied source. It does not trust a native success
claim in an edited JSON file. Preserve native observations separately, tied to
the exact GR2 hash and installed game identity.

## Native renderer fixture

```sh
python3 -m tools.civ5_gr2 harness \
  output/gr2-converted/ancient-candidate/RO_Ancient.conversion.json \
  --source output/models/outpost-eras-v1/RO_Ancient/RO_Ancient.br2 \
  --output output/gr2-research/render-fixture --scale 6
```

This generates a disposable test mod and complete ModBuddy tree using
`tools/build.py`'s manifest functions. It is not registered as another release.
It has no Terrain/Outposts dependencies and no automatic installer. Only its
dedicated map on elapsed turn zero places the candidate at `(8,8)`, a stock Fort
at `(10,8)` and a scout to make them visible. Ordinary maps and later saves are
left alone. There are no automated turns, saves or production gameplay hooks.
All three test landmark states intentionally use the **same** candidate to avoid
confusing this rendering probe with the 24-state integration.

WSDLC can package it for the macOS game's normal single-player menu:

```sh
python3 output/gr2-research/upstream/wsdlc/civ5_dlc_packer.py \
  output/gr2-research/render-fixture output/gr2-research/render-dlc \
  --game-assets '/path/to/Civilization V.app/Contents/Assets/Assets' \
  --base-db '/path/to/Civ V user data/cache/Civ5DebugDatabase.db'
```

Keep WSDLC output ignored and local: its generated UI hook includes a copy of
owned stock `InGame.lua`. For unattended **background** testing, use the optional
harness from AngelaDMerkel/Lekmod. Inspect its license before reuse: it permits
personal noncommercial use but restricts redistribution. No Lekmod source is
vendored or required by the converter.

```sh
python3 tools/civ5_gr2/setup_research.py --background-harness
python3 -m tools.civ5_gr2.background_test \
  --dlc output/gr2-research/render-dlc \
  --output output/gr2-research/native-run-001 \
  --activation-only --timeout 600
```

Steam must already be signed in and Civ V closed. This runner uses the pinned
harness's process-only background guard, startup/load Lua templates and PID-only
capture helpers with the installed GameCore. It temporarily installs only the
unique CG2 DLC, a map and startup hooks; bypasses the legal screen for this launch;
starts a fresh two-player Ancient scene; and advances no turns. It snapshots and
restores settings, UI, caches, logs and saves, preserves test logs/autosaves in the
evidence directory, and verifies original hashes. `--activation-only` disables
upstream diagnostic interposers while retaining the background activation guard.
Without it, diagnostic logging is more immediate but adds interposers to the
process. Neither mode modifies game executable or GameCore bytes.

For an authorized mouse/keyboard UI test, `--foreground-ui` explicitly permits
the disposable game window to activate; background protection remains the
default. `--window-size 1024 768` requests a temporary window through the backed-up
graphics INI. Record the actual native viewport and screenshot dimensions because
macOS display scaling can differ from that request. The runner restores the
original graphics settings. UI fixtures can wait for actual input without a
scene-ready marker, within the existing timeout; normal restoration still runs
on completion, error or interruption.

The run is bounded to 60–1200 seconds and always restores after normal completion,
errors or interruption. After an abnormal supervisor termination, close only the
owned game process and recover with:

```sh
python3 -m tools.civ5_gr2.background_test \
  --output output/gr2-research/native-run-001 --restore
```

Recovery refuses changed binaries, hooks, payloads or backup files; inspect the
journal instead of overriding that refusal. Evidence contains owned game UI and
must remain ignored/local. Use a fresh evidence directory for every run.

All native test runners across this user's worktrees should hold
`tools.civ5_test_lock.native_test_lock(owner, evidence)` before preparation and
through restoration. It uses a nonblocking `flock` lease at
`/private/tmp/civ5-native-test-<uid>.lock`; its JSON identifies the supervisor and
evidence location. A lock file's existence alone does not mean it is held. Also
check for an existing Civ V process and unresolved recovery journals. Coordinate
with other chats before changing installed DLC/GameCore or claiming the test slot.

Record the game executable/GameCore and GR2 hashes, native logs when available,
a screenshot showing both models, the landmark scale, UV/texture orientation,
normal lighting, shadows, fog behavior and visible defects. A `[CG2] scene-ready`
log establishes placement only. Startup, database load, structural validation and
actual correct rendering are separate outcomes. Scale 6 is an initial measurement
candidate; it is not approved mod display scale. Full 24-state/era integration
and native visual acceptance remain with each mod owner after the profile works.
