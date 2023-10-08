from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toonbase import ToontownGlobals

class NewsManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('NewsManagerAI')

    def getWeeklyCalendarHolidays(self):
        return []

    def getYearlyCalendarHolidays(self):
        return []

    def getOncelyCalendarHolidays(self):
        return []

    def getRelativelyCalendarHolidays(self):
        return []

    def getMultipleStartHolidays(self):
        return []

    def generate(self):
        DistributedObjectAI.generate(self)
        self.accept('avatarEntered', self.__handleAvatarEntered)

    def delete(self):
        self.ignoreAll()
        DistributedObjectAI.delete(self)

    def __handleAvatarEntered(self, av: DistributedToonAI):
        if self.air.cogInvasionManager.getInvading():
            cogType, isSkelecog = self.air.cogInvasionManager.getCogType()
            numCogsRemaining = self.air.cogInvasionManager.getNumCogsRemaining()
            self.sendUpdateToAvatarId(av.doId, 'setInvasionStatus',
                                      [ToontownGlobals.SuitInvasionBulletin, cogType, numCogsRemaining, isSkelecog])

    def invasionBegin(self, cogType: str, numCogsRemaining: int, isSkelecog: bool):
        self.sendUpdate('setInvasionStatus',
                        [ToontownGlobals.SuitInvasionBegin, cogType, numCogsRemaining, isSkelecog])

    def invasionEnd(self, cogType: str, numCogsRemaining: int, isSkelecog: bool):
        self.sendUpdate('setInvasionStatus',
                        [ToontownGlobals.SuitInvasionEnd, cogType, numCogsRemaining, isSkelecog])