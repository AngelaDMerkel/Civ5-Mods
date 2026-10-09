#!/usr/bin/env python3
"""Execute gameplay tests in real Lua 5.1, the language version used by Civ V."""
import sys
from packages import ROOT, TERRAIN, PACKAGES, package_files
try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    sys.exit("Install the test dependency in a virtual environment: python -m pip install lupa==2.8")
root = ROOT
compiler = LuaRuntime()
sources = sorted((root / 'mods').glob('*/src/**/*.lua'))
for source in sources:
    compiler.execute("assert(loadstring(...))", source.read_text())
print(f"Lua 5.1 syntax: {len(sources)} production files passed", flush=True)
terrain_files = package_files(PACKAGES[0])
for test in sorted((root / 'mods').glob('*/tests/test_*.lua')):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().TEST_ROOT = str(root)
    lua.globals().RT_LUA = lambda name: str(terrain_files['Lua/' + name + '.lua'])
    for name in ("RT_Config.lua", "RT_Rules.lua"):
        lua.execute((TERRAIN / "Lua" / name).read_text())
    lua.execute(test.read_text())
