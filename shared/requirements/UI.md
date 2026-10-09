# Shared UI requirements

Use native Civ V controls, typography and panel styles where practical. The
[reference index](../references/ui/README.md) records the current implementation;
it is a starting point, not proof that layouts have passed an in-game review.

- Build additive mod contexts. Avoid replacing game UI files for a convenience
  feature, and keep context/file names unique across companions.
- Use localized player-facing text for new controls. Existing hard-coded Terrain
  trade labels are migration debt, not a precedent for new strings.
- Present action availability, the reason an action is disabled, ongoing work and
  cancellation clearly. Destructive gameplay actions should show their concrete
  resource/upkeep effects before confirmation, as Outposts already does.
- Recheck active player, ownership and eligibility in action callbacks. UI
  refreshes are observational; game events own gameplay progression.
- Show only information the player may know. Do not leak hidden tile resources,
  enemy actions or unseen routes through status messages.
- Ensure windows close, scroll correctly, do not block unrelated map interaction,
  and hide appropriately on selection changes, city screens and turn changes.
- Test at 1024×768 and a widescreen resolution, with long labels and populated
  lists, both alone and with companions enabled. Check panel overlap, tooltip
  readability, icon clipping, disabled states and save/load behavior.

Current integration concerns: Terrain and Outposts both declare construction
panels at the top center; verify their runtime placement together. Irrigation's
worker button remains inside Terrain's context. Separating irrigation must account
for that shared space and construction-order ownership. Do not claim these issues
are resolved from an XML inspection alone.
