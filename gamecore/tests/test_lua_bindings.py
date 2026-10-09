#!/usr/bin/env python3
"""Run the production C++ bindings against Lupa's real Lua 5.1 (not Civ V)."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from lupa import lua51

ROOT = Path(__file__).resolve().parents[1]


class NativeLuaBindings(unittest.TestCase):
    def test_lifecycle_capabilities_and_stack(self):
        lua = ctypes.CDLL(lua51.__file__, mode=ctypes.RTLD_GLOBAL)
        lua.luaL_newstate.restype = ctypes.c_void_p
        lua.luaL_openlibs.argtypes = [ctypes.c_void_p]
        lua.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lua.lua_pcall.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        lua.lua_tolstring.restype = ctypes.c_char_p
        lua.lua_close.argtypes = [ctypes.c_void_p]
        with tempfile.TemporaryDirectory(prefix='c5m-lua-') as directory:
            library = Path(directory) / 'bindings.dylib'
            subprocess.run([
                'clang++', '-std=c++11', '-dynamiclib', '-undefined', 'dynamic_lookup',
                '-Wall', '-Wextra', '-Werror', '-I', str(ROOT / 'include'),
                '-I', str(ROOT / 'engine/sdk/ThirdPartyLibs/Lua51/include'),
                str(ROOT / 'src/C5M_ModuleRegistry.cpp'),
                str(ROOT / 'src/C5M_CoreContext.cpp'), str(ROOT / 'src/C5M_Lua.cpp'),
                str(ROOT / 'tests/lua_bindings.cpp'), '-o', str(library),
            ], check=True)
            bindings = ctypes.CDLL(str(library))
            bindings.c5m_test_register.argtypes = [ctypes.c_void_p]
            bindings.c5m_test_configure.argtypes = [ctypes.c_int]
            state = lua.luaL_newstate()
            self.assertTrue(state)
            try:
                lua.luaL_openlibs(state)
                self.assertEqual(bindings.c5m_test_register(state), 1)

                def check(source):
                    status = lua.luaL_loadstring(state, source.encode())
                    if status == 0:
                        status = lua.lua_pcall(state, 0, 0, 0)
                    if status:
                        self.fail(lua.lua_tolstring(state, -1, None).decode())

                check('''
                    assert(Game.ExistingMember == 42)
                    assert(Game.C5MGetCoreInfo().Phase == 'unconfigured')
                    assert(not Game.C5MGetCoreInfo().Ready)
                    assert(#Game.C5MGetModules() == 0)
                    assert(not Game.C5MHasCapability('c5m.core-introspection', 1))
                ''')
                self.assertEqual(bindings.c5m_test_configure(0), 1)
                check('''
                    local info = Game.C5MGetCoreInfo()
                    assert(info.Ready and info.Phase == 'frozen')
                    assert(info.Version == '0.1.0' and info.APIVersion == 1)
                    assert(info.Error == '' and not info.OwnsModSimulation)
                    assert(info.SelectionKey:find('c5m.core', 1, true))
                    assert(Game.C5MHasCapability('c5m.core-introspection', 1))
                    assert(not Game.C5MHasCapability('c5m.core-introspection', 2))
                    assert(not Game.C5MHasCapability('terrain.native-trade', 1))
                    local modules = Game.C5MGetModules()
                    assert(#modules == 1 and modules[1] == 'c5m.core')
                    modules[1] = 'invented'
                    info.Phase = 'invented'
                    assert(Game.C5MGetModules()[1] == 'c5m.core')
                    assert(Game.C5MGetCoreInfo().Phase == 'frozen')
                    for _, version in ipairs({0, -1, 1.5, 2147483648, math.huge, 0/0}) do
                        assert(not pcall(Game.C5MHasCapability, 'c5m.core-introspection', version))
                    end
                    assert(not pcall(Game.C5MHasCapability, 'c5m.core-introspection'))
                ''')
                self.assertEqual(bindings.c5m_test_configure(1), 0)
                check('''
                    local info = Game.C5MGetCoreInfo()
                    assert(not info.Ready and info.Phase == 'failed')
                    assert(info.Error:find('Module not compiled', 1, true))
                    assert(info.SelectionKey == '' and #Game.C5MGetModules() == 0)
                    assert(not Game.C5MHasCapability('c5m.core-introspection', 1))
                ''')
                self.assertEqual(bindings.c5m_test_configure(0), 1)
                check("assert(Game.C5MHasCapability('c5m.core-introspection', 1))")
            finally:
                lua.lua_close(state)


if __name__ == '__main__':
    unittest.main()
