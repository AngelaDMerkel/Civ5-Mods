# Windows target

The shared BNW source and C++03 registry are kept portable. A Windows GameCore DLL
has **not** been built or validated. The imported SDK deliberately excludes
prebuilt proprietary Windows libraries and old machine-specific project files.

A Windows build needs the compatible Civ V SDK toolchain and link libraries, a
project compiling the same engine/shared/module sources, the one-symbol export
definition in `engine/CvGameCoreDLL_Expansion2/`, and native save/game acceptance.
Do not label the Mac dylib or portable registry tests as a Windows release.
