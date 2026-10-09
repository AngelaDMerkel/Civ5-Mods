# BNW engine source

This directory holds one shared BNW gameplay source tree and its SDK headers.
`upstream.json` pins the source revisions and records every imported file's
original SHA-256 before platform or feature changes. Original copyright notices
remain in the files. This source is excluded from ordinary mod packages.

The BNW 1.0.3.279 C++/header sources agree between the two recorded mirrors after
newline normalization. The Windows resource script has one documented include
difference. No Lekmod or Vox Populi gameplay source is used as the base.

Keep engine integration edits small. New feature implementations belong in
`../modules/`, and shared code in `../src/`; platform/build adapters belong in
`../platforms/`. Use Git history to review changes from this pinned import.
