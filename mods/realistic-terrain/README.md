# Realistic Terrain

Owned by the **Terrain Mod** chat. Gameplay source is in `src/`, tests in `tests/`,
and trade rules in [docs/TRADE.md](docs/TRADE.md). The full current player guide is
[docs/GAMEPLAY.md](../../docs/GAMEPLAY.md).

Current release: Realistic Terrain v2, single-player BNW alpha; UUID
`d571e16c-bb58-40bf-a81f-a919249e7995`. Exposure, military supply, Caravansaries,
Ministry of Coin and replacement trade belong here. Irrigation's source belongs
to its sibling project and is assembled into this release by the shared builder.

The combined worker UI, construction-order infrastructure and irrigation text
still live here. Coordinate changes with Irrigated Farm; do not copy its Lua/SQL
back into this source tree. Resource Outposts shelter remains an optional bridge.

Build/test commands are in the [root README](../../README.md). Shared model tools
are cataloged in [tools/README.md](../../tools/README.md); approved designs are in
`shared/art/rt-models/` and selected icons in `shared/art/terrain-icons-round-3/`.
Native model conversion, UI rendering and gameplay acceptance remain pending.

The Outposts integration test found that stock macOS BNW resolves the shortened
`RT_Irrigation` include to `RT_IrrigationAI.lua`. Startup now uses exact `.lua`
filenames, adapting Terrain owner commit `4f94732` to this branch's module set.
The UI regression requires that convention. See the scoped native evidence in
[Outposts gameplay checks](../resource-outposts/docs/NATIVE-GAMEPLAY-TESTS.md);
this compatibility fix does not establish full Terrain gameplay acceptance.
