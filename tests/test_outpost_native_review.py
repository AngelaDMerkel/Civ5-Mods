"""Disposable scene safety/state checks; not evidence of native rendering."""
import unittest
from pathlib import Path

try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    LuaRuntime = None


@unittest.skipIf(LuaRuntime is None, 'install tests/requirements.txt')
class OutpostReviewTests(unittest.TestCase):
    def scene(self, marker='CG2_STATIC_TEST_V1', turn=0, multiplayer=False, production=False):
        lua = LuaRuntime()
        lua.execute('''
          callbacks={}; units=0; plots={}; reveals=0
          local event={Add=function(fn) table.insert(callbacks,fn) end}
          Events={SequenceGameInitComplete=event,LoadScreenClose=event,RequestYieldDisplay=function() end}
          GameInfoTypes={IMPROVEMENT_CG2_STATIC=100,IMPROVEMENT_FORT=14,BUILD_CG2_STATIC=50,UNIT_WARRIOR=2}
          Map={GetGridSize=function() return 24,16 end,GetNumPlots=function() return 384 end}
          function Map.GetPlot(x,y)
            local key=x+24*y
            if not plots[key] then
              local p={kind=-1,progress=0,pillaged=false}
              function p:GetScriptData() return marker end
              function p:GetX() return x end
              function p:GetY() return y end
              function p:IsGoody() return false end
              function p:SetImprovementType(k) self.kind=k end
              function p:GetImprovementType() return self.kind end
              function p:ChangeVisibilityCount() reveals=reveals+1 end
              function p:ChangeBuildProgress(b,n) self.progress=self.progress+n end
              function p:GetBuildProgress() return self.progress end
              function p:SetImprovementPillaged(v) self.pillaged=v end
              plots[key]=p
            end
            return plots[key]
          end
          function Map.GetPlotByIndex(i) return Map.GetPlot(i%24,math.floor(i/24)) end
          Game={GetElapsedGameTurns=function() return turn end,IsGameMultiPlayer=function() return multiplayer end,
            GetActivePlayer=function() return 0 end}
          Players={[0]={IsHuman=function() return true end,GetTeam=function() return 0 end,
            GetID=function() return 0 end,InitUnit=function() units=units+1 end}}
          UI={LookAt=function() end,SetYieldVisibleMode=function() end};YieldDisplayTypes={AREA=1}
          print=function() end
        ''')
        lua.globals().marker=marker; lua.globals().turn=turn; lua.globals().multiplayer=multiplayer
        name='RO_ProductionScene.lua' if production else 'RO_RenderScene.lua'
        lua.execute((Path(__file__).resolve().parents[1]/'mods/resource-outposts/tests/native'/name).read_text())
        lua.execute('for _,fn in ipairs(callbacks) do fn() end')
        return lua

    def test_campaign_save_and_multiplayer_are_untouched(self):
        for production in (False, True):
            for args in (('', 0, False), ('CG2_STATIC_TEST_V1', 1, False), ('CG2_STATIC_TEST_V1', 0, True)):
                lua=self.scene(*args, production=production)
                self.assertEqual(lua.globals().units, 0)
                self.assertEqual(lua.globals().reveals, 0)

    def test_duplicate_callbacks_keep_construction_incomplete_and_pillage_real(self):
        lua=self.scene()
        self.assertEqual(lua.globals().units, 1)
        self.assertEqual(lua.globals().reveals, 49)
        self.assertEqual(lua.eval('Map.GetPlot(8,8).kind'), 100)
        self.assertEqual(lua.eval('Map.GetPlot(10,8).kind'), -1)
        self.assertEqual(lua.eval('Map.GetPlot(10,8).progress'), 1)
        self.assertTrue(lua.eval('Map.GetPlot(8,10).pillaged'))
        self.assertEqual(lua.eval('Map.GetPlot(10,10).kind'), 14)


if __name__ == '__main__':
    unittest.main()
