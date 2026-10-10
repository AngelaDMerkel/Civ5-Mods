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


Additional terrain-junction references used by `build_terrain_cases.py`:

| Installed path | Purpose |
| --- | --- |
| `Resource/DX9/TerrainTextures.fpk` | `afri_desert_d.dds`, `afri_grassland_d.dds`, `afri_mountain_base_d.dds`, `river_diffuse.dds` for fixture material comparisons |
| `Resource/DX9/DecalTextures.fpk` | `floodplains_d.dds` for the river-bank vegetation ribbon; original regional crop textures reused |
| `Assets/terrain/pieces/Mountain/Africa/Afri_Mountain_1_1_H.dds` | Native A16B16G16R16 mountain height samples, normalized to an authored 24-unit fixture range |

Exact extracted hashes and origin locators are written to the ignored
`terrain-review/terrain-cases.json`. These are local reference inputs, not assets
for redistribution. The flat crop polygons, river ribbon, supporting hill and
placement/scaling of the mountain are authored fixture geometry. They do not
establish native terrain-compositor or procedural farm-placement behavior.


The installed `Resource/Common/MiscData.fpk:civ5artdefines_landmarks.xml` assigns
resource-free ordinary farms to `LayoutHandler=FARM`, `bTerrainContour=True`, and
era-specific `Medieval_Farm1/2/3.fxsxml` / `Modern_Farm1/2/3.fxsxml`. The unsuffixed
`Medieval_Farm.fxsxml` used by the earlier prop fixture is a constructed wheat
farm reference. `Assets/DLC/DLC_02/Features/Civ5ArtDefines_Landmarks_DLC_02.xml`
assigns Terrace Farm to `SNAPSHOT` with terrain contouring enabled. Reproduce the
read-only definition audit with `tools/irrigation_native/audit_native_layout.py`.
Output remains local. These definitions explain why decoded source meshes and
invented context do not demonstrate the native in-game farm appearance.


Desert provenance clarification: `farm_types.xml` declares regional crop families
(`Crops_Africa`, `Crops_America`, `Crops_Asia`, `Crops_Europe`) and construction,
wheat and damage families. It has no desert crop family. The inspected ordinary
Farm landmark rows likewise have no desert-specific binding. The terrace GR2,
Africa crop reference, desert terrain DDS and wheat-farm prop extract were
compared byte-for-byte with their installed archive entries and match. This
establishes authentic inputs, not that their authored combination reproduces a
standard desert farm. Which crop family the renderer chooses on a particular
desert tile and its actual parcel placement still require native observation.


Regular-farm correction: the importer now reads `medieval_farm1/2/3.gr2` and
`modern_farm1/2/3.gr2` with their original wrappers and visible-state textures.
Each file bundles three native model states. Farm2's constructed model is named
`Med_Farm1`, so state selection must inspect the graph rather than infer the name
from the filename. The ordinary farmstead ground decal is not the surrounding
crop-field texture. Native-derived irrigation candidates preserve that distinction
and retain the `FARM` handler without overriding regional crop assets. Their local
manifest records source and generated candidate hashes; no native pixels or
source-derived meshes are checked into the repository or release packages.
