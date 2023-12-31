from toontown.battle import DistributedBattleAI
from direct.directnotify import DirectNotifyGlobal

class DistributedBattleTutorialAI(DistributedBattleAI.DistributedBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorialAI')
    
    def __init__(self, air, battleMgr, pos, cog, toonId, zoneId,
                 finishCallback=None, maxCogs=4, interactivePropTrackBonus = -1):
        """__init__(air, battleMgr, pos, cog, toonId, zoneId,
                 finishCallback, maxCogs)
        """
        DistributedBattleAI.DistributedBattleAI.__init__(
            self, air, battleMgr, pos, cog, toonId, zoneId,
            finishCallback, maxCogs, tutorialFlag=1)

    # There is no timer in the tutorial... The reward movie is random length.
    def startRewardTimer(self):
        pass

    #def handleRewardDone(self):
    #    DistributedBattleAI.DistributedBattleAI.handleRewardDone(self)
