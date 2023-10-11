from panda3d.core import *
from direct.showbase import DirectObject
from toontown.cog import CogDNA
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import LevelBattleManagerAI
import random
import functools

class LevelCogPlannerAI(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('LevelCogPlannerAI')

    def __init__(self, air, level, cogCtor, battleCtor, cogSpecs, reserveCogSpecs, battleCellSpecs, battleExpAggreg=None):
        self.air = air
        self.level = level
        self.cogCtor = cogCtor
        self.cogSpecs = cogSpecs
        if simbase.config.GetBool('level-reserve-cogs', 0):
            self.reserveCogSpecs = reserveCogSpecs
        else:
            self.reserveCogSpecs = []
        self.battleCellSpecs = battleCellSpecs
        self.__genSuitInfos(self.level.getCogLevel(), self.level.getCogTrack())
        self.battleMgr = LevelBattleManagerAI.LevelBattleManagerAI(self.air, self.level, battleCtor, battleExpAggreg)
        self.battleCellId2cogs = {}
        for id in list(self.battleCellSpecs.keys()):
            self.battleCellId2cogs[id] = []

    def destroy(self):
        self.battleMgr.destroyBattleMgr()
        del self.battleMgr
        self.battleCellId2cogs = {}
        self.ignoreAll()
        del self.cogSpecs
        del self.cogCtor
        del self.level
        del self.air

    def __genJoinChances(self, num):
        joinChances = []
        for currChance in range(num):
            joinChances.append(random.randint(1, 100))

        joinChances.sort(key=functools.cmp_to_key(cmp))
        return joinChances

    def __genSuitInfos(self, level, track):
        if __dev__:
            pass

        def getCogDict(spec, cogId, level=level, track=track):
            cogDict = {}
            cogDict['track'] = track
            cogDict.update(spec)
            cogDict['zoneId'] = self.level.getEntityZoneId(spec['parentEntId'])
            cogDict['level'] += level
            cogDict['cogId'] = cogId
            return cogDict

        self.cogInfos = {}
        self.cogInfos['activeCogs'] = []
        for i in range(len(self.cogSpecs)):
            spec = self.cogSpecs[i]
            self.cogInfos['activeCogs'].append(getCogDict(spec, i))

        numReserve = len(self.reserveCogSpecs)
        joinChances = self.__genJoinChances(numReserve)
        self.cogInfos['reserveCogs'] = []
        for i in range(len(self.reserveCogSpecs)):
            spec = self.reserveCogSpecs[i]
            cogDict = getCogDict(spec, i)
            cogDict['joinChance'] = joinChances[i]
            self.cogInfos['reserveCogs'].append(cogDict)

    def __genSuitObject(self, cogDict, reserve):
        cog = self.cogCtor(simbase.air, self)
        dna = CogDNA.CogDNA()
        dna.newSuitRandom(level=CogDNA.getRandomSuitType(cogDict['level']), dept=cogDict['track'])
        cog.dna = dna
        cog.setLevel(cogDict['level'])
        cog.setSkeleRevives(cogDict.get('revives'))
        cog.setLevelDoId(self.level.doId)
        cog.setCogId(cogDict['cogId'])
        cog.setReserve(reserve)
        if cogDict['skeleton']:
            cog.setSkelecog(1)
        cog.generateWithRequired(cogDict['zoneId'])
        cog.boss = cogDict['boss']
        return cog

    def genCogs(self):
        cogHandles = {}
        activeCogs = []
        for activeSuitInfo in self.cogInfos['activeCogs']:
            cog = self.__genSuitObject(activeSuitInfo, 0)
            cog.setBattleCellIndex(activeSuitInfo['battleCell'])
            activeCogs.append(cog)

        cogHandles['activeCogs'] = activeCogs
        reserveCogs = []
        for reserveSuitInfo in self.cogInfos['reserveCogs']:
            cog = self.__genSuitObject(reserveSuitInfo, 1)
            reserveCogs.append([cog, reserveSuitInfo['joinChance'], reserveSuitInfo['battleCell']])

        cogHandles['reserveCogs'] = reserveCogs
        return cogHandles

    def __cogCanJoinBattle(self, cellId):
        battle = self.battleMgr.getBattle(cellId)
        if not battle.cogCanJoin():
            return 0
        return 1

    def requestBattle(self, cog, toonId):
        cellIndex = cog.getBattleCellIndex()
        cellSpec = self.battleCellSpecs[cellIndex]
        pos = cellSpec['pos']
        zone = self.level.getZoneId(self.level.getEntityZoneEntId(cellSpec['parentEntId']))
        maxCogs = 4
        self.battleMgr.newBattle(cellIndex, zone, pos, cog, toonId, self.__handleRoundFinished, self.__handleBattleFinished, maxCogs)
        for otherSuit in self.battleCellId2cogs[cellIndex]:
            if otherSuit is not cog:
                if self.__cogCanJoinBattle(cellIndex):
                    self.battleMgr.requestBattleAddSuit(cellIndex, otherSuit)
                else:
                    battle = self.battleMgr.getBattle(cellIndex)
                    if battle:
                        self.notify.warning('battle not joinable: numCogs=%s, joinable=%s, fsm=%s, toonId=%s' % (len(battle.cogs), battle.isJoinable(), battle.fsm.getCurrentState().getName(), toonId))
                    else:
                        self.notify.warning('battle not joinable: no battle for cell %s, toonId=%s' % (cellIndex, toonId))
                    return 0

        return 1

    def __handleRoundFinished(self, cellId, toonIds, totalHp, deadCogs):
        totalMaxHp = 0
        level = self.level
        battle = self.battleMgr.cellId2battle[cellId]
        for cog in battle.cogs:
            totalMaxHp += cog.maxHP

        for cog in deadCogs:
            level.cogs.remove(cog)

        cellReserves = []
        for info in level.reserveCogs:
            if info[2] == cellId:
                cellReserves.append(info)

        numSpotsAvailable = 4 - len(battle.cogs)
        if len(cellReserves) > 0 and numSpotsAvailable > 0:
            self.joinedReserves = []
            if __dev__:
                pass
            if len(battle.cogs) == 0:
                hpPercent = 100
            else:
                hpPercent = 100 - totalHp / totalMaxHp * 100.0
            for info in cellReserves:
                if info[1] <= hpPercent and len(self.joinedReserves) < numSpotsAvailable:
                    level.cogs.append(info[0])
                    self.joinedReserves.append(info)
                    info[0].setBattleCellIndex(cellId)

            for info in self.joinedReserves:
                level.reserveCogs.remove(info)

            if len(self.joinedReserves) > 0:
                self.reservesJoining(battle)
                level.d_setCogs()
                return
        if len(battle.cogs) == 0:
            if battle:
                battle.resume()
        else:
            battle = self.battleMgr.cellId2battle.get(cellId)
            if battle:
                battle.resume()

    def __handleBattleFinished(self, zoneId):
        pass

    def reservesJoining(self, battle):
        for info in self.joinedReserves:
            battle.cogRequestJoin(info[0])

        battle.resume()
        self.joinedReserves = []

    def getDoId(self):
        return 0

    def removeCog(self, cog):
        cog.requestDelete()

    def cogBattleCellChange(self, cog, oldCell, newCell):
        if oldCell is not None:
            if oldCell in self.battleCellId2cogs:
                self.battleCellId2cogs[oldCell].remove(cog)
            else:
                self.notify.warning('FIXME crash bandaid cogBattleCellChange cog.doId =%s, oldCell=%s not in battleCellId2Cogs.keys %s' % (cog.doId, oldCell, list(self.battleCellId2cogs.keys())))
            blocker = self.battleMgr.battleBlockers.get(oldCell)
            if blocker:
                blocker.removeCog(cog)
        if newCell is not None:
            self.battleCellId2cogs[newCell].append(cog)

            def addCogToBlocker(self=self):
                blocker = self.battleMgr.battleBlockers.get(newCell)
                if blocker:
                    blocker.addCog(cog)
                    return 1
                return 0

            if not addCogToBlocker():
                self.accept(self.getBattleBlockerEvent(newCell), addCogToBlocker)
        return

    def getBattleBlockerEvent(self, cellId):
        return 'battleBlockerAdded-' + str(self.level.doId) + '-' + str(cellId)
