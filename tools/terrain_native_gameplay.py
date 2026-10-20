#!/usr/bin/env python3
"""Stage current Terrain content with a disposable native acceptance probe."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from build import manifest, write_xml
from packages import ROOT, PACKAGES, RT_ID, package_files


def stage(output):
    if output.exists():
        raise ValueError('Use a fresh Terrain probe directory')
    spec = next(p for p in PACKAGES if p['id'] == RT_ID)
    originals = package_files(spec)
    hashes = {}
    for name, path in originals.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    shutil.copyfile(ROOT / 'mods/realistic-terrain/tests/native/C5M_TerrainChecks.lua',
                    output / 'Lua/C5M_TerrainChecks.lua')
    with (output / 'UI/RT_Environment.lua').open('a') as stream:
        stream.write('\n-- Disposable acceptance fixture only.\ninclude("C5M_TerrainChecks.lua");\n')
    files = {p.relative_to(output).as_posix(): p for p in sorted(output.rglob('*')) if p.is_file()}
    write_xml(manifest(files, spec), output / (spec['name'] + '.modinfo'))
    (output / 'fixture.json').write_text(json.dumps(dict(
        source_hashes=hashes,
        scope='Current Terrain ordinary-mod entrypoint and Lua runtime on the shared Mac GameCore',
        instrumentation='One test include appended to the staged UI copy; diagnostic update delegates to the production marker update',
        limits='No engine-owned trade, full campaign, custom models or process-restart persistence acceptance',
    ), indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    stage(parser.parse_args().output)
