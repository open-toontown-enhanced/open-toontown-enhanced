""" CogPlannerTutorial module: contains the CogPlannerTutorial class
    which handles management of the cog you will fight during the
    tutorial."""

from otp.ai.AIBaseGlobal import *

from direct.directnotify import DirectNotifyGlobal
from toontown.cog import DistributedTutorialCogAI
from . import TutorialBattleManagerAI

class CogPlannerTutorialAI:
    """
    CogPlannerTutorialAI: manages the single cog that you fight during
    the tutorial.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'CogPlannerTutorialAI')

    def __init__(self, air, zoneId, battleOverCallback):
        # Store these things
        self.zoneId = zoneId
        self.air = air
        self.battle = None
        # This callback will be used to open the HQ doors when the
        # battle is over.
        self.battleOverCallback = battleOverCallback

        # Create a battle manager
        self.battleMgr = TutorialBattleManagerAI.TutorialBattleManagerAI(
            self.air)

        # Create a flunky
        newCog = DistributedTutorialCogAI.DistributedTutorialCogAI(self.air, self)
        newCog.setupCogDNA(1, 1, "c")
        # This is a special tutorial path state
        newCog.generateWithRequired(self.zoneId)
        self.cog = newCog

    def cleanup(self):
        self.zoneId = None
        self.air = None
        if self.cog:
            self.cog.requestDelete()
            self.cog = None
        if self.battle:
            #self.battle.requestDelete()
            #RAU made to kill the mem leak when you close the window in the middle of the battle tutorial
            cellId = self.battle.battleCellId
            battleMgr = self.battle.battleMgr
            if cellId in battleMgr.cellId2battle:
                battleMgr.destroy(self.battle)
            
            self.battle = None

    def getDoId(self):
        # This is here because the cog expects the cog planner to be
        # a distributed object, if it has a cog planner. We want it to
        # have a cog planner, but not a distributed one, so we return
        # 0 when asked what our DoId is. Kind of hackful, I guess.
        return 0

    def requestBattle(self, zoneId, cog, toonId):
        # 70, 20, 0 is a battle cell position that I just made up.
        self.battle = self.battleMgr.newBattle(
            zoneId, zoneId, Vec3(35, 20, 0),
            cog, toonId,
            finishCallback=self.battleOverCallback)
        return 1

    def removeCog(self, cog):
        # Get rid of the cog.
        cog.requestDelete()
        self.cog = None
