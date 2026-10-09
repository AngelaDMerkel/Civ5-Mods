# Shared GameCore instructions

Apply the root instructions. The user requested one project-owned GameCore that
can support the repository's mods as optional modules. This is shared native
source, not another gameplay mod or a copy of Terrain's Lua runtime.

- Keep a BNW gameplay baseline; do not silently adopt Lekmod/VP balance rules.
- Compile native modules into one core per supported platform. Enabling an
  already-supported mod must not require a different binary for that combination.
- Advertise a capability only after its engine implementation exists. Test
  fixtures and proposed APIs are not gameplay support.
- Resolve explicit module requests before gameplay. Missing versions, conflicts,
  duplicate providers and incompatible saves must fail clearly, not partly run.
- Keep capabilities disabled when their owning content is absent. Never run both
  Lua and native owners of the same route, payment or other simulation.
- Preserve the existing standalone packages. Keep native source/build outputs
  outside their registered source roots. WSDLC must remain optional.
- Native changes require compiled tests plus later game/ABI/save validation;
  portable C++ tests alone do not establish a loadable Windows or Mac GameCore.
- Keep C++ compatible with the chosen BNW toolchain. The current registry uses
  C++03 and the standard library; it has no DLL/plugin ABI or SDK dependency.

Run `python3 gamecore/tests/run.py` for the native foundation. See README.md for
the implementation boundary and `docs/SHARED-GAMECORE.md` for the design.
