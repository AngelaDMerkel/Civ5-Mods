#!/usr/bin/env python3
"""Build the shared Mac GameCore using the pinned existing platform driver."""
import argparse
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
from bootstrap_compat import bootstrap

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--incremental', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('this build entry point currently targets macOS')
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    compat = bootstrap(ROOT/'compat.lock.json')
    command = [sys.executable, str(compat/'tools/build.py'), '--config',
               str(ROOT/'platforms/macos/build.json'), '--jobs', str(args.jobs)]
    if args.incremental:
        command.append('--incremental')
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
