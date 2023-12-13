from panda3d.core import AsyncTask
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from ..fishing import FishGlobals

class DistributedFishingSpotAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFishingSpotAI')

    def __init__(self, air, pond, posHpr: tuple[float, float, float, float, float, float]):
        DistributedObjectAI.__init__(self, air)
        self.pond = pond
        self.pondDoId: int = pond.getDoId()
        self.posHpr = posHpr
        self.avId: int = 0
        self.timeoutTask: AsyncTask | None = None

    def getPondDoId(self) -> int:
        return self.pondDoId

    def getPosHpr(self) -> tuple[float, float, float, float, float, float]:
        return self.posHpr

    def __startTimeoutTask(self, timeToAdd: int = 0):
        self.timeoutTask = self.doMethodLater(FishGlobals.CastTimeout + timeToAdd, self.__timeout, self.taskName('timeout'))

    def __timeout(self, task: AsyncTask):
        self.normalExit()

    def __stopTimeoutTask(self):
        if self.timeoutTask is not None:
            self.removeTask(self.timeoutTask)
            self.timeoutTask = None        

    def requestEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if self.avId == avId:
            return
        if self.avId != 0:
            self.sendUpdate('rejectEnter')
            return
        self.__stopTimeoutTask()
        self.acceptOnce(self.air.getAvatarExitEvent(self.avId), self.__handleUnexpectedExit)
        self.avId = avId
        self.pond.addAvId(avId)
        self.d_setOccupied(avId)
        self.d_setMovie(FishGlobals.EnterMovie)
        self.__startTimeoutTask(2)

    def requestExit(self):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.avId:
            self.air.writeServerEvent('suspicious', avId, f'requestExit: {avId} is not fishing in this spot!')
            return
        self.normalExit()

    def removeAvatar(self):
        self.__stopTimeoutTask()
        self.ignore(self.air.getAvatarExitEvent(self.avId))
        self.pond.removeAvId(self.avId)
        self.avId = 0

    def normalExit(self):
        self.removeAvatar()
        self.d_setMovie(FishGlobals.ExitMovie)
        self.doMethodLater(1.2, self.__clearEmpty, self.taskName('clearEmpty'))

    def __clearEmpty(self, task: AsyncTask):
        self.d_setOccupied(0)

    def __handleUnexpectedExit(self):
        self.removeAvatar()
        self.d_setOccupied(0)

    def d_setOccupied(self, avId: int):
        self.sendUpdate('setOccupied', [avId])

    def doCast(self, power: float, heading: float):
        avId = self.air.getAvatarIdFromSender()
        if avId != self.avId:
            self.air.writeServerEvent('suspicious', avId, f'doCast: {avId} is not fishing in this spot!')
            return
        if not 0.0 <= power <= 1.0:
            self.air.writeServerEvent('suspicious', avId, f'doCast: invalid power: {power} from {avId}!')
            return
        if not -FishGlobals.FishingAngleMax <= heading <= FishGlobals.FishingAngleMax:
            self.air.writeServerEvent('suspicious', avId, f'doCast: invalid heading: {heading} from {avId}!')
            return
        av = self.air.doId2do.get(avId)
        if not av:
            self.__handleUnexpectedExit()
            return
        self.__stopTimeoutTask()
        money: int = av.getMoney()
        castCost: int = FishGlobals.getCastCost(av.getFishingRod()) 
        if money < castCost:
            self.normalExit()
            return
        av.b_setMoney(money - castCost)
        self.d_setMovie(FishGlobals.CastMovie, power = power, heading = heading)
        self.__startTimeoutTask()

    def d_setMovie(self, mode: int = 0, code: int = 0, itemDesc1: int = 0, itemDesc2: int = 0,
                   itemDesc3: int = 0, power: int = 0, heading: int = 0):
        self.sendUpdate('setMovie', [mode, code, itemDesc1, itemDesc2, itemDesc3,
                                     power, heading])

    def sellFish(self):
        pass