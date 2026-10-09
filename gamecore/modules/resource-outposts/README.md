# Outpost native module

Existing [Outpost source](../../../mods/resource-outposts/) owns claims, upkeep
and AI. No extra native provider is registered in core 0.1.0. Add engine services
only for confirmed requirements; Terrain's road/agreement rules must not become
Outpost prerequisites. Preserve optional standalone behavior and existing IDs.
