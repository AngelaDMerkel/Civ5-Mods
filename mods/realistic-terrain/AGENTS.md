# Realistic Terrain instructions

Apply the root `AGENTS.md` and common requirements. Own exposure, supply,
Caravansaries, Ministry, trade, and the current combined `RT_Environment` UI.
Preserve `RT_` identifiers, package UUID/version and saved-state contracts.

Distribution decision, 2026-10-09: prefer a standard, standalone Steam Workshop
mod. Do not require WSDLC, Lekmod, Vox Populi or another mod manager/overhaul.
Exhaust supported Lua/SQL/XML/art capabilities first. If a confirmed feature
needs native support, develop a minimal Terrain-owned extension and document its
platform/install boundary; WSDLC may remain an optional distribution tool only.
Do not silently remove required features or introduce an engine dependency into
the standard package. See docs/NATIVE-INTEGRATION.md.

Irrigation source is in `../irrigated-farm/src/`; its construction/UI/text hooks
remain in this mod. Changes to those hooks need both Terrain and irrigation tests.
Do not accidentally make Resource Outposts a required dependency or change its
extraction rules through the optional shelter bridge.

Keep model builders outside this directory in `tools/`. Approved icons/models
and their selection process are recorded under `shared/art/` and
`shared/requirements/ART.md`. Record behavior changes in this README, the player
guide or `docs/TRADE.md` as appropriate.
