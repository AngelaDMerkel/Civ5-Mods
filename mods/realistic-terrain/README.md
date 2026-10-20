# Realistic Terrain

Owned by the **Terrain Mod** chat. Gameplay source is in `src/`, tests in `tests/`,
and trade rules in [docs/TRADE.md](docs/TRADE.md). The full current player guide is
[docs/GAMEPLAY.md](../../docs/GAMEPLAY.md).

Current release: Realistic Terrain v2, single-player BNW alpha; UUID
`d571e16c-bb58-40bf-a81f-a919249e7995`. Exposure, military supply, Caravansaries,
Ministry of Coin and replacement trade belong here. Irrigation's source belongs
to its sibling project and is assembled into this release by the shared builder.

The primary distribution target is a **standalone Steam Workshop mod** requiring
Brave New World, with no WSDLC, mod-manager or gameplay-overhaul dependency.
Current Lua/SQL/XML/art content is already packaged on that basis. Native trade
parity remains incomplete; necessary engine support will be a Terrain module in
the project-owned [shared GameCore](../../docs/SHARED-GAMECORE.md), as described
in [the integration plan](docs/NATIVE-INTEGRATION.md). A full Mac developer core
has compiled and passed ABI checks; native launch acceptance and the Terrain
trade implementation remain pending. See the [core validation record](../../gamecore/VALIDATION.md).

The combined worker UI, construction-order infrastructure and irrigation text
still live here. Coordinate changes with Irrigated Farm; do not copy its Lua/SQL
back into this source tree. Resource Outposts shelter remains an optional bridge.

Build/test commands are in the [root README](../../README.md). Shared model tools
are cataloged in [tools/README.md](../../tools/README.md); approved designs are in
`shared/art/rt-models/` and selected icons in `shared/art/terrain-icons-round-3/`.
Native model conversion, UI rendering and gameplay acceptance remain pending.
