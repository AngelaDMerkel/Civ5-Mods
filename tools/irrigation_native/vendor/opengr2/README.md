# OpenGr2 Oodle1 decoder

Files from https://github.com/arves100/opengr2 at commit
`4e5edd5e98dbd69270d40a92ed94cfe16e57955a` (MPL-2.0; see LICENSE).
The upstream source credits Arbos/nwn2mdk for Oodle1 decompression.
Only the compression and platform dependencies are included. No proprietary
Granny SDK, game binaries, or game art are included.

Built locally by `native_gr2.py`, using the host C compiler. Supports only the
little-endian Oodle1 path used by the installed Civ V assets. The upstream C
codec is intended for trusted local game archives, not arbitrary uploaded files.

Local change: `debug.h` includes `elements.h` only under `_DEBUG`, avoiding
unrelated parser dependencies in this release-only decoder build.
