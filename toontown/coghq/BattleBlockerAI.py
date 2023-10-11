from otp.level import DistributedEntityAI
from direct.directnotify import DirectNotifyGlobal

class BattleBlockerAI(DistributedEntityAI.DistributedEntityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleBlockerAI')

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.cogIds = []
        self.active = 1

    def destroy(self):
        self.notify.debug('delete')
        self.ignoreAll()
        DistributedEntityAI.DistributedEntityAI.destroy(self)

    def generate(self):
        DistributedEntityAI.DistributedEntityAI.generate(self)
        self.accept('plannerCreated-' + str(self.level.doId), self.registerBlocker)

    def registerBlocker(self):
        if hasattr(self.level, 'planner'):
            self.level.planner.battleMgr.addBattleBlocker(self, self.cellId)

    def deactivate(self):
        if self.isDeleted():
            return
        self.active = 0
        self.sendUpdate('setActive', [self.active])

    def getActive(self):
        return self.active

    def addCog(self, cog):
        self.cogIds.append(cog.doId)
        self.d_setCogs()

    def removeCog(self, cog):
        try:
            self.cogIds.remove(cog.doId)
            self.d_setCogs()
        except:
            self.notify.debug("didn't have cogId %d" % cog.doId)

    def d_setCogs(self):
        self.sendUpdate('setCogs', [self.cogIds])

    def b_setBattle(self, battleId):
        self.battle = battleId
        self.d_setBattle(battleId)

    def d_setBattle(self, battleId):
        self.sendUpdate('setBattle', [battleId])

    def b_setBattleFinished(self):
        self.deactivate()
        self.setBattleFinished()
        self.d_setBattleFinished()

    def setBattleFinished(self):
        self.notify.debug('setBattleFinished: %s' % self.entId)
        messenger.send('battleBlockerFinished-' + str(self.entId))
        messenger.send(self.getOutputEventName(), [1])

    def d_setBattleFinished(self):
        self.sendUpdate('setBattleFinished', [])

    if __dev__:

        def attribChanged(self, *args):
            self.cogIds = []
            cogs = self.level.planner.battleCellId2cogs.get(self.cellId)
            if cogs:
                for cog in cogs:
                    self.cogIds.append(cog.doId)

            else:
                self.notify.warning("Couldn't find battle cell id %d in battleCellId2cogs" % self.cellId)
            self.d_setCogs()
            self.registerBlocker()
