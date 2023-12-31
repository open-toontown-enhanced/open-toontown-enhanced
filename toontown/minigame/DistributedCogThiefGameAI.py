import random
from panda3d.core import Point3
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.distributed.ClockDelta import globalClockDelta
from direct.task import Task
from toontown.minigame import DistributedMinigameAI
from toontown.minigame import MinigameGlobals
from toontown.minigame import CogThiefGameGlobals
CTGG = CogThiefGameGlobals

class DistributedCogThiefGameAI(DistributedMinigameAI.DistributedMinigameAI):
    notify = directNotify.newCategory('DistributedCogThiefGameAI')
    ExplodeWaitTime = 6.0 + CTGG.LyingDownDuration

    def __init__(self, air, minigameId):
        try:
            self.DistributedCogThiefGameAI_initialized
        except:
            self.DistributedCogThiefGameAI_initialized = 1
            DistributedMinigameAI.DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedCogThiefGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.cogInfo = {}
            self.barrelInfo = {}
            self.initBarrelInfo()

    def generate(self):
        self.notify.debug('generate')
        DistributedMinigameAI.DistributedMinigameAI.generate(self)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        self.removeAllTasks()
        DistributedMinigameAI.DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        self.initCogInfo()
        DistributedMinigameAI.DistributedMinigameAI.setGameReady(self)

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('play')

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.notify.debug('gameOver')
        score = int(CTGG.calcScore(self.getCurrentGameTime()))
        for avId in self.avIdList:
            self.scoreDict[avId] = score

        if self.getNumBarrelsStolen() == 0:
            for avId in self.avIdList:
                self.scoreDict[avId] += CTGG.PerfectBonus[len(self.avIdList) - 1]
                self.logPerfectGame(avId)

        self.gameFSM.request('cleanup')
        DistributedMinigameAI.DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        self.startCogGoals()
        if not config.GetBool('cog-thief-endless', 0):
            taskMgr.doMethodLater(CTGG.GameTime, self.timerExpired, self.taskName('gameTimer'))

    def exitPlay(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        taskMgr.remove(self.taskName('gameTimer'))
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def initCogInfo(self):
        for cogIndex in range(self.getNumCogs()):
            self.cogInfo[cogIndex] = {'pos': Point3(CogThiefGameGlobals.CogStartingPositions[cogIndex]),
             'goal': CTGG.NoGoal,
             'goalId': CTGG.InvalidGoalId,
             'barrel': CTGG.NoBarrelCarried}

    def initBarrelInfo(self):
        for barrelIndex in range(CogThiefGameGlobals.NumBarrels):
            self.barrelInfo[barrelIndex] = {'pos': Point3(CogThiefGameGlobals.BarrelStartingPositions[barrelIndex]),
             'carriedBy': CTGG.BarrelOnGround,
             'stolen': False}

    def makeCogCarryBarrel(self, timestamp, clientStamp, cogIndex, barrelIndex):
        if cogIndex in self.cogInfo and barrelIndex in self.barrelInfo:
            self.barrelInfo[barrelIndex]['carriedBy'] = cogIndex
            self.cogInfo[cogIndex]['barrel'] = barrelIndex
        else:
            self.notify.warning('makeCogCarryBarrel invalid cogIndex=%s barrelIndex=%s' % (cogIndex, barrelIndex))

    def b_makeCogCarryBarrel(self, clientStamp, cogIndex, barrelIndex):
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        self.notify.debug('b_makeCogCarryBarrel timeStamp=%s clientStamp=%s cog=%s barrel=%s' % (timestamp,
         clientStamp,
         cogIndex,
         barrelIndex))
        self.makeCogCarryBarrel(timestamp, clientStamp, cogIndex, barrelIndex)
        self.d_makeCogCarryBarrel(timestamp, clientStamp, cogIndex, barrelIndex)

    def d_makeCogCarryBarrel(self, timestamp, clientStamp, cogIndex, barrelIndex):
        pos = self.cogInfo[cogIndex]['pos']
        gameTime = self.getCurrentGameTime()
        self.sendUpdate('makeCogCarryBarrel', [timestamp,
         clientStamp,
         cogIndex,
         barrelIndex,
         pos[0],
         pos[1],
         pos[2]])

    def makeCogDropBarrel(self, timestamp, clientStamp, cogIndex, barrelIndex, barrelPos):
        if cogIndex in self.cogInfo and barrelIndex in self.barrelInfo:
            self.barrelInfo[barrelIndex]['carriedBy'] = CTGG.BarrelOnGround
            self.cogInfo[cogIndex]['barrel'] = CTGG.NoBarrelCarried
        else:
            self.notify.warning('makeCogDropBarrel invalid cogIndex=%s barrelIndex=%s' % (cogIndex, barrelIndex))

    def b_makeCogDropBarrel(self, clientStamp, cogIndex, barrelIndex, barrelPos):
        if self.barrelInfo[barrelIndex]['carriedBy'] != cogIndex:
            self.notify.error("self.barrelInfo[%s]['carriedBy'] != %s" % (barrelIndex, cogIndex))
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        self.makeCogDropBarrel(timestamp, clientStamp, cogIndex, barrelIndex, barrelPos)
        self.d_makeCogDropBarrel(timestamp, clientStamp, cogIndex, barrelIndex, barrelPos)

    def d_makeCogDropBarrel(self, timestamp, clientStamp, cogIndex, barrelIndex, barrelPos):
        pos = barrelPos
        gameTime = self.getCurrentGameTime()
        self.sendUpdate('makeCogDropBarrel', [timestamp,
         clientStamp,
         cogIndex,
         barrelIndex,
         pos[0],
         pos[1],
         pos[2]])

    def isCogCarryingABarrel(self, cogIndex):
        result = self.cogInfo[cogIndex]['barrel'] > CTGG.NoBarrelCarried
        return result

    def isCogCarryingThisBarrel(self, cogIndex, barrelIndex):
        result = self.cogInfo[cogIndex]['barrel'] == barrelIndex
        return result

    def startCogGoals(self):
        delayTimes = []
        for cogIndex in range(self.getNumCogs()):
            delayTimes.append(cogIndex * 1.0)

        random.shuffle(delayTimes)
        for cogIndex in range(self.getNumCogs()):
            self.doMethodLater(delayTimes[cogIndex], self.chooseCogGoal, self.uniqueName('choseCogGoal-%d-' % cogIndex), extraArgs=[cogIndex])

    def chaseToon(self, cogNum, avId):
        goalType = CTGG.ToonGoal
        goalId = avId
        self.cogInfo[cogNum]['goal'] = goalType
        self.cogInfo[cogNum]['goalId'] = goalId
        pos = self.cogInfo[cogNum]['pos']
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        self.notify.debug('chaseToon time=%s cogNum=%s, avId=%s' % (timestamp, cogNum, avId))
        gameTime = self.getCurrentGameTime()
        self.sendUpdate('updateCogGoal', [timestamp,
         timestamp,
         cogNum,
         goalType,
         goalId,
         pos[0],
         pos[1],
         pos[2]])

    def hitByCog(self, avId, timestamp, cogNum, x, y, z):
        if cogNum >= self.getNumCogs():
            self.notify.warning('hitByCog, possible hacker avId=%s' % avId)
            return
        barrelIndex = self.cogInfo[cogNum]['barrel']
        if barrelIndex >= 0:
            barrelPos = Point3(x, y, z)
            self.b_makeCogDropBarrel(timestamp, cogNum, barrelIndex, barrelPos)
        startPos = CTGG.CogStartingPositions[cogNum]
        self.cogInfo[cogNum]['pos'] = startPos
        self.cogInfo[cogNum]['goal'] = CTGG.NoGoal
        self.cogInfo[cogNum]['goalId'] = CTGG.InvalidGoalId
        self.sendCogSync(timestamp, cogNum)
        self.doMethodLater(self.ExplodeWaitTime, self.chooseCogGoal, self.uniqueName('choseCogGoal-%d-' % cogNum), extraArgs=[cogNum])

    def sendCogSync(self, clientstamp, cogNum):
        pos = self.cogInfo[cogNum]['pos']
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        goalType = self.cogInfo[cogNum]['goal']
        goalId = self.cogInfo[cogNum]['goalId']
        gameTime = self.getCurrentGameTime()
        self.sendUpdate('updateCogGoal', [timestamp,
         clientstamp,
         cogNum,
         goalType,
         goalId,
         pos[0],
         pos[1],
         pos[2]])

    def chooseCogGoal(self, cogNum):
        barrelIndex = self.findClosestUnassignedBarrel(cogNum)
        if barrelIndex >= 0:
            self.chaseBarrel(cogNum, barrelIndex)
        else:
            noOneChasing = self.avIdList[:]
            for key in self.cogInfo:
                if self.cogInfo[key]['goal'] == CTGG.ToonGoal:
                    toonId = self.cogInfo[key]['goalId']
                    if toonId in noOneChasing:
                        noOneChasing.remove(toonId)

            chaseToonId = self.avIdList[0]
            if noOneChasing:
                chaseToonId = random.choice(noOneChasing)
            else:
                chaseToonId = random.choice(self.avIdList)
            self.chaseToon(cogNum, chaseToonId)

    def chaseBarrel(self, cogNum, barrelIndex):
        goalType = CTGG.BarrelGoal
        goalId = barrelIndex
        self.cogInfo[cogNum]['goal'] = goalType
        self.cogInfo[cogNum]['goalId'] = goalId
        pos = self.cogInfo[cogNum]['pos']
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        self.notify.debug('chaseBarrel time=%s cogNum=%s, barrelIndex=%s' % (timestamp, cogNum, barrelIndex))
        gameTime = self.getCurrentGameTime()
        self.sendUpdate('updateCogGoal', [timestamp,
         timestamp,
         cogNum,
         goalType,
         goalId,
         pos[0],
         pos[1],
         pos[2]])

    def getCogCarryingBarrel(self, barrelIndex):
        return self.barrelInfo[barrelIndex]['carriedBy']

    def cogHitBarrel(self, clientStamp, cogIndex, barrelIndex, x, y, z):
        if cogIndex >= self.getNumCogs():
            self.notify.warning('cogHitBarrel, possible hacker cogIndex=%s' % cogIndex)
            return
        if barrelIndex >= CTGG.NumBarrels:
            self.notify.warning('cogHitBarrel, possible hacker barrelIndex=%s' % barrelIndex)
            return
        if self.isCogCarryingABarrel(cogIndex):
            self.notify.debug('cog is already carrying a barrel ignore')
            return
        if self.cogInfo[cogIndex]['goal'] == CTGG.NoGoal:
            self.notify.debug('ignoring barrel hit as cog %d has no goal' % cogIndex)
            return
        if self.getCogCarryingBarrel(barrelIndex) == CTGG.BarrelOnGround:
            pos = Point3(x, y, z)
            returnPosIndex = self.chooseReturnPos(cogIndex, pos)
            self.runAway(clientStamp, cogIndex, pos, barrelIndex, returnPosIndex)

    def chooseReturnPos(self, cogIndex, cogPos):
        shortestDistance = 10000
        shortestReturnIndex = -1
        for retIndex in range(len(CTGG.CogReturnPositions)):
            retPos = CTGG.CogReturnPositions[retIndex]
            distance = (cogPos - retPos).length()
            if distance < shortestDistance:
                shortestDistance = distance
                shortestReturnIndex = retIndex
                self.notify.debug('shortest distance=%s index=%s' % (shortestDistance, shortestReturnIndex))

        self.notify.debug('chooseReturnpos returning %s' % shortestReturnIndex)
        return shortestReturnIndex

    def runAway(self, clientStamp, cogIndex, cogPos, barrelIndex, returnPosIndex):
        self.cogInfo[cogIndex]['pos'] = cogPos
        self.b_makeCogCarryBarrel(clientStamp, cogIndex, barrelIndex)
        goalType = CTGG.RunAwayGoal
        goalId = returnPosIndex
        self.cogInfo[cogIndex]['goal'] = goalType
        self.cogInfo[cogIndex]['goalId'] = 0
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        gameTime = self.getCurrentGameTime()
        self.sendUpdate('updateCogGoal', [timestamp,
         clientStamp,
         cogIndex,
         goalType,
         goalId,
         cogPos[0],
         cogPos[1],
         cogPos[2]])

    def pieHitCog(self, avId, timestamp, cogNum, x, y, z):
        if cogNum >= self.getNumCogs():
            self.notify.warning('hitByCog, possible hacker avId=%s' % avId)
            return
        barrelIndex = self.cogInfo[cogNum]['barrel']
        if barrelIndex >= 0:
            barrelPos = Point3(x, y, z)
            self.b_makeCogDropBarrel(timestamp, cogNum, barrelIndex, barrelPos)
        startPos = CTGG.CogStartingPositions[cogNum]
        self.cogInfo[cogNum]['pos'] = startPos
        self.cogInfo[cogNum]['goal'] = CTGG.NoGoal
        self.cogInfo[cogNum]['goalId'] = CTGG.InvalidGoalId
        self.sendCogSync(timestamp, cogNum)
        self.doMethodLater(self.ExplodeWaitTime, self.chooseCogGoal, self.uniqueName('choseCogGoal-%d-' % cogNum), extraArgs=[cogNum])

    def findClosestUnassignedBarrel(self, cogNum):
        possibleBarrels = []
        for key in self.barrelInfo:
            info = self.barrelInfo[key]
            if info['carriedBy'] == CTGG.BarrelOnGround and not info['stolen']:
                if not self.isCogGoingForBarrel(key):
                    possibleBarrels.append(key)

        shortestDistance = 10000
        shortestBarrelIndex = -1
        cogPos = self.cogInfo[cogNum]['pos']
        for possibleIndex in possibleBarrels:
            barrelPos = self.barrelInfo[possibleIndex]['pos']
            distance = (cogPos - barrelPos).length()
            if distance < shortestDistance:
                shortestDistance = distance
                shortestBarrelIndex = possibleIndex

        return shortestBarrelIndex

    def isCogGoingForBarrel(self, barrelIndex):
        result = False
        for cogNum in self.cogInfo:
            cogInfo = self.cogInfo[cogNum]
            if cogInfo['goal'] == CTGG.BarrelGoal and cogInfo['goalId'] == barrelIndex:
                result = True
                break

        return result

    def markBarrelStolen(self, clientStamp, barrelIndex):
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        self.sendUpdate('markBarrelStolen', [timestamp, clientStamp, barrelIndex])
        self.barrelInfo[barrelIndex]['stolen'] = True

    def getNumBarrelsStolen(self):
        numStolen = 0
        for barrel in list(self.barrelInfo.values()):
            if barrel['stolen']:
                numStolen += 1

        return numStolen

    def cogAtReturnPos(self, clientstamp, cogIndex, barrelIndex):
        if cogIndex not in self.cogInfo or barrelIndex not in self.barrelInfo:
            avId = self.air.getAvatarIdFromSender()
            self.air.writeServerEvent('suspicious cogAtReturnPos avId=%s, cogIndex=%s, barrelIndex=%s' % (avId, cogIndex, barrelIndex))
            return
        if self.cogInfo[cogIndex]['goal'] == CTGG.RunAwayGoal:
            if self.isCogCarryingThisBarrel(cogIndex, barrelIndex):
                self.markBarrelStolen(clientstamp, barrelIndex)
                returnPosIndex = self.cogInfo[cogIndex]['goalId']
                retPos = CTGG.CogReturnPositions[returnPosIndex]
                self.b_makeCogDropBarrel(clientstamp, cogIndex, barrelIndex, retPos)
                startPos = CTGG.CogStartingPositions[cogIndex]
                self.cogInfo[cogIndex]['pos'] = startPos
                self.cogInfo[cogIndex]['goal'] = CTGG.NoGoal
                self.cogInfo[cogIndex]['goalId'] = CTGG.InvalidGoalId
                self.doMethodLater(0.5, self.chooseCogGoal, self.uniqueName('choseCogGoal-%d-' % cogIndex), extraArgs=[cogIndex])
                self.checkForGameOver()

    def checkForGameOver(self):
        numStolen = 0
        for key in self.barrelInfo:
            if self.barrelInfo[key]['stolen']:
                numStolen += 1

        self.notify.debug('numStolen = %s' % numStolen)
        if simbase.config.GetBool('cog-thief-check-barrels', 1):
            if not simbase.config.GetBool('cog-thief-endless', 0):
                if numStolen == len(self.barrelInfo):
                    self.gameOver()

    def timerExpired(self, task):
        self.notify.debug('timer expired')
        self.gameOver()
        return Task.done

    def getNumCogs(self):
        result = simbase.config.GetInt('cog-thief-num-cogs', 0)
        if not result:
            safezone = self.getSafezoneId()
            result = CTGG.calculateCogs(self.numPlayers, safezone)
        return result
