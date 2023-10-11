from panda3d.core import *
from direct.showbase import DirectObject
from toontown.cog import CogDNA
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import LevelBattleManagerAI
import random
import functools

class LevelSuitPlannerAI(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('LevelSuitPlannerAI')

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
            suitDict = {}
            suitDict['track'] = track
            suitDict.update(spec)
            suitDict['zoneId'] = self.level.getEntityZoneId(spec['parentEntId'])
            suitDict['level'] += level
            suitDict['cogId'] = cogId
            return suitDict

        self.suitInfos = {}
        self.suitInfos['activeCogs'] = []
        for i in range(len(self.cogSpecs)):
            spec = self.cogSpecs[i]
            self.suitInfos['activeCogs'].append(getCogDict(spec, i))

        numReserve = len(self.reserveCogSpecs)
        joinChances = self.__genJoinChances(numReserve)
        self.suitInfos['reserveCogs'] = []
        for i in range(len(self.reserveCogSpecs)):
            spec = self.reserveCogSpecs[i]
            suitDict = getCogDict(spec, i)
            suitDict['joinChance'] = joinChances[i]
            self.suitInfos['reserveCogs'].append(suitDict)

    def __genSuitObject(self, suitDict, reserve):
        suit = self.cogCtor(simbase.air, self)
        dna = CogDNA.CogDNA()
        dna.newSuitRandom(level=CogDNA.getRandomSuitType(suitDict['level']), dept=suitDict['track'])
        suit.dna = dna
        suit.setLevel(suitDict['level'])
        suit.setSkeleRevives(suitDict.get('revives'))
        suit.setLevelDoId(self.level.doId)
        suit.setCogId(suitDict['cogId'])
        suit.setReserve(reserve)
        if suitDict['skeleton']:
            suit.setSkelecog(1)
        suit.generateWithRequired(suitDict['zoneId'])
        suit.boss = suitDict['boss']
        return suit

    def genCogs(self):
        suitHandles = {}
        activeCogs = []
        for activeSuitInfo in self.suitInfos['activeCogs']:
            suit = self.__genSuitObject(activeSuitInfo, 0)
            suit.setBattleCellIndex(activeSuitInfo['battleCell'])
            activeCogs.append(suit)

        suitHandles['activeCogs'] = activeCogs
        reserveCogs = []
        for reserveSuitInfo in self.suitInfos['reserveCogs']:
            suit = self.__genSuitObject(reserveSuitInfo, 1)
            reserveCogs.append([suit, reserveSuitInfo['joinChance'], reserveSuitInfo['battleCell']])

        suitHandles['reserveCogs'] = reserveCogs
        return suitHandles

    def __suitCanJoinBattle(self, cellId):
        battle = self.battleMgr.getBattle(cellId)
        if not battle.suitCanJoin():
            return 0
        return 1

    def requestBattle(self, suit, toonId):
        cellIndex = suit.getBattleCellIndex()
        cellSpec = self.battleCellSpecs[cellIndex]
        pos = cellSpec['pos']
        zone = self.level.getZoneId(self.level.getEntityZoneEntId(cellSpec['parentEntId']))
        maxCogs = 4
        self.battleMgr.newBattle(cellIndex, zone, pos, suit, toonId, self.__handleRoundFinished, self.__handleBattleFinished, maxCogs)
        for otherSuit in self.battleCellId2cogs[cellIndex]:
            if otherSuit is not suit:
                if self.__suitCanJoinBattle(cellIndex):
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
        for suit in battle.cogs:
            totalMaxHp += suit.maxHP

        for suit in deadCogs:
            level.cogs.remove(suit)

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
            battle.suitRequestJoin(info[0])

        battle.resume()
        self.joinedReserves = []

    def getDoId(self):
        return 0

    def removeSuit(self, suit):
        suit.requestDelete()

    def suitBattleCellChange(self, suit, oldCell, newCell):
        if oldCell is not None:
            if oldCell in self.battleCellId2cogs:
                self.battleCellId2cogs[oldCell].remove(suit)
            else:
                self.notify.warning('FIXME crash bandaid suitBattleCellChange suit.doId =%s, oldCell=%s not in battleCellId2Cogs.keys %s' % (suit.doId, oldCell, list(self.battleCellId2cogs.keys())))
            blocker = self.battleMgr.battleBlockers.get(oldCell)
            if blocker:
                blocker.removeSuit(suit)
        if newCell is not None:
            self.battleCellId2cogs[newCell].append(suit)

            def addCogToBlocker(self=self):
                blocker = self.battleMgr.battleBlockers.get(newCell)
                if blocker:
                    blocker.addCog(suit)
                    return 1
                return 0

            if not addCogToBlocker():
                self.accept(self.getBattleBlockerEvent(newCell), addCogToBlocker)
        return

    def getBattleBlockerEvent(self, cellId):
        return 'battleBlockerAdded-' + str(self.level.doId) + '-' + str(cellId)
