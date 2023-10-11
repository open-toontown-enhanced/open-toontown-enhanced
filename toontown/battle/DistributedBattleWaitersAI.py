from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattleFinalAI

class DistributedBattleWaitersAI(DistributedBattleFinalAI.DistributedBattleFinalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleWaitersAI')

    def __init__(self, air, bossCog, roundCallback, finishCallback, battleSide):
        DistributedBattleFinalAI.DistributedBattleFinalAI.__init__(self, air, bossCog, roundCallback, finishCallback, battleSide)

    def startBattle(self, toonIds, cogs):
        self.joinableFsm.request('Joinable')
        for toonId in toonIds:
            if self.addToon(toonId):
                self.activeToons.append(toonId)

        self.d_setMembers()
        for suit in cogs:
            self.pendingCogs.append(suit)

        self.d_setMembers()
        self.needAdjust = 1
        self.b_setState('ReservesJoining')
