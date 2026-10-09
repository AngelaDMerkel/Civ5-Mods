# Shared resources

| Resource | Purpose |
| --- | --- |
| [Runtime requirements](requirements/RUNTIME.md) | Compatibility, state, optional integrations and package boundaries |
| [UI requirements](requirements/UI.md) | Common native appearance, behavior and acceptance checks |
| [Player documentation](requirements/DOCUMENTATION.md) | Brief player READMEs and illustrated guides explaining the gameplay |
| [Collection identity](requirements/BRANDING.md) | Shared masthead, icon and wordmark built on WSDLC styling |
| [Art requirements](requirements/ART.md) | Selection process, mesh fidelity, provenance and approval scope |
| [Reference index](references/README.md) | Where source evidence and local comparison material live |
| [UI reference index](references/ui/README.md) | Current controls, styles, icons and integration points |
| [Art inventory](art/README.md) | Versioned original selections, concepts and approvals |
| [Support tool catalog](../tools/README.md) | Shared builders, validators and review tools |

These are common development resources. Each mod's gameplay rules stay in its
own documentation; runtime assets stay in its `src/` tree. Keep shared resources
outside playable packages. Store extracted game art and databases in ignored
`shared/references/local/` or the existing local `output/` caches.
