#!/usr/bin/env python3
"""Package a validated developer build; never installs or publishes a GameCore."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
from bootstrap_compat import bootstrap

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
BINARY = 'libCvGameCoreDLL_Expansion2_DLL.dylib'


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()


def package(output, app=None):
    build = REPO / 'build/gamecore/macos'
    report = json.loads((build / 'build-report.json').read_text())
    if report['source_dirty'] or report['source_commit'] != git('rev-parse', 'HEAD') or git('status', '--porcelain'):
        raise ValueError('commit changes, then rebuild --incremental from the clean revision before packaging')
    binary = (build / BINARY).read_bytes()
    digest = hashlib.sha256(binary).hexdigest()
    if digest != report['binary_sha256']:
        raise ValueError('binary does not match the build report')
    compat = bootstrap(ROOT / 'compat.lock.json')
    lock = json.loads((ROOT / 'compat.lock.json').read_text())
    if report['compat_commit'] != lock['commit']:
        raise ValueError('build used a different compatibility revision')
    spec = importlib.util.spec_from_file_location('c5m_compat_validation', compat / 'tools/validate.py')
    validation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validation)
    result = validation.validate(build / BINARY, app=app)

    files = {
        BINARY: binary,
        'build-report.json': (json.dumps(report, indent=2) + '\n').encode(),
        'validation.json': (json.dumps(result, indent=2) + '\n').encode(),
        'compat.lock.json': (ROOT / 'compat.lock.json').read_bytes(),
        'upstream.json': (ROOT / 'engine/upstream.json').read_bytes(),
        'compat.LICENSE': (ROOT / 'third_party/compat.LICENSE').read_bytes(),
        'README.txt': (
            'Shared Civ V GameCore: developer build, not a Workshop package.\n'
            'This archive does not install anything and does not require WSDLC.\n'
            'Keep the existing Lua content backend. Native trade and other gameplay\n'
            'providers are not implemented or advertised by this build.\n'
            'Binary/ABI validation is not native startup, gameplay or save acceptance.\n'
            'Native installation and acceptance remain deferred. Do not overwrite\n'
            'your installed game using this archive as an installation guide.\n'
            'Source and acceptance contract: gamecore/ in the recorded source commit.\n'
        ).encode(),
    }
    manifest = {
        'format': 1,
        'product': 'civ5-mods',
        'edition': 'developer',
        'source_commit': report['source_commit'],
        'platform': 'macos-x86_64',
        'native_acceptance': 'deferred',
        'host_hash_checked': app is not None,
        'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
    }
    files['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp.zip')
    try:
        with zipfile.ZipFile(temporary, 'w') as archive:
            for name, data in sorted(files.items()):
                entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, data)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('archive CRC verification failed')
            for name, expected in manifest['files'].items():
                if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                    raise ValueError('archive content hash mismatch: ' + name)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(output)
    print('SHA-256:', hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=REPO / 'dist/native/C5M-GameCore-macos-developer.zip')
    parser.add_argument('--app', type=Path, help='read-only verification of the installed host executable hash')
    args = parser.parse_args()
    try:
        package(args.output.resolve(), args.app)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
