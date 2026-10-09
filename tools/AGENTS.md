# Shared tools instructions

Apply the root instructions. This is shared support code: inspect affected
consumers before changing paths, formats, defaults or interfaces. Preserve the
active irrigation v2 tooling when working on Terrain or Outposts.

Use paths based on this repository, not a developer's absolute home directory,
for project inputs. Keep approved art under `shared/art/`, generated output under
`output/`/`build/`/`dist/`, and runtime source under `mods/*/src/`.

Package composition belongs in `packages.py`. Reject duplicate installed paths
and VFS names; do not resolve a collision by silently overwriting a source file.
After packaging changes run the Python package tests, build, validator and Lua
tests. Never rewrite approval records just to pass an export validator.
