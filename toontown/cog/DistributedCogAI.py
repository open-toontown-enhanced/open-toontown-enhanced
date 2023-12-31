from otp.ai.AIBaseGlobal import *
from panda3d.core import *
from panda3d.toontown import *
from direct.distributed.ClockDelta import *
from otp.avatar import DistributedAvatarAI
from . import CogTimings
from direct.task import Task
from . import CogPlannerBase, CogBase, CogDialog, CogDNA
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import CogBattleGlobals
from toontown.building import FADoorCodes
from . import DistributedCogBaseAI
from toontown.hood import ZoneUtil
import random

class DistributedCogAI(DistributedCogBaseAI.DistributedCogBaseAI):
    COG_BUILDINGS = simbase.config.GetBool('want-cog-buildings', 1)
    DEBUG_COG_POSITIONS = simbase.config.GetBool('debug-cog-positions', 0)
    UPDATE_TIMESTAMP_INTERVAL = 180.0
    myId = 0
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogAI')

    def __init__(self, air, cogPlanner):
        DistributedCogBaseAI.DistributedCogBaseAI.__init__(self, air, cogPlanner)
        self.bldgTrack = None
        self.branchId = None
        if cogPlanner:
            self.branchId = cogPlanner.zoneId
        self.pathEndpointStart = 0
        self.pathEndpointEnd = 0
        self.minPathLen = 0
        self.maxPathLen = 0
        self.pathPositionIndex = 0
        self.pathPositionTimestamp = 0.0
        self.pathState = 0
        self.currentLeg = 0
        self.legType = SuitLeg.TOff
        self.flyInCog = 0
        self.buildingCog = 0
        self.attemptingTakeover = 0
        self.takeoverIsCogdo = False
        self.buildingDestination = None
        self.buildingDestinationIsCogdo = False
        return

    def stopTasks(self):
        taskMgr.remove(self.taskName('flyAwayNow'))
        taskMgr.remove(self.taskName('danceNowFlyAwayLater'))
        taskMgr.remove(self.taskName('move'))

    def pointInMyPath(self, point, elapsedTime):
        if self.pathState != 1:
            return 0
        then = globalClock.getFrameTime() + elapsedTime
        elapsed = then - self.pathStartTime
        if not self.sp:
            pass
        return self.legList.isPointInRange(point, elapsed - self.sp.PATH_COLLISION_BUFFER, elapsed + self.sp.PATH_COLLISION_BUFFER)

    def requestBattle(self, x, y, z, h, p, r):
        toonId = self.air.getAvatarIdFromSender()
        if self.air.doId2do.get(toonId) == None:
            return
        if self.pathState == 3:
            pass
        else:
            if self.pathState != 1:
                if self.notify.getDebug():
                    self.notify.debug('requestBattle() - cog %d not on path' % self.getDoId())
                if self.pathState == 2 or self.pathState == 4:
                    self.b_setBrushOff(CogDialog.getBrushOffIndex(self.getStyleName()))
                self.d_denyBattle(toonId)
                return
            else:
                if self.legType != SuitLeg.TWalk:
                    if self.notify.getDebug():
                        self.notify.debug('requestBattle() - cog %d not in Bellicose' % self.getDoId())
                    self.b_setBrushOff(CogDialog.getBrushOffIndex(self.getStyleName()))
                    self.d_denyBattle(toonId)
                    return
        self.confrontPos = Point3(x, y, z)
        self.confrontHpr = Vec3(h, p, r)
        if self.sp.requestBattle(self.zoneId, self, toonId):
            if self.notify.getDebug():
                self.notify.debug('Cog %d requesting battle in zone %d' % (self.getDoId(), self.zoneId))
        else:
            if self.notify.getDebug():
                self.notify.debug('requestBattle from cog %d - denied by battle manager' % self.getDoId())
            self.b_setBrushOff(CogDialog.getBrushOffIndex(self.getStyleName()))
            self.d_denyBattle(toonId)
        return

    def getConfrontPosHpr(self):
        return (
         self.confrontPos, self.confrontHpr)

    def flyAwayNow(self):
        self.b_setPathState(2)
        self.stopPathNow()
        name = self.taskName('flyAwayNow')
        taskMgr.remove(name)
        taskMgr.doMethodLater(CogTimings.toSky, self.finishFlyAwayNow, name)

    def danceNowFlyAwayLater(self):
        self.b_setPathState(4)
        self.stopPathNow()
        name = self.taskName('danceNowFlyAwayLater')
        taskMgr.remove(name)
        taskMgr.doMethodLater(CogTimings.victoryDance + CogTimings.toSky, self.finishFlyAwayNow, name)

    def finishFlyAwayNow(self, task):
        self.notify.debug('Cog %s finishFlyAwayNow' % self.doId)
        self.requestRemoval()
        return Task.done

    def d_setSPDoId(self, doId):
        self.sendUpdate('setSPDoId', [doId])

    def getSPDoId(self):
        if self.sp:
            return self.sp.getDoId()
        else:
            return 0

    def releaseControl(self):
        self.b_setPathState(0)

    def b_setPathEndpoints(self, start, end, minPathLen, maxPathLen):
        self.setPathEndpoints(start, end, minPathLen, maxPathLen)
        self.d_setPathEndpoints(start, end, minPathLen, maxPathLen)

    def d_setPathEndpoints(self, start, end, minPathLen, maxPathLen):
        self.sendUpdate('setPathEndpoints', [start, end, minPathLen, maxPathLen])

    def setPathEndpoints(self, start, end, minPathLen, maxPathLen):
        self.pathEndpointStart = start
        self.pathEndpointEnd = end
        self.minPathLen = minPathLen
        self.maxPathLen = maxPathLen

    def getPathEndpoints(self):
        return (
         self.pathEndpointStart, self.pathEndpointEnd, self.minPathLen, self.maxPathLen)

    def b_setPathPosition(self, index, timestamp):
        self.setPathPosition(index, timestamp)
        self.d_setPathPosition(index, timestamp)

    def d_setPathPosition(self, index, timestamp):
        self.notify.debug('Cog %d reaches point %d at time %0.2f' % (self.getDoId(), index, timestamp))
        self.sendUpdate('setPathPosition', [index, globalClockDelta.localToNetworkTime(timestamp)])

    def setPathPosition(self, index, timestamp):
        self.pathPositionIndex = index
        self.pathPositionTimestamp = timestamp

    def getPathPosition(self):
        return (
         self.pathPositionIndex, globalClockDelta.localToNetworkTime(self.pathPositionTimestamp))

    def b_setPathState(self, state):
        self.setPathState(state)
        self.d_setPathState(state)

    def d_setPathState(self, state):
        self.sendUpdate('setPathState', [state])

    def setPathState(self, state):
        if self.pathState != state:
            self.pathState = state
            if state == 0:
                self.stopPathNow()
            elif state == 1:
                self.moveToNextLeg(None)
            elif state == 2:
                self.stopPathNow()
            elif state == 3:
                pass
            elif state == 4:
                self.stopPathNow()
            else:
                self.notify.error('Invalid state: ' + str(state))
        return

    def getPathState(self):
        return self.pathState

    def d_debugCogPosition(self, elapsed, currentLeg, x, y, timestamp):
        timestamp = globalClockDelta.localToNetworkTime(timestamp)
        self.sendUpdate('debugCogPosition', [
         elapsed, currentLeg, x, y, timestamp])

    def initializePath(self):
        self.makeLegList()
        if self.notify.getDebug():
            self.notify.debug('Leg list:')
            print(self.legList)
        idx1 = self.startPoint.getIndex()
        idx2 = self.endPoint.getIndex()
        self.pathStartTime = globalClock.getFrameTime()
        self.setPathEndpoints(idx1, idx2, self.minPathLen, self.maxPathLen)
        self.setPathPosition(0, self.pathStartTime)
        self.pathState = 1
        self.currentLeg = 0
        self.zoneId = ZoneUtil.getTrueZoneId(self.legList.getZoneId(0), self.branchId)
        self.legType = self.legList.getType(0)
        if self.notify.getDebug():
            self.notify.debug('creating cog in zone %d' % self.zoneId)

    def resync(self):
        self.b_setPathPosition(self.currentLeg, self.pathStartTime + self.legList.getStartTime(self.currentLeg))

    def moveToNextLeg(self, task):
        now = globalClock.getFrameTime()
        elapsed = now - self.pathStartTime
        nextLeg = self.legList.getLegIndexAtTime(elapsed, self.currentLeg)
        numLegs = self.legList.getNumLegs()
        if self.currentLeg != nextLeg:
            self.currentLeg = nextLeg
            self.__beginLegType(self.legList.getType(nextLeg))
            zoneId = self.legList.getZoneId(nextLeg)
            zoneId = ZoneUtil.getTrueZoneId(zoneId, self.branchId)
            self.__enterZone(zoneId)
            self.notify.debug('Cog %d reached leg %d of %d in zone %d.' % (self.getDoId(), nextLeg, numLegs - 1, self.zoneId))
            if self.DEBUG_COG_POSITIONS:
                leg = self.legList.getLeg(nextLeg)
                pos = leg.getPosAtTime(elapsed - leg.getStartTime())
                self.d_debugCogPosition(elapsed, nextLeg, pos[0], pos[1], now)
        if now - self.pathPositionTimestamp > self.UPDATE_TIMESTAMP_INTERVAL:
            self.resync()
        if self.pathState != 1:
            return Task.done
        nextLeg += 1
        while nextLeg + 1 < numLegs and self.legList.getZoneId(nextLeg) == ZoneUtil.getCanonicalZoneId(self.zoneId) and self.legList.getType(nextLeg) == self.legType:
            nextLeg += 1

        if nextLeg < numLegs:
            nextTime = self.legList.getStartTime(nextLeg)
            delay = nextTime - elapsed
            taskMgr.remove(self.taskName('move'))
            taskMgr.doMethodLater(delay, self.moveToNextLeg, self.taskName('move'))
        else:
            if self.attemptingTakeover:
                self.startTakeOver()
            self.requestRemoval()
        return Task.done

    def stopPathNow(self):
        taskMgr.remove(self.taskName('move'))

    def __enterZone(self, zoneId):
        if zoneId != self.zoneId:
            self.sp.zoneChange(self, self.zoneId, zoneId)
            self.air.sendSetZone(self, zoneId)
            self.zoneId = zoneId
            if self.pathState == 1:
                self.sp.checkForBattle(zoneId, self)

    def __beginLegType(self, legType):
        self.legType = legType
        if legType == SuitLeg.TWalkFromStreet:
            self.checkBuildingState()
        else:
            if legType == SuitLeg.TToToonBuilding:
                self.openToonDoor()
            else:
                if legType == SuitLeg.TToSuitBuilding:
                    self.openCogDoor()
                else:
                    if legType == SuitLeg.TToCoghq:
                        self.openCogHQDoor(1)
                    else:
                        if legType == SuitLeg.TFromCoghq:
                            self.openCogHQDoor(0)

    def resume(self):
        self.notify.debug('Cog %s resume' % self.doId)
        if self.currHP <= 0:
            self.notify.debug('Cog %s dead after resume' % self.doId)
            self.requestRemoval()
        else:
            self.danceNowFlyAwayLater()

    def prepareToJoinBattle(self):
        self.b_setPathState(0)

    def interruptMove(self):
        CogBase.CogBase.interruptMove(self)

    def checkBuildingState(self):
        blockNumber = self.buildingDestination
        if blockNumber == None:
            return
        building = self.sp.buildingMgr.getBuilding(blockNumber)
        if self.attemptingTakeover:
            if not building.isToonBlock():
                self.flyAwayNow()
                return
            if not hasattr(building, 'door'):
                self.flyAwayNow()
                return
            building.door.setDoorLock(FADoorCodes.COG_APPROACHING)
        else:
            if not building.isCogBlock():
                self.flyAwayNow()
        return

    def openToonDoor(self):
        blockNumber = self.buildingDestination
        building = self.sp.buildingMgr.getBuilding(blockNumber)
        if not building.isToonBlock():
            self.flyAwayNow()
            return
        if not hasattr(building, 'door'):
            self.flyAwayNow()
            return
        building.door.requestCogEnter(self.getDoId())

    def openCogDoor(self):
        blockNumber = self.buildingDestination
        building = self.sp.buildingMgr.getBuilding(blockNumber)
        if not building.isCogBlock():
            self.flyAwayNow()
            return

    def openCogHQDoor(self, enter):
        blockNumber = self.legList.getBlockNumber(self.currentLeg)
        try:
            door = self.sp.cogHQDoors[blockNumber]
        except:
            self.notify.error('No CogHQ door %s in zone %s' % (blockNumber, self.sp.zoneId))
            return

        if enter:
            door.requestCogEnter(self.getDoId())
        else:
            door.requestCogExit(self.getDoId())

    def startTakeOver(self):
        if not self.COG_BUILDINGS:
            return
        blockNumber = self.buildingDestination
        if not self.sp.buildingMgr.isCogBlock(blockNumber):
            self.notify.debug('Cog %d taking over building %d in %d' % (self.getDoId(), blockNumber, self.zoneId))
            difficulty = self.getActualLevel() - 1
            dept = CogDNA.getCogDept(self.dna.name)
            if self.buildingDestinationIsCogdo:
                self.sp.cogdoTakeOver(blockNumber, dept, difficulty, self.buildingHeight)
            else:
                self.sp.cogTakeOver(blockNumber, dept, difficulty, self.buildingHeight)
