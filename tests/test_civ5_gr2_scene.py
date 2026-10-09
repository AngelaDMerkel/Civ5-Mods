"""Fixture guard tests only; these mocks are not native renderer validation."""
import unittest
from pathlib import Path

try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    LuaRuntime=None


@unittest.skipIf(LuaRuntime is None,'install tests/requirements.txt to run Lua 5.1 fixture guards')
class SceneTests(unittest.TestCase):
    def run_scene(self, marker, elapsed, multiplayer=False):
        lua=LuaRuntime()
        lua.execute('''
          placed=0; scouts=0; callbacks={}
          local event={Add=function(fn) table.insert(callbacks,fn) end}
          Events={SequenceGameInitComplete=event,LoadScreenClose=event}
          GameInfoTypes={IMPROVEMENT_CG2_STATIC=100,IMPROVEMENT_FORT=14,UNIT_SCOUT=2}
          local plot={GetScriptData=function() return marker end,
            SetImprovementType=function() placed=placed+1 end,SetRevealed=function() end}
          Map={GetPlot=function() return plot end,GetGridSize=function() return 24,16 end,
            GetNumPlots=function() return 384 end,GetPlotByIndex=function() return plot end}
          Game={GetElapsedGameTurns=function() return elapsed end,
            IsGameMultiPlayer=function() return multiplayer end,GetActivePlayer=function() return 0 end}
          Players={[0]={IsHuman=function() return true end,GetTeam=function() return 0 end,
            InitUnit=function() scouts=scouts+1 end}}
          UI={LookAt=function() end};print=function() end
        ''')
        lua.globals().marker=marker;lua.globals().elapsed=elapsed;lua.globals().multiplayer=multiplayer
        lua.execute((Path(__file__).resolve().parents[1]/'tools/civ5_gr2/fixtures/CG2_Scene.lua').read_text())
        lua.execute('for _,fn in ipairs(callbacks) do fn() end')
        return lua.globals().placed,lua.globals().scouts

    def test_ordinary_map_cannot_be_mutated(self):
        self.assertEqual(self.run_scene('',0),(0,0))

    def test_later_save_and_multiplayer_cannot_be_mutated(self):
        self.assertEqual(self.run_scene('CG2_STATIC_TEST_V1',1),(0,0))
        self.assertEqual(self.run_scene('CG2_STATIC_TEST_V1',0,True),(0,0))

    def test_two_callbacks_create_exactly_one_fresh_scene(self):
        self.assertEqual(self.run_scene('CG2_STATIC_TEST_V1',0),(2,1))


if __name__=='__main__':unittest.main()
