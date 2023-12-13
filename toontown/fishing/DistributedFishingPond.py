from typing import Union
from panda3d.core import Vec3
from direct.distributed.DistributedObject import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task

class DistributedFishingPond(DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFishingPond')
    pollInterval = 0.5

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.notify.debug('init')
        self.targets: dict[int, DistributedObject] = {}
        self.area: int | None = None
        self.localToonBobPos: Vec3 | None = None
        self.localToonSpot: DistributedObject | None = None
        self.pondBingoMgr: DistributedObject | None = None
        self.visitedSpots: dict[int, DistributedObject] = {}

    def disable(self):
        self.visitedSpots.clear()
        self.stopCheckingTargets()
        DistributedObject.disable(self)

    def setArea(self, area: int):
        self.area = area

    def getArea(self) -> int:
        return self.area

    def addTarget(self, target: DistributedObject):
        self.notify.debug('addTarget: %s' % target)
        self.targets[target.getDoId()] = target

    def removeTarget(self, target: DistributedObject):
        self.notify.debug('removeTarget: %s' % target)
        del self.targets[target.getDoId()]

    def startCheckingTargets(self, spot: DistributedObject, bobPos: Vec3):
        self.notify.debug('startCheckingTargets')
        self.localToonSpot = spot
        self.localToonBobPos = bobPos
        taskMgr.doMethodLater(self.pollInterval * 2, self.checkTargets, self.taskName('checkTargets'))

    def stopCheckingTargets(self):
        self.notify.debug('stopCheckingTargets')
        taskMgr.remove(self.taskName('checkTargets'))
        if not base.wantBingo:
            self.localToonSpot = None
        self.localToonBobPos = None

    def checkTargets(self, task: Union[Task.Task, None] = None) -> Task.done:
        self.notify.debug('checkTargets')
        if self.localToonSpot != None:
            for target in list(self.targets.values()):
                targetPos = target.getPos(render)
                distVec = Vec3(targetPos - self.localToonBobPos)
                dist = distVec.length()
                if dist < target.getRadius():
                    targetDoId = target.getDoId()
                    self.notify.debug('checkTargets: hit target: %s' % targetDoId)
                    self.d_hitTarget(targetDoId)
                    return Task.done

            taskMgr.doMethodLater(self.pollInterval, self.checkTargets, self.taskName('checkTargets'))
        else:
            self.notify.warning('localToonSpot became None while checking targets')
        return Task.done

    def d_hitTarget(self, targetDoId: int):
        self.localToonSpot.hitTarget(targetDoId)

    def setPondBingoManager(self, pondBingoMgr: DistributedObject):
        self.pondBingoMgr = pondBingoMgr

    def removePondBingoManager(self):
        del self.pondBingoMgr
        self.pondBingoMgr = None

    def getPondBingoManager(self) -> DistributedObject:
        return self.pondBingoMgr

    def hasPondBingoManager(self) -> bool:
        return (self.pondBingoMgr and [1] or [0])[0]

    def handleBingoCatch(self, catch: tuple[int, int]):
        if self.pondBingoMgr:
            self.pondBingoMgr.setLastCatch(catch)

    def handleBingoBoot(self):
        if self.pondBingoMgr:
            self.pondBingoMgr.handleBoot()

    def cleanupBingoMgr(self):
        if self.pondBingoMgr:
            self.pondBingoMgr.cleanup()

    def setLocalToonSpot(self, spot: Union[DistributedObject, None] = None):
        self.localToonSpot = spot
        if spot is not None and spot.getDoId() not in self.visitedSpots:
            self.visitedSpots[spot.getDoId()] = spot

    def showBingoGui(self):
        if self.pondBingoMgr:
            self.pondBingoMgr.showCard()

    def getLocalToonSpot(self) -> DistributedObject:
        return self.localToonSpot

    def resetSpotGui(self):
        for spot in list(self.visitedSpots.values()):
            spot.resetCastGui()

    def setSpotGui(self):
        for spot in list(self.visitedSpots.values()):
            spot.setCastGui()
