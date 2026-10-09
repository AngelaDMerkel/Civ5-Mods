# Native farm sources (local extraction only)

Source: the user's installed macOS Civilization V / Brave New World Assets.
Read on 2026-10-09. No game art is versioned or included in playable packages.

| Archive | Relevant assets |
| --- | --- |
| `Resource/Common/ImprovementModels.fpk` | Medieval/Modern Farm GR2, FXSXML and `improvementmodels_stringdatabase.gsd` |
| `Resource/Common/ConquestDeluxeModels.fpk` | Constructed/HB/PL Incan Terrace Farm GR2/FXSXML and `conquestdeluxemodels_stringdatabase.gsd` |
| `Resource/DX9/ImprovementTextures.fpk` | Native farm prop and decal maps |
| `Resource/DX9/ConquestDeluxeTextures.fpk` | Native Incan Terrace diffuse maps |
| `Resource/Common/MiscData.fpk` | `farm_types.xml`, regional crop-decal declarations |
| `Resource/DX9/DecalTextures.fpk` | `crops_africa_01_d.dds` through `crops_africa_08_d.dds`, other regional crop families |

Reproduce with `tools/irrigation_native/import_native_farms.py`. The ignored
output manifest records exact archive entry names, byte sizes and SHA-256 hashes.
GLB/GR2 comparison uses decoded geometry, not screenshots or generated studies.
The three terrace states have native source geometry; ordinary Farm field
placement remains an engine-controlled system requiring separate investigation.

Decoder provenance: [OpenGr2](https://github.com/arves100/opengr2), pinned to
`4e5edd5e98dbd69270d40a92ed94cfe16e57955a`, MPL-2.0. The release-only debug-header
adjustment is documented beside the source. Our experimental uncompressed writer
is independent project code; its round-trip checks do not establish game support.
