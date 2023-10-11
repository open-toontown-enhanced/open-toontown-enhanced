from panda3d.toontown import *
from otp.ai.AIBaseGlobal import *
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from .CogPlannerBase import CogPlannerBase
from .DistributedCogAI import DistributedCogAI
from toontown.battle import BattleManagerAI
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from . import CogDNA
from toontown.battle import CogBattleGlobals
from . import CogTimings
from toontown.toon import NPCToons
from toontown.building import HQBuildingAI
from toontown.hood import ZoneUtil
from toontown.building import CogBuildingGlobals
from toontown.building.DistributedBuildingAI import DistributedBuildingAI
from toontown.building.DistributedBuildingMgrAI import DistributedBuildingMgrAI
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import ToontownGlobals
from toontown.coghq.DistributedCogHQDoorAI import DistributedCogHQDoorAI
import math, time, random

class DistributedCogPlannerAI(DistributedObjectAI, CogPlannerBase):
    CogdoPopFactor = config.GetFloat('cogdo-pop-factor', 1.5)
    CogdoRatio = min(1.0, max(0.0, config.GetFloat('cogdo-ratio', 0.5)))
    MinimumOfOne = config.GetBool('minimum-of-one-building', 0)
    MAX_COG_TYPES = 6
    POP_UPKEEP_DELAY = 10
    POP_ADJUST_DELAY = 300
    PATH_COLLISION_BUFFER = 5
    TOTAL_MAX_COGS = 50
    MIN_PATH_LEN = 40
    MAX_PATH_LEN = 300
    MIN_TAKEOVER_PATH_LEN = 2
    COGS_ENTER_BUILDINGS = 1
    COG_BUILDING_NUM_COGS = 1.5
    COG_BUILDING_TIMEOUT = [
     None, None, None, None, None, None, 72, 60, 48, 36, 24, 12, 6, 3, 1, 0.5]
    TOTAL_COG_BUILDING_PCT = 18 * CogdoPopFactor
    BUILDING_HEIGHT_DISTRIBUTION = [
     14, 18, 25, 23, 20]

    defaultCogName = simbase.config.GetString('cog-type', 'random')
    if defaultCogName == 'random':
        defaultCogName = None
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogPlannerAI')

    def __init__(self, air, zoneId: int):
        DistributedObjectAI.__init__(self, air)
        CogPlannerBase.__init__(self)
        self.air = air
        self.zoneId: int = zoneId
        self.canonicalZoneId: int = ZoneUtil.getCanonicalZoneId(zoneId)
        if simbase.air.wantCogdominiums:
            if not hasattr(self.__class__, 'CogdoPopAdjusted'):
                self.__class__.CogdoPopAdjusted = True
                for index in range(len(self.CogHoodInfo)):
                    hoodInfo = self.CogHoodInfo[index]
                    hoodInfo[self.COG_HOOD_INFO_BMIN] = int(0.5 + self.CogdoPopFactor * hoodInfo[self.COG_HOOD_INFO_BMIN])
                    hoodInfo[self.COG_HOOD_INFO_BMAX] = int(0.5 + self.CogdoPopFactor * hoodInfo[self.COG_HOOD_INFO_BMAX])

        self.hoodInfoIdx: int = -1
        for index in range(len(self.CogHoodInfo)):
            currHoodInfo = self.CogHoodInfo[index]
            if currHoodInfo[self.COG_HOOD_INFO_ZONE] == self.canonicalZoneId:
                self.hoodInfoIdx = index

        self.currDesired: int | None = None
        self.baseNumCogs = (self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_MIN] + self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_MAX]) // 2
        self.targetNumCogdos = 0
        if simbase.air.wantCogdominiums:
            self.targetNumCogdos = int(0.5 + self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_BMIN] * self.CogdoRatio)
            if self.MinimumOfOne:
                self.targetNumCogdos = max(self.targetNumCogdos, 1)
        self.targetNumCogBuildings: int = self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_BMIN]
        self.targetNumCogBuildings -= self.targetNumCogdos
        if self.MinimumOfOne:
            self.targetNumCogBuildings = max(self.targetNumCogBuildings, 1)
        if ZoneUtil.isWelcomeValley(self.zoneId):
            self.targetNumCogdos = 0
            self.targetNumCogBuildings = 0
        self.pendingBuildingTracks: list[str] = []
        self.pendingBuildingHeights: list[int] = []
        self.pendingCogdoHeights: list[int] = []
        self.cogList: DistributedCogAI = []
        self.numFlyInCogs: int = 0
        self.numBuildingCogs: int = 0
        self.numAttemptingTakeover: int = 0
        self.numAttemptingCogdoTakeover: int = 0
        self.zoneInfo: dict[int, DistributedCogAI] = {}
        self.zoneIdToPointMap: dict[int, DNASuitPoint] = None
        self.cogHQDoors: DistributedCogHQDoorAI = []
        self.battleMgr = BattleManagerAI.BattleManagerAI(self.air)
        self.setupDNA()
        if self.notify.getDebug():
            self.notify.debug('Creating a building manager AI in zone' + str(self.zoneId))
        self.buildingMgr: DistributedBuildingMgrAI = self.air.buildingManagers.get(self.zoneId)
        if self.buildingMgr:
            blocks, hqBlocks, gagshopBlocks, petshopBlocks, kartshopBlocks, animBldgBlocks = self.buildingMgr.getDNABlockLists()
            for currBlock in blocks:
                bldg = self.buildingMgr.getBuilding(currBlock)
                bldg.setCogPlannerExt(self)

            for currBlock in animBldgBlocks:
                bldg = self.buildingMgr.getBuilding(currBlock)
                bldg.setCogPlannerExt(self)

        self.dnaStore.resetBlockNumbers()
        self.initBuildingsAndPoints()
        numCogs = simbase.config.GetInt('cog-count', -1)
        if numCogs >= 0:
            self.currDesired = numCogs
        cogHood = simbase.config.GetInt('cogs-only-in-hood', -1)
        if cogHood >= 0:
            if self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_ZONE] != cogHood:
                self.currDesired = 0
        self.cogCountAdjust: int = 0

    def cleanup(self):
        taskMgr.remove(self.taskName('sptUpkeepPopulation'))
        taskMgr.remove(self.taskName('sptAdjustPopulation'))
        for cog in self.cogList:
            cog.stopTasks()
            if cog.isGenerated():
                self.zoneChange(cog, cog.zoneId)
                cog.requestDelete()

        self.cogList = []
        self.numFlyInCogs = 0
        self.numBuildingCogs = 0
        self.numAttemptingTakeover = 0
        self.numAttemptingCogdoTakeover = 0

    def delete(self):
        self.cleanup()
        DistributedObjectAI.delete(self)

    def initBuildingsAndPoints(self):
        if not self.buildingMgr:
            return
        if self.notify.getDebug():
            self.notify.debug('Initializing building points')
        self.buildingFrontDoors = {}
        self.buildingSideDoors = {}
        for p in self.frontdoorPointList:
            blockNumber = p.getLandmarkBuildingIndex()
            if p.getPointType() < 0:
                self.notify.warning('No landmark building for (%s) in zone %d' % (repr(p), self.zoneId))
            elif blockNumber in self.buildingFrontDoors:
                self.notify.warning('Multiple front doors for building %d in zone %d' % (blockNumber, self.zoneId))
            else:
                self.buildingFrontDoors[blockNumber] = p

        for p in self.sidedoorPointList:
            blockNumber = p.getLandmarkBuildingIndex()
            if p.getPointType() < 0:
                self.notify.warning('No landmark building for (%s) in zone %d' % (repr(p), self.zoneId))
            elif blockNumber in self.buildingSideDoors:
                self.buildingSideDoors[blockNumber].append(p)
            else:
                self.buildingSideDoors[blockNumber] = [
                 p]

        for bldg in self.buildingMgr.getBuildings():
            if isinstance(bldg, HQBuildingAI.HQBuildingAI):
                continue
            blockNumber = bldg.getBlock()[0]
            if blockNumber not in self.buildingFrontDoors:
                self.notify.warning('No front door for building %d in zone %d' % (blockNumber, self.zoneId))
            if blockNumber not in self.buildingSideDoors:
                self.notify.warning('No side door for building %d in zone %d' % (blockNumber, self.zoneId))

    def countNumCogsPerTrack(self, count: int):
        for cog in self.cogList:
            if cog.track in count:
                count[cog.track] += 1
            else:
                count[cog.track] = 1

    def countNumBuildingsPerTrack(self, count: int):
        if self.buildingMgr:
            for building in self.buildingMgr.getBuildings():
                if building.isCogBuilding():
                    if building.track in count:
                        count[building.track] += 1
                    else:
                        count[building.track] = 1

    def countNumBuildingsPerHeight(self, count: int):
        if self.buildingMgr:
            for building in self.buildingMgr.getBuildings():
                if building.isCogBuilding():
                    height = building.numFloors - 1
                    if height in count:
                        count[height] += 1
                    else:
                        count[height] = 1

    def formatNumCogsPerTrack(self, count: int) -> str:
        result = ' '
        for track, num in list(count.items()):
            result += ' %s:%d' % (track, num)

        return result[2:]

    def calcDesiredNumFlyInCogs(self) -> int:
        if self.currDesired != None:
            return 0
        return self.baseNumCogs + self.cogCountAdjust

    def calcDesiredNumBuildingCogs(self) -> int:
        if self.currDesired != None:
            return self.currDesired
        if not self.buildingMgr:
            return 0
        cogBuildings = self.buildingMgr.getEstablishedCogBlocks()
        return int(len(cogBuildings) * self.COG_BUILDING_NUM_COGS)

    def getZoneIdToPointMap(self) -> dict[int, DNASuitPoint]:
        if self.zoneIdToPointMap != None:
            return self.zoneIdToPointMap
        self.zoneIdToPointMap = {}
        for point in self.streetPointList:
            points = self.dnaStore.getAdjacentPoints(point)
            i = points.getNumPoints() - 1
            while i >= 0:
                pi = points.getPointIndex(i)
                p = self.pointIndexes[pi]
                i -= 1
                zoneName = self.dnaStore.getSuitEdgeZone(point.getIndex(), p.getIndex())
                zoneId = int(self.extractGroupName(zoneName))
                if zoneId in self.zoneIdToPointMap:
                    self.zoneIdToPointMap[zoneId].append(point)
                else:
                    self.zoneIdToPointMap[zoneId] = [point]

        return self.zoneIdToPointMap

    def getStreetPointsForBuilding(self, blockNumber: int) -> list[DNASuitPoint]:
        pointList = []
        if blockNumber in self.buildingSideDoors:
            for doorPoint in self.buildingSideDoors[blockNumber]:
                points = self.dnaStore.getAdjacentPoints(doorPoint)
                i = points.getNumPoints() - 1
                while i >= 0:
                    pi = points.getPointIndex(i)
                    point = self.pointIndexes[pi]
                    if point.getPointType() == DNASuitPoint.STREETPOINT:
                        pointList.append(point)
                    i -= 1

        if blockNumber in self.buildingFrontDoors:
            doorPoint = self.buildingFrontDoors[blockNumber]
            points = self.dnaStore.getAdjacentPoints(doorPoint)
            i = points.getNumPoints() - 1
            while i >= 0:
                pi = points.getPointIndex(i)
                pointList.append(self.pointIndexes[pi])
                i -= 1

        return pointList

    def createNewCog(self, blockNumbers: list[int], streetPoints: list[DNASuitPoint], toonBlockTakeover: int = None, cogdoTakeover: bool= None,
                      minPathLen: int = None, maxPathLen: int = None, buildingHeight: int = None, cogLevel: int = None, cogType: int = None,
                      cogTrack: str= None, cogName: str = None, skelecog: bool = None, revives: int = None):
        startPoint = None
        blockNumber = None
        if self.notify.getDebug():
            self.notify.debug('Choosing origin from %d+%d possibles.' % (len(streetPoints), len(blockNumbers)))
        while startPoint == None and len(blockNumbers) > 0:
            bn = random.choice(blockNumbers)
            blockNumbers.remove(bn)
            if bn in self.buildingSideDoors:
                for doorPoint in self.buildingSideDoors[bn]:
                    points = self.dnaStore.getAdjacentPoints(doorPoint)
                    i = points.getNumPoints() - 1
                    while blockNumber == None and i >= 0:
                        pi = points.getPointIndex(i)
                        p = self.pointIndexes[pi]
                        i -= 1
                        startTime = CogTimings.fromCogBuilding
                        startTime += self.dnaStore.getSuitEdgeTravelTime(doorPoint.getIndex(), pi, self.cogWalkSpeed)
                        if not self.pointCollision(p, doorPoint, startTime):
                            startTime = CogTimings.fromCogBuilding
                            startPoint = doorPoint
                            blockNumber = bn

        while startPoint == None and len(streetPoints) > 0:
            p = random.choice(streetPoints)
            streetPoints.remove(p)
            if not self.pointCollision(p, None, CogTimings.fromSky):
                startPoint = p
                startTime = CogTimings.fromSky

        if startPoint == None:
            return
        newCog = DistributedCogAI(simbase.air, self)
        newCog.startPoint = startPoint
        if blockNumber != None:
            newCog.buildingCog = 1
            if cogTrack == None:
                cogTrack = self.buildingMgr.getBuildingTrack(blockNumber)
        else:
            newCog.flyInCog = 1
            newCog.attemptingTakeover = self.newCogShouldAttemptTakeover()
            if newCog.attemptingTakeover:
                cogdosNeeded = self.countNumNeededCogdos()
                bldgsNeeded = self.countNumNeededBuildings()
                cogdosAvailable = cogdosNeeded - self.numAttemptingCogdoTakeover
                bldgsAvailable = bldgsNeeded - (self.numAttemptingTakeover - self.numAttemptingCogdoTakeover)
                totalAvailable = cogdosAvailable + bldgsAvailable
                if cogdoTakeover is None:
                    cogdoTakeover = False
                    if simbase.air.wantCogdominiums:
                        if totalAvailable > 0:
                            r = random.randrange(totalAvailable)
                            if r < cogdosAvailable:
                                cogdoTakeover = True
                newCog.takeoverIsCogdo = cogdoTakeover
                if newCog.takeoverIsCogdo:
                    pendingTracks = [
                     's']
                    pendingHeights = self.pendingCogdoHeights
                else:
                    pendingTracks = self.pendingBuildingTracks
                    pendingHeights = self.pendingBuildingHeights
                if cogTrack == None and len(pendingTracks) > 0:
                    cogTrack = pendingTracks[0]
                    del pendingTracks[0]
                    pendingTracks.append(cogTrack)
                if buildingHeight == None and len(pendingHeights) > 0:
                    buildingHeight = pendingHeights[0]
                    del pendingHeights[0]
                    pendingHeights.append(buildingHeight)
            else:
                if cogdoTakeover and cogTrack == None:
                    cogTrack = random.choice(['s'])
        if cogName == None:
            if not cogdoTakeover:
                cogName, skelecog = self.air.cogInvasionManager.getInvadingCog()
                self.air.cogInvasionManager.subtractNumCogsRemaining(1)
            if cogName == None:
                cogName = self.defaultCogName
        if cogType == None and cogName != None:
            cogType = CogDNA.getCogType(cogName)
            cogTrack = CogDNA.getCogDept(cogName)
        if cogLevel == None and buildingHeight != None:
            if not cogdoTakeover:
                cogLevel = self.chooseCogLevel(self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_LVL], buildingHeight)
            else:
                cogLevel = self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_LVL][-1] + 1
        cogLevel, cogType, cogTrack = self.pickLevelTypeAndTrack(cogLevel, cogType, cogTrack)
        newCog.setupCogDNA(cogLevel, cogType, cogTrack)
        newCog.buildingHeight = buildingHeight
        gotDestination = self.chooseDestination(newCog, startTime, toonBlockTakeover=toonBlockTakeover, cogdoTakeover=cogdoTakeover, minPathLen=minPathLen, maxPathLen=maxPathLen)
        if not gotDestination:
            self.notify.debug("Couldn't get a destination in %d!" % self.zoneId)
            newCog.doNotDeallocateChannel = None
            newCog.delete()
            return
        newCog.initializePath()
        self.zoneChange(newCog, None, newCog.zoneId)
        if skelecog:
            newCog.setSkelecog(skelecog)
        if revives:
            newCog.setSkeleRevives(revives)
        newCog.generateWithRequired(newCog.zoneId)
        newCog.moveToNextLeg(None)
        self.cogList.append(newCog)
        if newCog.flyInCog:
            self.numFlyInCogs += 1
        if newCog.buildingCog:
            self.numBuildingCogs += 1
        if newCog.attemptingTakeover:
            self.numAttemptingTakeover += 1
            if newCog.takeoverIsCogdo:
                self.numAttemptingCogdoTakeover += 1
        return newCog

    def countNumNeededBuildings(self) -> int:
        if not self.buildingMgr:
            return 0
        numCogBuildings = len(self.buildingMgr.getCogBlocks()) - len(self.buildingMgr.getCogdoBlocks())
        numNeeded = self.targetNumCogBuildings - numCogBuildings
        return numNeeded

    def countNumNeededCogdos(self) -> int:
        if not self.buildingMgr:
            return 0
        numCogdos = len(self.buildingMgr.getCogdoBlocks())
        numNeeded = self.targetNumCogdos - numCogdos
        return numNeeded

    def newCogShouldAttemptTakeover(self) -> bool:
        if not self.COGS_ENTER_BUILDINGS:
            return False
        numNeeded = self.countNumNeededBuildings()
        if simbase.air.wantCogdominiums:
            numNeeded += self.countNumNeededCogdos()
        if self.numAttemptingTakeover >= numNeeded:
            self.pendingBuildingTracks = []
            return False
        self.notify.debug('DSP %d is planning a takeover attempt in zone %d' % (self.getDoId(), self.zoneId))
        return True

    def chooseDestination(self, cog: DistributedCogAI, startTime: float, toonBlockTakeover: int = None,
                          cogdoTakeover: bool = None, minPathLen: int = None, maxPathLen: int= None) -> bool:
        possibles = []
        backup = []
        if cogdoTakeover is None:
            cogdoTakeover = False
        if toonBlockTakeover != None:
            cog.attemptingTakeover = 1
            blockNumber = toonBlockTakeover
            if blockNumber in self.buildingFrontDoors:
                possibles.append((blockNumber, self.buildingFrontDoors[blockNumber]))
        elif cog.attemptingTakeover:
            for blockNumber in self.buildingMgr.getToonBlocks():
                building = self.buildingMgr.getBuilding(blockNumber)
                extZoneId, intZoneId = building.getExteriorAndInteriorZoneId()
                if not NPCToons.isZoneProtected(intZoneId):
                    if blockNumber in self.buildingFrontDoors:
                        possibles.append((blockNumber, self.buildingFrontDoors[blockNumber]))

        else:
            if self.buildingMgr:
                for blockNumber in self.buildingMgr.getCogBlocks():
                    track = self.buildingMgr.getBuildingTrack(blockNumber)
                    if track == cog.track and blockNumber in self.buildingSideDoors:
                        for doorPoint in self.buildingSideDoors[blockNumber]:
                            possibles.append((blockNumber, doorPoint))

            backup = []
            for p in self.streetPointList:
                backup.append((None, p))

        if self.notify.getDebug():
            self.notify.debug('Choosing destination point from %d+%d possibles.' % (len(possibles), len(backup)))
        if len(possibles) == 0:
            possibles = backup
            backup = []
        if minPathLen == None:
            if cog.attemptingTakeover:
                minPathLen = self.MIN_TAKEOVER_PATH_LEN
            else:
                minPathLen = self.MIN_PATH_LEN
        if maxPathLen == None:
            maxPathLen = self.MAX_PATH_LEN
        retryCount = 0
        while len(possibles) > 0 and retryCount < 50:
            p = random.choice(possibles)
            possibles.remove(p)
            if len(possibles) == 0:
                possibles = backup
                backup = []
            path = self.genPath(cog.startPoint, p[1], minPathLen, maxPathLen)
            if path and not self.pathCollision(path, startTime):
                cog.endPoint = p[1]
                cog.minPathLen = minPathLen
                cog.maxPathLen = maxPathLen
                cog.buildingDestination = p[0]
                cog.buildingDestinationIsCogdo = cogdoTakeover
                cog.setPath(path)
                return True
            retryCount += 1

        return False

    def pathCollision(self, path: DNASuitPath, elapsedTime: float) -> bool:
        pathLength = path.getNumPoints()
        i = 0
        pi = path.getPointIndex(i)
        point = self.pointIndexes[pi]
        adjacentPoint = self.pointIndexes[path.getPointIndex(i + 1)]
        while point.getPointType() == DNASuitPoint.FRONTDOORPOINT or point.getPointType() == DNASuitPoint.SIDEDOORPOINT:
            i += 1
            lastPi = pi
            pi = path.getPointIndex(i)
            adjacentPoint = point
            point = self.pointIndexes[pi]
            elapsedTime += self.dnaStore.getSuitEdgeTravelTime(lastPi, pi, self.cogWalkSpeed)

        return self.pointCollision(point, adjacentPoint, elapsedTime)

    def pointCollision(self, point: DNASuitPoint, adjacentPoint: DNASuitPoint, elapsedTime: float) -> bool:
        for cog in self.cogList:
            if cog.pointInMyPath(point, elapsedTime):
                return True

        if adjacentPoint != None:
            return self.battleCollision(point, adjacentPoint)
        else:
            points = self.dnaStore.getAdjacentPoints(point)
            i = points.getNumPoints() - 1
            while i >= 0:
                pi = points.getPointIndex(i)
                p = self.pointIndexes[pi]
                i -= 1
                if self.battleCollision(point, p):
                    return True

        return False

    def battleCollision(self, point: DNASuitPoint, adjacentPoint: DNASuitPoint) -> bool:
        zoneName = self.dnaStore.getSuitEdgeZone(point.getIndex(), adjacentPoint.getIndex())
        zoneId = int(self.extractGroupName(zoneName))
        return self.battleMgr.cellHasBattle(zoneId)

    def removeCog(self, cog: DistributedCogAI):
        self.zoneChange(cog, cog.zoneId)
        if self.cogList.count(cog) > 0:
            self.cogList.remove(cog)
            if cog.flyInCog:
                self.numFlyInCogs -= 1
            if cog.buildingCog:
                self.numBuildingCogs -= 1
            if cog.attemptingTakeover:
                self.numAttemptingTakeover -= 1
                if cog.takeoverIsCogdo:
                    self.numAttemptingCogdoTakeover -= 1
        cog.requestDelete()

    def countTakeovers(self):
        count = 0
        for cog in self.cogList:
            if cog.attemptingTakeover:
                count += 1

        return count

    def countCogdoTakeovers(self):
        count = 0
        for cog in self.cogList:
            if cog.attemptingTakeover and cog.takeoverIsCogdo:
                count += 1

        return count

    def __waitForNextUpkeep(self):
        t = random.random() * 2.0 + self.POP_UPKEEP_DELAY
        taskMgr.doMethodLater(t, self.upkeepCogPopulation, self.taskName('sptUpkeepPopulation'))

    def __waitForNextAdjust(self):
        t = random.random() * 10.0 + self.POP_ADJUST_DELAY
        taskMgr.doMethodLater(t, self.adjustCogPopulation, self.taskName('sptAdjustPopulation'))

    def upkeepCogPopulation(self, task: Task) -> Task.done:
        targetFlyInNum = self.calcDesiredNumFlyInCogs()
        targetFlyInNum = min(targetFlyInNum, self.TOTAL_MAX_COGS - self.numBuildingCogs)
        streetPoints = self.streetPointList[:]
        flyInDeficit = (targetFlyInNum - self.numFlyInCogs + 3) // 4
        while flyInDeficit > 0:
            if not self.createNewCog([], streetPoints):
                break
            flyInDeficit -= 1

        if self.buildingMgr:
            cogBuildings = self.buildingMgr.getEstablishedCogBlocks()
        else:
            cogBuildings = []
        if self.currDesired != None:
            targetBuildingNum = max(0, self.currDesired - self.numFlyInCogs)
        else:
            targetBuildingNum = int(len(cogBuildings) * self.COG_BUILDING_NUM_COGS)
        targetBuildingNum += flyInDeficit
        targetBuildingNum = min(targetBuildingNum, self.TOTAL_MAX_COGS - self.numFlyInCogs)
        buildingDeficit = (targetBuildingNum - self.numBuildingCogs + 3) // 4
        while buildingDeficit > 0:
            if not self.createNewCog(cogBuildings, streetPoints):
                break
            buildingDeficit -= 1

        if self.notify.getDebug() and self.currDesired == None:
            self.notify.debug('zone %d has %d of %d fly-in and %d of %d building cogs.' % (self.zoneId, self.numFlyInCogs, targetFlyInNum, self.numBuildingCogs, targetBuildingNum))
            if buildingDeficit != 0:
                self.notify.debug('remaining deficit is %d.' % buildingDeficit)
        if self.buildingMgr:
            cogBuildings = self.buildingMgr.getEstablishedCogBlocks()
            timeoutIndex = min(len(cogBuildings), len(self.COG_BUILDING_TIMEOUT) - 1)
            timeout = self.COG_BUILDING_TIMEOUT[timeoutIndex]
            if timeout != None:
                timeout *= 3600.0
                oldest = None
                oldestAge = 0
                now = time.time()
                for b in cogBuildings:
                    building = self.buildingMgr.getBuilding(b)
                    if hasattr(building, 'elevator'):
                        if building.elevator.fsm.getCurrentState().getName() == 'waitEmpty':
                            age = now - building.becameCogTime
                            if age > oldestAge:
                                oldest = building
                                oldestAge = age

                if oldestAge > timeout:
                    self.notify.info('Street %d has %d buildings; reclaiming %0.2f-hour-old building.' % (self.zoneId, len(cogBuildings), oldestAge / 3600.0))
                    oldest.b_setVictorList([0, 0, 0, 0])
                    oldest.updateSavedBy([])
                    oldest.toonTakeOver()
        self.__waitForNextUpkeep()
        return Task.done

    def adjustCogPopulation(self, task: Task) -> Task.done:
        hoodInfo = self.CogHoodInfo[self.hoodInfoIdx]
        if hoodInfo[self.COG_HOOD_INFO_MAX] == 0:
            self.__waitForNextAdjust()
            return Task.done
        min = hoodInfo[self.COG_HOOD_INFO_MIN]
        max = hoodInfo[self.COG_HOOD_INFO_MAX]
        adjustment = random.choice((-2, -1, -1, 0, 0, 0, 1, 1, 2))
        self.cogCountAdjust += adjustment
        desiredNum = self.calcDesiredNumFlyInCogs()
        if desiredNum < min:
            self.cogCountAdjust = min - self.baseNumCogs
        else:
            if desiredNum > max:
                self.cogCountAdjust = max - self.baseNumCogs
        self.__waitForNextAdjust()
        return Task.done

    def cogTakeOver(self, blockNumber: int, cogTrack: str, difficulty: int, buildingHeight: int):
        if self.pendingBuildingTracks.count(cogTrack) > 0:
            self.pendingBuildingTracks.remove(cogTrack)
        if self.pendingBuildingHeights.count(buildingHeight) > 0:
            self.pendingBuildingHeights.remove(buildingHeight)
        building = self.buildingMgr.getBuilding(blockNumber)
        building.cogTakeOver(cogTrack, difficulty, buildingHeight)

    def cogdoTakeOver(self, blockNumber: int, cogTrack: str, difficulty: int, buildingHeight: int):
        if self.pendingCogdoHeights.count(buildingHeight) > 0:
            self.pendingCogdoHeights.remove(buildingHeight)
        building = self.buildingMgr.getBuilding(blockNumber)
        building.cogdoTakeOver(cogTrack, difficulty, buildingHeight)

    def recycleBuilding(self, isCogdo: bool):
        bmin = self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_BMIN]
        current = len(self.buildingMgr.getCogBlocks())
        target = self.targetNumCogBuildings + self.targetNumCogdos
        if target > bmin and current <= target:
            if isCogdo:
                if self.targetNumCogdos > choice(self.MinimumOfOne, 1, 0):
                    self.targetNumCogdos -= 1
                    self.assignCogdos(1)
            elif self.targetNumCogBuildings > choice(self.MinimumOfOne, 1, 0):
                self.targetNumCogBuildings -= 1
                self.assignCogBuildings(1)

    def assignInitialCogBuildings(self):
        totalBuildings = 0
        targetCogBuildings = 0
        actualCogBuildings = 0
        targetCogdos = 0
        actualCogdos = 0
        for sp in list(self.air.cogPlanners.values()):
            totalBuildings += len(sp.frontdoorPointList)
            targetCogBuildings += sp.targetNumCogBuildings
            targetCogdos += sp.targetNumCogdos
            if sp.buildingMgr:
                numCogdoBlocks = len(sp.buildingMgr.getCogdoBlocks())
                actualCogBuildings += len(sp.buildingMgr.getCogBlocks()) - numCogdoBlocks
                actualCogdos += numCogdoBlocks

        wantedCogBuildings = int(totalBuildings * self.TOTAL_COG_BUILDING_PCT / 100)
        if simbase.air.wantCogdominiums:
            wantedCogdos = int(wantedCogBuildings * self.CogdoRatio)
            wantedCogBuildings -= wantedCogdos
        else:
            wantedCogdos = 0
        self.notify.debug('Want %d out of %d total cog buildings; we currently have %d assigned, %d actual.' % (wantedCogBuildings, totalBuildings, targetCogBuildings, actualCogBuildings))
        if actualCogBuildings > 0:
            numReassigned = 0
            for sp in list(self.air.cogPlanners.values()):
                if sp.buildingMgr:
                    numBuildings = len(sp.buildingMgr.getCogBlocks()) - len(sp.buildingMgr.getCogdoBlocks())
                else:
                    numBuildings = 0
                if numBuildings > sp.targetNumCogBuildings:
                    more = numBuildings - sp.targetNumCogBuildings
                    sp.targetNumCogBuildings += more
                    targetCogBuildings += more
                    numReassigned += more

            if numReassigned > 0:
                self.notify.debug('Assigned %d buildings where cog buildings already existed.' % numReassigned)
        if simbase.air.wantCogdominiums:
            if actualCogdos > 0:
                numReassigned = 0
                for sp in list(self.air.cogPlanners.values()):
                    if sp.buildingMgr:
                        numCogdos = len(sp.buildingMgr.getCogdoBlocks())
                    else:
                        numCogdos = 0
                    if numCogdos > sp.targetNumCogdos:
                        more = numCogdos - sp.targetNumCogdos
                        sp.targetNumCogdos += more
                        targetCogdos += more
                        numReassigned += more

                if numReassigned > 0:
                    self.notify.debug('Assigned %d cogdos where cogdos already existed.' % numReassigned)
        if wantedCogBuildings > targetCogBuildings:
            additionalBuildings = wantedCogBuildings - targetCogBuildings
            self.assignCogBuildings(additionalBuildings)
        else:
            if wantedCogBuildings < targetCogBuildings:
                extraBuildings = targetCogBuildings - wantedCogBuildings
                self.unassignCogBuildings(extraBuildings)
        if simbase.air.wantCogdominiums:
            if wantedCogdos > targetCogdos:
                additionalCogdos = wantedCogdos - targetCogdos
                self.assignCogdos(additionalCogdos)
            elif wantedCogdos < targetCogdos:
                extraCogdos = targetCogdos - wantedCogdos
                self.unassignCogdos(extraCogdos)

    def assignCogBuildings(self, numToAssign: int):
        hoodInfo = self.CogHoodInfo[:]
        totalWeight = self.TOTAL_BWEIGHT
        totalWeightPerTrack = self.TOTAL_BWEIGHT_PER_TRACK[:]
        totalWeightPerHeight = self.TOTAL_BWEIGHT_PER_HEIGHT[:]
        numPerTrack = {'c': 0, 'l': 0, 'm': 0, 's': 0}
        for sp in list(self.air.cogPlanners.values()):
            sp.countNumBuildingsPerTrack(numPerTrack)
            numPerTrack['c'] += sp.pendingBuildingTracks.count('c')
            numPerTrack['l'] += sp.pendingBuildingTracks.count('l')
            numPerTrack['m'] += sp.pendingBuildingTracks.count('m')
            numPerTrack['s'] += sp.pendingBuildingTracks.count('s')

        numPerHeight = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for sp in list(self.air.cogPlanners.values()):
            sp.countNumBuildingsPerHeight(numPerHeight)
            numPerHeight[0] += sp.pendingBuildingHeights.count(0)
            numPerHeight[1] += sp.pendingBuildingHeights.count(1)
            numPerHeight[2] += sp.pendingBuildingHeights.count(2)
            numPerHeight[3] += sp.pendingBuildingHeights.count(3)
            numPerHeight[4] += sp.pendingBuildingHeights.count(4)

        while numToAssign > 0:
            smallestCount = None
            smallestTracks = []
            for trackIndex in range(4):
                if totalWeightPerTrack[trackIndex]:
                    track = CogDNA.cogDepts[trackIndex]
                    count = numPerTrack[track]
                    if smallestCount == None or count < smallestCount:
                        smallestTracks = [
                         track]
                        smallestCount = count
                    elif count == smallestCount:
                        smallestTracks.append(track)

            if not smallestTracks:
                self.notify.info('No more room for buildings, with %s still to assign.' % numToAssign)
                return
            buildingTrack = random.choice(smallestTracks)
            buildingTrackIndex = CogDNA.cogDepts.index(buildingTrack)
            smallestCount = None
            smallestHeights = []
            for height in range(5):
                if totalWeightPerHeight[height]:
                    count = float(numPerHeight[height]) / float(self.BUILDING_HEIGHT_DISTRIBUTION[height])
                    if smallestCount == None or count < smallestCount:
                        smallestHeights = [
                         height]
                        smallestCount = count
                    elif count == smallestCount:
                        smallestHeights.append(height)

            if not smallestHeights:
                self.notify.info('No more room for buildings, with %s still to assign.' % numToAssign)
                return
            buildingHeight = random.choice(smallestHeights)
            self.notify.info('Existing buildings are (%s, %s), choosing from (%s, %s), chose %s, %s.' % (self.formatNumCogsPerTrack(numPerTrack), self.formatNumCogsPerTrack(numPerHeight), smallestTracks, smallestHeights, buildingTrack, buildingHeight))
            repeat = 1
            while repeat and buildingTrack != None and buildingHeight != None:
                if len(hoodInfo) == 0:
                    self.notify.warning('No more streets can have cog buildings, with %d buildings unassigned!' % numToAssign)
                    return
                repeat = 0
                currHoodInfo = self.chooseStreetWithPreference(hoodInfo, buildingTrackIndex, buildingHeight)
                zoneId = currHoodInfo[self.COG_HOOD_INFO_ZONE]
                if zoneId in self.air.cogPlanners:
                    sp = self.air.cogPlanners[zoneId]
                    numCogdos = sp.targetNumCogdos
                    numBldgs = sp.targetNumCogBuildings
                    numTotalBuildings = len(sp.frontdoorPointList)
                else:
                    numCogdos = 0
                    numBldgs = 0
                    numTotalBuildings = 0
                if numCogdos + numBldgs >= currHoodInfo[self.COG_HOOD_INFO_BMAX] or numCogdos + numBldgs >= numTotalBuildings:
                    self.notify.info('Zone %d has enough buildings.' % zoneId)
                    hoodInfo.remove(currHoodInfo)
                    weight = currHoodInfo[self.COG_HOOD_INFO_BWEIGHT]
                    tracks = currHoodInfo[self.COG_HOOD_INFO_TRACK]
                    heights = currHoodInfo[self.COG_HOOD_INFO_HEIGHTS]
                    totalWeight -= weight
                    totalWeightPerTrack[0] -= weight * tracks[0]
                    totalWeightPerTrack[1] -= weight * tracks[1]
                    totalWeightPerTrack[2] -= weight * tracks[2]
                    totalWeightPerTrack[3] -= weight * tracks[3]
                    totalWeightPerHeight[0] -= weight * heights[0]
                    totalWeightPerHeight[1] -= weight * heights[1]
                    totalWeightPerHeight[2] -= weight * heights[2]
                    totalWeightPerHeight[3] -= weight * heights[3]
                    totalWeightPerHeight[4] -= weight * heights[4]
                    if totalWeightPerTrack[buildingTrackIndex] <= 0:
                        buildingTrack = None
                    if totalWeightPerHeight[buildingHeight] <= 0:
                        buildingHeight = None
                    repeat = 1

            if buildingTrack != None and buildingHeight != None:
                sp.targetNumCogBuildings += 1
                sp.pendingBuildingTracks.append(buildingTrack)
                sp.pendingBuildingHeights.append(buildingHeight)
                self.notify.info('Assigning building to zone %d, pending tracks = %s, pending heights = %s' % (zoneId, sp.pendingBuildingTracks, sp.pendingBuildingHeights))
                numPerTrack[buildingTrack] += 1
                numPerHeight[buildingHeight] += 1
                numToAssign -= 1

    def unassignCogBuildings(self, numToAssign: int):
        hoodInfo = self.CogHoodInfo[:]
        totalWeight = self.TOTAL_BWEIGHT
        while numToAssign > 0:
            repeat = 1
            while repeat:
                if len(hoodInfo) == 0:
                    self.notify.warning('No more streets can remove cog buildings, with %d buildings too many!' % numToAssign)
                    return
                repeat = 0
                currHoodInfo = self.chooseStreetNoPreference(hoodInfo, totalWeight)
                zoneId = currHoodInfo[self.COG_HOOD_INFO_ZONE]
                if zoneId in self.air.cogPlanners:
                    sp = self.air.cogPlanners[zoneId]
                    numCogdos = sp.targetNumCogdos
                    numBldgs = sp.targetNumCogBuildings
                    numTotalBuildings = len(sp.frontdoorPointList)
                else:
                    numCogdos = 0
                    numBldgs = 0
                    numTotalBuildings = 0
                overallStrapped = numCogdos + numBldgs <= currHoodInfo[self.COG_HOOD_INFO_BMIN]
                bldgStrapped = numBldgs <= choice(self.MinimumOfOne, 1, 0)
                if overallStrapped or bldgStrapped:
                    self.notify.info("Zone %d can't remove any more buildings." % zoneId)
                    hoodInfo.remove(currHoodInfo)
                    totalWeight -= currHoodInfo[self.COG_HOOD_INFO_BWEIGHT]
                    repeat = 1

            self.notify.info('Unassigning building from zone %d.' % zoneId)
            sp.targetNumCogBuildings -= 1
            numToAssign -= 1

    def assignCogdos(self, numToAssign: int):
        hoodInfo = self.CogHoodInfo[:]
        totalWeight = self.TOTAL_BWEIGHT
        while numToAssign > 0:
            while 1:
                if len(hoodInfo) == 0:
                    self.notify.warning('No more streets can have cogdos, with %d cogdos unassigned!' % numToAssign)
                    return
                currHoodInfo = self.chooseStreetNoPreference(hoodInfo, totalWeight)
                zoneId = currHoodInfo[self.COG_HOOD_INFO_ZONE]
                if zoneId in self.air.cogPlanners:
                    sp = self.air.cogPlanners[zoneId]
                    numCogdos = sp.targetNumCogdos
                    numBldgs = sp.targetNumCogBuildings
                    numTotalBuildings = len(sp.frontdoorPointList)
                else:
                    numCogdos = 0
                    numBldgs = 0
                    numTotalBuildings = 0
                if numCogdos + numBldgs >= currHoodInfo[self.COG_HOOD_INFO_BMAX] or numCogdos + numBldgs >= numTotalBuildings:
                    self.notify.info('Zone %d has enough cogdos.' % zoneId)
                    hoodInfo.remove(currHoodInfo)
                    weight = currHoodInfo[self.COG_HOOD_INFO_BWEIGHT]
                    totalWeight -= weight
                    continue
                break

            sp.targetNumCogdos += 1
            sp.pendingCogdoHeights.append(DistributedBuildingAI.FieldOfficeNumFloors)
            self.notify.info('Assigning cogdo to zone %d' % zoneId)
            numToAssign -= 1

    def unassignCogdos(self, numToAssign: int):
        hoodInfo = self.CogHoodInfo[:]
        totalWeight = self.TOTAL_BWEIGHT
        while numToAssign > 0:
            while 1:
                currHoodInfo = self.chooseStreetNoPreference(hoodInfo, totalWeight)
                zoneId = currHoodInfo[self.COG_HOOD_INFO_ZONE]
                if zoneId in self.air.cogPlanners:
                    sp = self.air.cogPlanners[zoneId]
                    numCogdos = sp.targetNumCogdos
                    numBldgs = sp.targetNumCogBuildings
                    numTotalBuildings = len(sp.frontdoorPointList)
                else:
                    numCogdos = 0
                    numBldgs = 0
                    numTotalBuildings = 0
                overallStrapped = numCogdos + numBldgs <= currHoodInfo[self.COG_HOOD_INFO_BMIN]
                cogdoStrapped = numCogdos <= choice(self.MinimumOfOne, 1, 0)
                if overallStrapped or cogdoStrapped:
                    self.notify.info("Zone %s can't remove any more cogdos." % zoneId)
                    hoodInfo.remove(currHoodInfo)
                    totalWeight -= currHoodInfo[self.COG_HOOD_INFO_BWEIGHT]
                    continue
                break

            self.notify.info('Unassigning cogdo from zone %s.' % zoneId)
            sp.targetNumCogdos -= 1
            numToAssign -= 1

    def chooseStreetNoPreference(self, hoodInfo: CogPlannerBase.CogHoodInfo, totalWeight: int) -> CogPlannerBase.CogHoodInfo:
        c = random.random() * totalWeight
        t = 0
        for currHoodInfo in hoodInfo:
            weight = currHoodInfo[self.COG_HOOD_INFO_BWEIGHT]
            t += weight
            if c < t:
                return currHoodInfo

        self.notify.warning('Weighted random choice failed!  Total is %s, chose %s' % (t, c))
        return random.choice(hoodInfo)

    def chooseStreetWithPreference(self, hoodInfo: CogPlannerBase.CogHoodInfo, buildingTrackIndex: int, buildingHeight: int) -> CogPlannerBase.CogHoodInfo:
        dist = []
        for currHoodInfo in hoodInfo:
            weight = currHoodInfo[self.COG_HOOD_INFO_BWEIGHT]
            thisValue = weight * currHoodInfo[self.COG_HOOD_INFO_TRACK][buildingTrackIndex] * currHoodInfo[self.COG_HOOD_INFO_HEIGHTS][buildingHeight]
            dist.append(thisValue)

        totalWeight = sum(dist)
        c = random.random() * totalWeight
        t = 0
        for i in range(len(hoodInfo)):
            t += dist[i]
            if c < t:
                return hoodInfo[i]

        self.notify.warning('Weighted random choice failed!  Total is %s, chose %s' % (t, c))
        return random.choice(hoodInfo)

    def chooseCogLevel(self, possibleLevels: tuple[int], buildingHeight: list[int]) -> int:
        choices = []
        for level in possibleLevels:
            minFloors, maxFloors = CogBuildingGlobals.CogBuildingInfo[level - 1][0]
            if buildingHeight >= minFloors - 1 and buildingHeight <= maxFloors - 1:
                choices.append(level)

        return random.choice(choices)

    def initTasks(self):
        self.__waitForNextUpkeep()
        self.__waitForNextAdjust()

    def resyncCogs(self):
        for cog in self.cogList:
            cog.resync()

    def flyCogs(self):
        for cog in self.cogList:
            if cog.pathState == 1:
                cog.flyAwayNow()

    def requestBattle(self, zoneId: int, cog: DistributedCogAI, toonId: int) -> bool:
        self.notify.debug('requestBattle() - zone: %d cog: %d toon: %d' % (zoneId, cog.doId, toonId))
        canonicalZoneId = ZoneUtil.getCanonicalZoneId(zoneId)
        if canonicalZoneId not in self.battlePosDict:
            return False
        toon = self.air.doId2do.get(toonId)
        if toon.getBattleId() > 0:
            self.notify.warning('We tried to request a battle when the toon was already in battle')
            return False
        if toon:
            if hasattr(toon, 'doId'):
                print((
                 'Setting toonID ', toonId))
                toon.b_setBattleId(toonId)
        pos = self.battlePosDict[canonicalZoneId]
        interactivePropTrackBonus = -1
        if simbase.config.GetBool('props-buff-battles', True) and canonicalZoneId in self.cellToGagBonusDict:
            tentativeBonusTrack = self.cellToGagBonusDict[canonicalZoneId]
            trackToHolidayDict = {ToontownBattleGlobals.SQUIRT_TRACK: ToontownGlobals.HYDRANTS_BUFF_BATTLES, ToontownBattleGlobals.THROW_TRACK: ToontownGlobals.MAILBOXES_BUFF_BATTLES, ToontownBattleGlobals.HEAL_TRACK: ToontownGlobals.TRASHCANS_BUFF_BATTLES}
            if tentativeBonusTrack in trackToHolidayDict:
                holidayId = trackToHolidayDict[tentativeBonusTrack]
                if simbase.air.holidayManager.isHolidayRunning(holidayId) and simbase.air.holidayManager.getCurPhase(holidayId) >= 1:
                    interactivePropTrackBonus = tentativeBonusTrack
        self.battleMgr.newBattle(zoneId, zoneId, pos, cog, toonId, self.__battleFinished, self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_SMAX], interactivePropTrackBonus)
        for currOther in self.zoneInfo[zoneId]:
            self.notify.debug('Found cog %d in this new battle zone %d' % (currOther.getDoId(), zoneId))
            if currOther != cog:
                if currOther.pathState == 1 and currOther.legType == SuitLeg.TWalk:
                    self.checkForBattle(zoneId, currOther)

        return True

    def __battleFinished(self, zoneId: int):
        self.notify.debug('DistCogPlannerAI:  battle in zone ' + str(zoneId) + ' finished')

    def __cogCanJoinBattle(self, zoneId: int) -> bool:
        battle = self.battleMgr.getBattle(zoneId)
        if len(battle.cogs) >= 4:
            return False
        if battle:
            if simbase.config.GetBool('cogs-always-join', 0):
                return True
            jChanceList = self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_JCHANCE]
            ratioIdx = len(battle.toons) - battle.numCogsEver + 2
            if ratioIdx >= 0:
                if ratioIdx < len(jChanceList):
                    if random.randint(0, 99) < jChanceList[ratioIdx]:
                        return True
                else:
                    self.notify.warning('__cogCanJoinBattle idx out of range!')
                    return True
        return False

    def checkForBattle(self, zoneId: int, cog: DistributedCogAI):
        if self.battleMgr.cellHasBattle(zoneId):
            if self.__cogCanJoinBattle(zoneId) and self.battleMgr.requestBattleAddCog(zoneId, cog):
                pass
            else:
                cog.flyAwayNow()

    def zoneChange(self, cog: DistributedCogAI, oldZone: int, newZone: int = None):
        if oldZone in self.zoneInfo and cog in self.zoneInfo[oldZone]:
            self.zoneInfo[oldZone].remove(cog)
        if newZone != None:
            if newZone not in self.zoneInfo:
                self.zoneInfo[newZone] = []
            self.zoneInfo[newZone].append(cog)

    def d_setZoneId(self, zoneId: int):
        self.sendUpdate('setZoneId', [self.getZoneId()])

    def getZoneId(self) -> int:
        return self.zoneId

    def cogListQuery(self):
        cogIndexList = []
        for cog in self.cogList:
            cogIndexList.append(CogDNA.cogHeadTypes.index(cog.dna.name))

        self.sendUpdateToAvatarId(self.air.getAvatarIdFromSender(), 'cogListResponse', [cogIndexList])

    def buildingListQuery(self):
        buildingDict = {}
        self.countNumBuildingsPerTrack(buildingDict)
        buildingList = [0, 0, 0, 0]
        for dept in CogDNA.cogDepts:
            if dept in buildingDict:
                buildingList[CogDNA.cogDepts.index(dept)] = buildingDict[dept]

        self.sendUpdateToAvatarId(self.air.getAvatarIdFromSender(), 'buildingListResponse', [buildingList])

    def pickLevelTypeAndTrack(self, level: int = None, type: int = None, track: str = None) -> tuple[int, int, str]:
        if level == None:
            level = random.choice(self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_LVL])
        if type == None:
            typeChoices = list(range(max(level - 4, 1), min(level, self.MAX_COG_TYPES) + 1))
            type = random.choice(typeChoices)
        else:
            level = min(max(level, type), type + 4)
        if track == None:
            track = CogDNA.cogDepts[CogBattleGlobals.pickFromFreqList(self.CogHoodInfo[self.hoodInfoIdx][self.COG_HOOD_INFO_TRACK])]
        self.notify.debug('pickLevelTypeAndTrack: %d %d %s' % (level, type, track))
        return (
         level, type, track)

    @classmethod
    def dump(cls):
        s = ''
        totalBldgs = 0
        totalCogdos = 0
        targetTotalBldgs = 0
        targetTotalCogdos = 0
        for index in range(len(cls.CogHoodInfo)):
            currHoodInfo = cls.CogHoodInfo[index]
            zoneId, min, max, bmin, bmax, bweight, smax, jchance, track, lvl, heights = currHoodInfo
            sp = simbase.air.cogPlanners[zoneId]
            targetCogdos = sp.targetNumCogdos
            targetBldgs = sp.targetNumCogBuildings
            bm = simbase.air.buildingManagers.get(zoneId)
            if bm:
                numCogdos = len(bm.getCogdoBlocks())
                numBldgs = len(bm.getCogBlocks()) - numCogdos
                s += '  %s: %2s/%2s buildings, %2s/%2s cogdos\n' % (zoneId, numBldgs, targetBldgs, numCogdos, targetCogdos)
                totalBldgs += numBldgs
                totalCogdos += numCogdos
                targetTotalBldgs += targetBldgs
                targetTotalCogdos += targetCogdos

        header = '%s\n' % (cls.__name__,)
        header += ' %s/%s buildings, %s/%s cogdos\n' % (totalBldgs, targetTotalBldgs, totalCogdos, targetTotalCogdos)
        s = header + s
        print(s)
