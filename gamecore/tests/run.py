#!/usr/bin/env python3
"""Compile and run foundation tests; this does not build a Civ V GameCore."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    compiler = shlex.split(os.environ.get('CXX', 'c++'))
    with tempfile.TemporaryDirectory(prefix='c5m-registry-') as directory:
        binary = Path(directory) / 'module-registry-tests'
        subprocess.run(compiler + [
            '-std=c++03', '-Wall', '-Wextra', '-Werror', '-pedantic',
            '-I', str(ROOT / 'include'),
            str(ROOT / 'src/C5M_ModuleRegistry.cpp'),
            str(ROOT / 'tests/module_registry.cpp'), '-o', str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    main()
