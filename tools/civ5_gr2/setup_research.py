"""Optional pinned native reference codec and independent reader; Python stdlib only.

Run: python3 tools/civ5_gr2/setup_research.py [--offline]
Conversion itself requires neither network nor these research dependencies.
"""
import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PINS = {
    'lslib': ('https://github.com/Norbyte/lslib.git', '6f5f6987d10d8485876b8368431c948e4dea4f83'),
    'opengr2': ('https://github.com/arves100/opengr2.git', '4e5edd5e98dbd69270d40a92ed94cfe16e57955a'),
    'nexus-buddy-2': ('https://github.com/deliverator23/Nexus-Buddy-2.git', 'c42a7f6d1bac7190dec5fd27efe588db91fc24a3'),
    'wsdlc': ('https://github.com/AngelaDMerkel/Wir-Schaffen-DLC.git', '950a329f57074dfd762e9c32aea7a67a3704b643'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    cache = REPO / 'output/gr2-research'
    cache.mkdir(parents=True, exist_ok=True)
    for name, (url, revision) in PINS.items():
        path = cache / 'upstream' / name
        if not path.exists():
            if args.offline:
                parser.error(f'missing offline source {path}')
            subprocess.run(['git', 'clone', '--no-checkout', url, str(path)], check=True)
            subprocess.run(['git', '-C', str(path), 'checkout', '--detach', revision], check=True)
        head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True)
        if head != revision or dirty:
            parser.error(f'{path} must be clean at {revision}; existing work will not be reset')
    source = cache / 'upstream/opengr2/libopengrn'
    common = ['clang', '-std=c11', '-O2', '-DBUILD_LIBOPENGRN_STATIC', '-I' + str(source)]
    subprocess.run(common + ['-dynamiclib'] + [str(source / n) for n in ('compression.c', 'oodle1.c', 'platform.c')]
                   + ['-o', str(cache / 'libopengrn-codec.dylib')], check=True)
    subprocess.run(common + sorted(str(p) for p in source.glob('*.c'))
                   + [str(Path(__file__).with_name('independent_probe.c')), '-o', str(cache / 'independent-probe')], check=True)
    (cache / 'dependencies.json').write_text(json.dumps(PINS, indent=2) + '\n')
    print('Built native optional research tools in', cache)


if __name__ == '__main__':
    main()
