from otp.level import DistributedLevelAI, LevelSpec
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from otp.level import LevelSpec
from toontown.toonbase import ToontownGlobals, ToontownBattleGlobals
from toontown.coghq import FactoryEntityCreatorAI, MintRoomSpecs
from toontown.coghq import MintRoomBase, LevelCogPlannerAI
from toontown.coghq import DistributedMintBattleAI
from toontown.cog import DistributedMintCogAI

class DistributedMintRoomAI(DistributedLevelAI.DistributedLevelAI, MintRoomBase.MintRoomBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMintRoomAI')

    def __init__(self, air, mintId, mintDoId, zoneId, roomId, roomNum, avIds, battleExpAggreg):
        DistributedLevelAI.DistributedLevelAI.__init__(self, air, zoneId, 0, avIds)
        MintRoomBase.MintRoomBase.__init__(self)
        self.setMintId(mintId)
        self.setRoomId(roomId)
        self.roomNum = roomNum
        self.mintDoId = mintDoId
        self.battleExpAggreg = battleExpAggreg

    def createEntityCreator(self):
        return FactoryEntityCreatorAI.FactoryEntityCreatorAI(level=self)

    def getBattleCreditMultiplier(self):
        return ToontownBattleGlobals.getMintCreditMultiplier(self.mintId)

    def generate(self):
        self.notify.debug('generate %s: room=%s' % (self.doId, self.roomId))
        self.notify.debug('loading spec')
        specModule = MintRoomSpecs.getMintRoomSpecModule(self.roomId)
        roomSpec = LevelSpec.LevelSpec(specModule)
        if __dev__:
            self.notify.debug('creating entity type registry')
            typeReg = self.getMintEntityTypeReg()
            roomSpec.setEntityTypeReg(typeReg)
        self.notify.debug('creating entities')
        DistributedLevelAI.DistributedLevelAI.generate(self, roomSpec)
        self.notify.debug('creating cogs')
        cogSpecModule = MintRoomSpecs.getCogSpecModule(self.roomId)
        self.planner = LevelCogPlannerAI.LevelCogPlannerAI(self.air, self, DistributedMintCogAI.DistributedMintCogAI, DistributedMintBattleAI.DistributedMintBattleAI, cogSpecModule.CogData, cogSpecModule.ReserveCogData, cogSpecModule.BattleCells, battleExpAggreg=self.battleExpAggreg)
        cogHandles = self.planner.genCogs()
        messenger.send('plannerCreated-' + str(self.doId))
        self.cogs = cogHandles['activeCogs']
        self.reserveCogs = cogHandles['reserveCogs']
        self.d_setCogs()
        self.notify.debug('finish mint room %s %s creation' % (self.roomId, self.doId))

    def delete(self):
        self.notify.debug('delete: %s' % self.doId)
        cogs = self.cogs
        for reserve in self.reserveCogs:
            cogs.append(reserve[0])

        self.planner.destroy()
        del self.planner
        for cog in cogs:
            if not cog.isDeleted():
                cog.factoryIsGoingDown()
                cog.requestDelete()

        del self.battleExpAggreg
        DistributedLevelAI.DistributedLevelAI.delete(self, deAllocZone=False)

    def getMintId(self):
        return self.mintId

    def getRoomId(self):
        return self.roomId

    def getRoomNum(self):
        return self.roomNum

    def getCogLevel(self):
        return self.cogLevel

    def d_setCogs(self):
        self.sendUpdate('setCogs', [self.getCogs(), self.getReserveCogs()])

    def getCogs(self):
        cogIds = []
        for cog in self.cogs:
            cogIds.append(cog.doId)

        return cogIds

    def getReserveCogs(self):
        cogIds = []
        for cog in self.reserveCogs:
            cogIds.append(cog[0].doId)

        return cogIds

    def d_setBossConfronted(self, toonId):
        if toonId not in self.avIdList:
            self.notify.warning('d_setBossConfronted: %s not in list of participants' % toonId)
            return
        self.sendUpdate('setBossConfronted', [toonId])

    def setVictors(self, victorIds):
        activeVictors = []
        activeVictorIds = []
        for victorId in victorIds:
            toon = self.air.doId2do.get(victorId)
            if toon is not None:
                activeVictors.append(toon)
                activeVictorIds.append(victorId)

        description = '%s|%s' % (self.mintId, activeVictorIds)
        for avId in activeVictorIds:
            self.air.writeServerEvent('mintDefeated', avId, description)

        for toon in activeVictors:
            simbase.air.questManager.toonDefeatedMint(toon, self.mintId, activeVictors)

        return

    def b_setDefeated(self):
        self.d_setDefeated()
        self.setDefeated()

    def d_setDefeated(self):
        self.sendUpdate('setDefeated')

    def setDefeated(self):
        pass

    def allToonsGone(self, toonsThatCleared):
        DistributedLevelAI.DistributedLevelAI.allToonsGone(self, toonsThatCleared)
        if self.roomNum == 0:
            mint = simbase.air.doId2do.get(self.mintDoId)
            if mint is not None:
                mint.allToonsGone()
            else:
                self.notify.warning('no mint %s in allToonsGone' % self.mintDoId)
        return
