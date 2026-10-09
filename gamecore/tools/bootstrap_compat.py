#!/usr/bin/env python3
"""Materialize exactly the locked compatibility commit; safe to vendor."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import shutil


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def bootstrap(lock_path):
    lock_path = Path(lock_path).resolve()
    lock = json.loads(lock_path.read_text())
    commit = lock['commit']
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('compatibility lock requires a full, exact commit')
    if lock['repository'] != 'https://github.com/AngelaDMerkel/civ5-macos-gamecore-compat.git':
        raise ValueError('unrecognized compatibility repository')
    cache = lock_path.parent / '.compat' / commit
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix='.fetch-', dir=cache.parent))
        try:
            source = os.environ.get('CIV5_COMPAT_SOURCE', lock['repository'])
            git(temporary, 'init', '--quiet')
            git(temporary, 'fetch', '--quiet', '--depth=1', source, commit)
            git(temporary, 'checkout', '--quiet', '--detach', commit)
            temporary.rename(cache)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    if git(cache, 'rev-parse', 'HEAD') != commit:
        raise ValueError('compatibility checkout does not match lock')
    # Include ignored files: an injected header must not alter a locked build.
    if git(cache, 'status', '--porcelain', '--untracked-files=all', '--ignored'):
        raise ValueError('compatibility checkout is dirty; remove or repair the cache')
    return cache


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lock', type=Path)
    args = parser.parse_args()
    try:
        print(bootstrap(args.lock))
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
