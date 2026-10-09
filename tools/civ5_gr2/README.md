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
python3 -m unittest discover -s tests -p 'test_civ5_gr2.py'
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
