# Realistic Terrain instructions

Apply the root `AGENTS.md` and common requirements. Own exposure, supply,
Caravansaries, Ministry, trade, and the current combined `RT_Environment` UI.
Preserve `RT_` identifiers, package UUID/version and saved-state contracts.

Irrigation source is in `../irrigated-farm/src/`; its construction/UI/text hooks
remain in this mod. Changes to those hooks need both Terrain and irrigation tests.
Do not accidentally make Resource Outposts a required dependency or change its
extraction rules through the optional shelter bridge.

Keep model builders outside this directory in `tools/`. Approved icons/models
and their selection process are recorded under `shared/art/` and
`shared/requirements/ART.md`. Record behavior changes in this README, the player
guide or `docs/TRADE.md` as appropriate.
