from otp.level import DistributedLevelAI, LevelSpec
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from otp.level import LevelSpec
from toontown.toonbase import ToontownGlobals, ToontownBattleGlobals
from toontown.coghq import FactoryEntityCreatorAI, CountryClubRoomSpecs
from toontown.coghq import CountryClubRoomBase, LevelSuitPlannerAI
from toontown.coghq import DistributedCountryClubBattleAI
from toontown.cog import DistributedMintCogAI

class DistributedCountryClubRoomAI(DistributedLevelAI.DistributedLevelAI, CountryClubRoomBase.CountryClubRoomBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCountryClubRoomAI')

    def __init__(self, air, countryClubId, countryClubDoId, zoneId, roomId, roomNum, avIds, battleExpAggreg):
        DistributedLevelAI.DistributedLevelAI.__init__(self, air, zoneId, 0, avIds)
        CountryClubRoomBase.CountryClubRoomBase.__init__(self)
        self.setCountryClubId(countryClubId)
        self.countryClubId = countryClubId
        self.setRoomId(roomId)
        self.roomNum = roomNum
        self.countryClubDoId = countryClubDoId
        self.battleExpAggreg = battleExpAggreg

    def createEntityCreator(self):
        return FactoryEntityCreatorAI.FactoryEntityCreatorAI(level=self)

    def getBattleCreditMultiplier(self):
        return ToontownBattleGlobals.getCountryClubCreditMultiplier(self.countryClubId)

    def generate(self):
        self.notify.debug('generate %s: room=%s' % (self.doId, self.roomId))
        self.notify.debug('loading spec')
        specModule = CountryClubRoomSpecs.getCountryClubRoomSpecModule(self.roomId)
        roomSpec = LevelSpec.LevelSpec(specModule)
        if __dev__:
            self.notify.debug('creating entity type registry')
            typeReg = self.getCountryClubEntityTypeReg()
            roomSpec.setEntityTypeReg(typeReg)
        self.notify.debug('creating entities')
        DistributedLevelAI.DistributedLevelAI.generate(self, roomSpec)
        self.notify.debug('creating cogs')
        cogSpecModule = CountryClubRoomSpecs.getCogSpecModule(self.roomId)
        self.planner = LevelSuitPlannerAI.LevelSuitPlannerAI(self.air, self, DistributedMintCogAI.DistributedMintCogAI, DistributedCountryClubBattleAI.DistributedCountryClubBattleAI, cogSpecModule.CogData, cogSpecModule.ReserveCogData, cogSpecModule.BattleCells, battleExpAggreg=self.battleExpAggreg)
        cogHandles = self.planner.genCogs()
        messenger.send('plannerCreated-' + str(self.doId))
        self.cogs = cogHandles['activeCogs']
        self.reserveCogs = cogHandles['reserveCogs']
        self.d_setCogs()
        self.notify.debug('finish mint room %s %s creation' % (self.roomId, self.doId))

    def requestDelete(self):
        self.notify.info('requestDelete: %s' % self.doId)
        DistributedLevelAI.DistributedLevelAI.requestDelete(self)

    def delete(self):
        self.notify.info('delete: %s' % self.doId)
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

    def getCountryClubId(self):
        return self.countryClubId

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

        description = '%s|%s' % (self.countryClubId, activeVictorIds)
        for avId in activeVictorIds:
            self.air.writeServerEvent('mintDefeated', avId, description)

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
            mint = simbase.air.doId2do.get(self.countryClubDoId)
            if mint is not None:
                mint.allToonsGone()
            else:
                self.notify.warning('no mint %s in allToonsGone' % self.countryClubDoId)
        return

    def challengeDefeated(self):
        countryClub = simbase.air.doId2do.get(self.countryClubDoId)
        if countryClub:
            countryClub.roomDefeated(self)
