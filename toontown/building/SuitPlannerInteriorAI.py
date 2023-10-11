from typing import Union
from otp.ai.AIBaseGlobal import *
from toontown.cog import CogDNA
from direct.directnotify import DirectNotifyGlobal
from toontown.cog.DistributedCogAI import DistributedCogAI
from toontown.building import CogBuildingGlobals
import random, functools

class SuitPlannerInteriorAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('SuitPlannerInteriorAI')

    def __init__(self, numFloors: int, bldgLevel: int, bldgTrack: str, zone: int, respectInvasions: bool = True):
        self.dbg_nCogs1stRound: bool = config.GetBool('n-cogs-1st-round', 0)
        self.dbg_4CogsPerFloor: bool = config.GetBool('4-cogs-per-floor', 0)
        self.dbg_1SuitPerFloor: bool = config.GetBool('1-cog-per-floor', 0)
        self.zoneId: int = zone
        self.numFloors: int = numFloors
        self.respectInvasions: bool = respectInvasions
        dbg_defaultSuitName = simbase.config.GetString('cog-type', 'random')
        if dbg_defaultSuitName == 'random':
            self.dbg_defaultSuitType: str | None = None
        else:
            self.dbg_defaultSuitType: str | None = CogDNA.getCogType(dbg_defaultSuitName)
        if isinstance(bldgLevel, str):
            self.notify.warning('bldgLevel is a string!')
            bldgLevel = int(bldgLevel)
        self._genSuitInfos(numFloors, bldgLevel, bldgTrack)

    def __genJoinChances(self, num) -> list[int]:
        joinChances = []
        for currChance in range(num):
            joinChances.append(random.randint(1, 100))

        joinChances.sort(key=functools.cmp_to_key(cmp))
        return joinChances

    def _genSuitInfos(self, numFloors: int, bldgLevel: int, bldgTrack: str):
        self.cogInfos = []
        self.notify.debug('\n\ngenerating cogsInfos with numFloors (' + str(numFloors) + ') bldgLevel (' + str(bldgLevel) + '+1) and bldgTrack (' + str(bldgTrack) + ')')
        for currFloor in range(numFloors):
            infoDict = {}
            lvls = self.__genLevelList(bldgLevel, currFloor, numFloors)
            activeDicts = []
            maxActive = min(4, len(lvls))
            if self.dbg_nCogs1stRound:
                numActive = min(self.dbg_nCogs1stRound, maxActive)
            else:
                numActive = random.randint(1, maxActive)
            if currFloor + 1 == numFloors and len(lvls) > 1:
                origBossSpot = len(lvls) - 1
                if numActive == 1:
                    newBossSpot = numActive - 1
                else:
                    newBossSpot = numActive - 2
                tmp = lvls[newBossSpot]
                lvls[newBossSpot] = lvls[origBossSpot]
                lvls[origBossSpot] = tmp
            bldgInfo = CogBuildingGlobals.CogBuildingInfo[bldgLevel]
            if len(bldgInfo) > CogBuildingGlobals.COG_BLDG_INFO_REVIVES:
                revives = bldgInfo[CogBuildingGlobals.COG_BLDG_INFO_REVIVES][0]
            else:
                revives = 0
            for currActive in range(numActive - 1, -1, -1):
                level = lvls[currActive]
                type = self.__genNormalSuitType(level)
                activeDict = {}
                activeDict['type'] = type
                activeDict['track'] = bldgTrack
                activeDict['level'] = level
                activeDict['revives'] = revives
                activeDicts.append(activeDict)

            infoDict['activeCogs'] = activeDicts
            reserveDicts = []
            numReserve = len(lvls) - numActive
            joinChances = self.__genJoinChances(numReserve)
            for currReserve in range(numReserve):
                level = lvls[currReserve + numActive]
                type = self.__genNormalSuitType(level)
                reserveDict = {}
                reserveDict['type'] = type
                reserveDict['track'] = bldgTrack
                reserveDict['level'] = level
                reserveDict['revives'] = revives
                reserveDict['joinChance'] = joinChances[currReserve]
                reserveDicts.append(reserveDict)

            infoDict['reserveCogs'] = reserveDicts
            self.cogInfos.append(infoDict)

    def __genNormalSuitType(self, lvl: int) -> int:
        if self.dbg_defaultSuitType != None:
            return self.dbg_defaultSuitType
        return CogDNA.getRandomSuitType(lvl)

    def __genLevelList(self, bldgLevel: int, currFloor: int, numFloors: int) -> list[int]:
        bldgInfo = CogBuildingGlobals.CogBuildingInfo[bldgLevel]
        if self.dbg_1SuitPerFloor:
            return [1]
        else:
            if self.dbg_4CogsPerFloor:
                return [5, 6, 7, 10]
        lvlPoolRange = bldgInfo[CogBuildingGlobals.COG_BLDG_INFO_LVL_POOL]
        maxFloors = bldgInfo[CogBuildingGlobals.COG_BLDG_INFO_FLOORS][1]
        lvlPoolMults = bldgInfo[CogBuildingGlobals.COG_BLDG_INFO_LVL_POOL_MULTS]
        floorIdx = min(currFloor, maxFloors - 1)
        lvlPoolMin = lvlPoolRange[0] * lvlPoolMults[floorIdx]
        lvlPoolMax = lvlPoolRange[1] * lvlPoolMults[floorIdx]
        lvlPool = random.randint(int(lvlPoolMin), int(lvlPoolMax))
        lvlMin = bldgInfo[CogBuildingGlobals.COG_BLDG_INFO_COG_LVLS][0]
        lvlMax = bldgInfo[CogBuildingGlobals.COG_BLDG_INFO_COG_LVLS][1]
        self.notify.debug('Level Pool: ' + str(lvlPool))
        lvlList = []
        while lvlPool >= lvlMin:
            newLvl = random.randint(lvlMin, min(lvlPool, lvlMax))
            lvlList.append(newLvl)
            lvlPool -= newLvl

        if currFloor + 1 == numFloors:
            bossLvlRange = bldgInfo[CogBuildingGlobals.COG_BLDG_INFO_BOSS_LVLS]
            newLvl = random.randint(bossLvlRange[0], bossLvlRange[1])
            lvlList.append(newLvl)
        lvlList.sort(key=functools.cmp_to_key(cmp))
        self.notify.debug('LevelList: ' + repr(lvlList))
        return lvlList

    def __setupSuitInfo(self, cog: DistributedCogAI, bldgTrack: str, cogLevel: int, cogType: int) -> bool:
        cogName, skeleton = simbase.air.cogInvasionManager.getInvadingCog()
        if cogName and self.respectInvasions:
            cogType = CogDNA.getCogType(cogName)
            bldgTrack = CogDNA.getCogDept(cogName)
            cogLevel = min(max(cogLevel, cogType), cogType + 4)
        dna = CogDNA.CogDNA()
        dna.newSuitRandom(cogType, bldgTrack)
        cog.dna = dna
        self.notify.debug('Creating cog type ' + cog.dna.name + ' of level ' + str(cogLevel) + ' from type ' + str(cogType) + ' and track ' + str(bldgTrack))
        cog.setLevel(cogLevel)
        return skeleton

    def __genSuitObject(self, cogZone: int, cogType: int, bldgTrack: str, cogLevel: int, revives: int = 0) -> DistributedCogAI:
        newSuit = DistributedCogAI(simbase.air, None)
        skel = self.__setupSuitInfo(newSuit, bldgTrack, cogLevel, cogType)
        if skel:
            newSuit.setSkelecog(1)
        newSuit.setSkeleRevives(revives)
        newSuit.generateWithRequired(cogZone)
        newSuit.node().setName('cog-%s' % newSuit.doId)
        return newSuit

    def myPrint(self):
        self.notify.info('Generated cogs for building: ')
        for currInfo in cogInfos:
            whichSuitInfo = cogInfos.index(currInfo) + 1
            self.notify.debug(' Floor ' + str(whichSuitInfo) + ' has ' + str(len(currInfo[0])) + ' active cogs.')
            for currActive in range(len(currInfo[0])):
                self.notify.debug('  Active cog ' + str(currActive + 1) + ' is of type ' + str(currInfo[0][currActive][0]) + ' and of track ' + str(currInfo[0][currActive][1]) + ' and of level ' + str(currInfo[0][currActive][2]))

            self.notify.debug(' Floor ' + str(whichSuitInfo) + ' has ' + str(len(currInfo[1])) + ' reserve cogs.')
            for currReserve in range(len(currInfo[1])):
                self.notify.debug('  Reserve cog ' + str(currReserve + 1) + ' is of type ' + str(currInfo[1][currReserve][0]) + ' and of track ' + str(currInfo[1][currReserve][1]) + ' and of lvel ' + str(currInfo[1][currReserve][2]) + ' and has ' + str(currInfo[1][currReserve][3]) + '% join restriction.')

    def genFloorCogs(self, floor: int) -> dict[str, Union[DistributedCogAI, tuple[DistributedCogAI, int]]]:
        cogHandles = {}
        floorInfo = self.cogInfos[floor]
        activeCogs = []
        for activeSuitInfo in floorInfo['activeCogs']:
            cog = self.__genSuitObject(self.zoneId, activeSuitInfo['type'], activeSuitInfo['track'], activeSuitInfo['level'], activeSuitInfo['revives'])
            activeCogs.append(cog)

        cogHandles['activeCogs'] = activeCogs
        reserveCogs = []
        for reserveSuitInfo in floorInfo['reserveCogs']:
            cog = self.__genSuitObject(self.zoneId, reserveSuitInfo['type'], reserveSuitInfo['track'], reserveSuitInfo['level'], reserveSuitInfo['revives'])
            reserveCogs.append((cog, reserveSuitInfo['joinChance']))

        cogHandles['reserveCogs'] = reserveCogs

        simbase.air.cogInvasionManager.subtractNumCogsRemaining(len(activeCogs) + len(reserveCogs))

        return cogHandles

    def genCogs(self) -> list[dict[str, Union[DistributedCogAI, tuple[DistributedCogAI, int]]]]:
        cogHandles = []
        for floor in range(len(self.cogInfos)):
            floorSuitHandles = self.genFloorCogs(floor)
            cogHandles.append(floorSuitHandles)

        return cogHandles
