# Shared static Civilization V GR2 tools

Experimental converter infrastructure for **all repository mods**, maintained in
`tools/`. Outposts is the first consumer, not the owner of the serializer. Native
Civ V compatibility has not been established. Animated models are outside scope.

Python 3.10+ runs directly on Apple Silicon; the converter has no third-party
Python dependencies. Optional reference inspection needs Apple Command Line Tools
(`clang`) and the pinned open-source Oodle1 codec. No Windows runtime, Wine,
Nexus Buddy, proprietary DLL or SDK is loaded.

```sh
python3 -m tools.civ5_gr2 --help
python3 -m unittest discover -s tests -p 'test_civ5_gr2*.py'
python3 tools/civ5_gr2/setup_research.py
```

The setup script fetches the three exact revisions in `setup_research.py` to
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
profile. Material appearance, UV orientation, scale, shadows, fog and uncompressed
GR2 acceptance remain native-game checks. The converter always marks native game
status `unverified`; structural checks and OpenGR2 reads cannot promote it.
