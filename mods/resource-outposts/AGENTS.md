# Resource Outposts instructions

Apply root instructions and shared requirements. Keep this package usable by
itself. Do not introduce roads, supply, trade-agreement or Ministry gates into
resource extraction or optional garrison shelter. Preserve the existing UUID,
`RO_` Lua interfaces and the historic `RT_` database identifiers used by outposts.

Keep resource transfer, territorial ownership, maintenance and abandonment
accounting consistent; do not double-count native and neutral-site resources.
Changes to integration must pass tests with Terrain absent and present.

Keep mesh tooling in `tools/` and approved era references under `shared/art/`.
Preserve the approved architecture and central garrison space. Source design
approval does not establish native conversion or automatic era switching.
