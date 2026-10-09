#!/usr/bin/env python3
"""Execute gameplay tests in real Lua 5.1, the language version used by Civ V."""
from pathlib import Path
import sys
try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    sys.exit("Install the test dependency in a virtual environment: python -m pip install lupa==2.8")
root = Path(__file__).resolve().parents[1]
compiler = LuaRuntime()
sources = sorted((root / "mod").rglob("*.lua")) + sorted((root / "outposts").rglob("*.lua"))
for source in sources:
    compiler.execute("assert(loadstring(...))", source.read_text())
print(f"Lua 5.1 syntax: {len(sources)} production files passed", flush=True)
for test in ("test_rules.lua", "test_gameplay.lua", "test_construction.lua", "test_trade_economy.lua", "test_trade_rules.lua", "test_trade.lua", "test_outposts.lua", "test_irrigation.lua", "test_art.lua"):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().TEST_ROOT = str(root)
    for name in ("RT_Config.lua", "RT_Rules.lua"):
        lua.execute((root / "mod/Lua" / name).read_text())
    lua.execute((root / "tests" / test).read_text())
