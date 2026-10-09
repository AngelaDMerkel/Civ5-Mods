#!/usr/bin/env python3
"""Compile and run portable core tests; native acceptance is separate."""
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
        random_binary = Path(directory) / 'random-seed-tests'
        subprocess.run(compiler + [
            '-std=c++03', '-Wall', '-Wextra', '-Werror', '-pedantic',
            '-I', str(ROOT / 'include'), str(ROOT / 'tests/random_seed.cpp'),
            '-o', str(random_binary),
        ], check=True)
        subprocess.run([str(random_binary)], check=True)
        context_binary = Path(directory) / 'core-context-tests'
        subprocess.run(compiler + [
            '-std=c++03', '-Wall', '-Wextra', '-Werror', '-pedantic',
            '-I', str(ROOT / 'include'),
            str(ROOT / 'src/C5M_ModuleRegistry.cpp'),
            str(ROOT / 'src/C5M_CoreContext.cpp'),
            str(ROOT / 'tests/core_context.cpp'), '-o', str(context_binary),
        ], check=True)
        subprocess.run([str(context_binary)], check=True)


if __name__ == '__main__':
    main()
