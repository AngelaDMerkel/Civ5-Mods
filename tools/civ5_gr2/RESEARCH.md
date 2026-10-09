# Native static GR2 investigation — 9 October 2026

## Scope and evidence

This is shared infrastructure for Terrain, Outposts, Irrigation and future
Climate art. Resource Outposts provides the first approved source model, not a
converter-specific package identity. Geometry approval remains unchanged.
The current era-selection handoff is on `mod/resource-outposts` at `6efac5d` in
`mods/resource-outposts/docs/ERA-VISUALS.md`. Older `CONVERSION.txt` claims that era
selection is unfinished are stale. No gameplay changes are required here.

## Dependencies inspected

| Source and pinned revision | License inspected | Finding |
| --- | --- | --- |
| [LSLib](https://github.com/Norbyte/lslib/tree/6f5f6987d10d8485876b8368431c948e4dea4f83) | MIT, `LICENSE` | `GR2/Reader.cs`, `Writer.cs`, `Format.cs` supply a usable serialization reference. Current model classes target Divinity/BG3. Stock Civ V hashes are not resolved; compressed reads call native compressor support. No claim of running LSLib against Fort. |
| [OpenGR2](https://github.com/arves100/opengr2/tree/4e5edd5e98dbd69270d40a92ed94cfe16e57955a) | MPL-2.0, `LICENSE` and source headers | Oodle1 decoding works on the six local Fort sections. Writer is incomplete. Native `gr2nfo` crashes on stock hashed names; on embedded-string rewrites its nonportable `%I64u` printing also crashes on macOS. Our separate probe uses unmodified library loading without that dumper. |
| [Nexus Buddy 2](https://github.com/deliverator23/Nexus-Buddy-2/tree/c42a7f6d1bac7190dec5fd27efe588db91fc24a3) | No license grant found in inspected tree | `BR2Importer.cs` and `Shaders/IndieBuildingShader.cs` inspected only. Depends on Firaxis Granny wrappers, native templates and Windows. No copied code/templates or runtime dependency. |

Decision: implement a small Python standard-library dynamic-record reader/writer,
using the documented GR2 serialization layout and measured Civ V schema.
LSLib's MIT notice is retained for the format reference. Optional OpenGR2 is
pinned separately for local reference decoding and an independent container and
vertex/index byte check. A successful open-source read does not prove game use.

## Local Fort container

Origin: installed macOS game `Civilization V.app/Contents/Assets/Resource/Common/ImprovementModels.fpk`.
Extracted only to ignored `shared/references/local/fort/`. The extractor records
archive/file SHA-256 and paths in its local `provenance.json`.

All six `fort_mid`, `hb_fort_mid`, `pl_fort_mid`, `fort_mod`, `hb_fort_mod`,
`pl_fort_mod` GR2s use v7 signature `29de6cc0baa4532b25f5b7a5f666e2ee`, 32-bit
little-endian pointers, tag `0x80000031`, eight sections, 4-byte alignment,
Oodle1 encoding (2), 12-byte relocation records and no mixed-marshalling records.
CRC32 covers bytes after the 104-byte magic/file header, including the section
table. Section 0 contains objects; 1 vertices; 2 16-bit indices; 6 type records.
Their root record has 13 members and is 92 bytes.

Header word at byte 88 is **string database ID 2**, not an ordinary string CRC in
these files. Missing string relocations contain `~CRC32(UTF8(string)) & 0xffffffff`.
The matching `improvementmodels_stringdatabase.gsd` is itself an uncompressed GR2
with `Strings`, `DatabaseCRC` and `ExtendedData`; 1,597 strings resolve the records.
Examples: `ArtToolInfo` -> `0x9f40e8c6`, `ExporterInfo` -> `0x7a1e8fcd`.
A normal writer can embed strings using relocations and set the database ID to 0.

`fort_mid.gr2` SHA-256:
`f3cc9ee6ce54613c3b11a6ea540f9f2962b1f2db6c29bdc41343671e77ba78ce`.
It has five meshes (64/220/126/4/1508 vertices), 1129 triangles total, three
materials, four skeletons and four models. The final model binds both decal and
Fort body meshes. Four rigid one-bone skeletons accompany unskinned vertices.
No bone weight fields occur in its vertex stream. Bindings are by bone name.

The vertex stride is **60 bytes**: float32 `Position[3]`, `Normal[3]`,
`Tangent[3]`, `Binormal[3]`, `TextureCoordinates0[3]`, in that order. Source
coordinates are Z-up. ArtToolInfo is right `(1,0,0)`, up `(0,0,1)`, back `(0,-1,0)`.
The third texture coordinate exists even for static improvements. The prototype
will preserve BR2 u/v and initialize that absent component to zero; its visual
meaning is not proven. Static all-root weights can be represented by a single
rigid bone binding, as Fort does; nonrigid BR2 inputs must be rejected.

## Material and wrapper records

Materials use `ExtendedData` variants containing `FireGrafixMaterial`: `ShaderSet`,
fallback material, alpha/Z modes, bone count, shadow/reflection flags, version,
visibility and parameter-set references. The Fort body uses **BuildingShader**,
not merely a diffuse Granny texture. Its modes are AlphaMode 8, ZMode 4,
AlphaRef 128, SkinBoneCount 0, Shadows 1, Version 4. The decal and tree-cut meshes
use `LandmarkShader` and `LandmarkShader_Stencil`, outside the first writer profile.

`BuildingGlobal` has nine parameters (view matrices, control values, fog color,
camera, water height, overlay projection and FOW base scale). `BuildingTextures`
has ten: Diffuse, BuildingSREF, Irradiance, SpecSharp, SpecSoft, ColorCorrection,
DistanceFogRamp, FOWMask, FOWBaseLayer and FOWColorKey. Each block stores parallel
names/types/usage/registers/sizes/semantics/storage indices/flags arrays plus
float/integer/texture data. Texture slots occupy groups of four string entries;
unused entries are empty strings. These are serialized engine interface records,
not shader code. Global texture parameters are normally blank for engine binding.

The Fort body references `Fort_MID_DIFF.dds` and `Fort_MID_SREF.dds`; the wrapper
also lists decal diffuse/height and `Generic_Grey_8.dds`. It is a simple `<Asset>`
with `<Mesh file="...gr2" source="Max"/>` and `<Texture .../>` entries. No animation
is necessary for a static wrapper. Pillaged wrappers additionally name effects;
those effects and proprietary textures are not copied to the new converter.

## Validation boundary

Seven synthetic container regression tests pass. A local Fort graph was decoded,
reserialized without compression/hashed strings and read back. The independent
OpenGR2 library loaded that rewritten file and read all five vertex/index counts
and byte CRCs. This does not constitute permission to distribute the rewritten
reference, or evidence of native game rendering. It remains in the ignored cache.
