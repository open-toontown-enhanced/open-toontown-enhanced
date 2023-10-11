from otp.ai.AIBase import *
from .BattleBase import *
from .BattleCalculatorAI import *
from toontown.toonbase.ToontownBattleGlobals import *
from .CogBattleGlobals import *
from . import DistributedBattleBaseAI
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import State
from direct.showbase.PythonUtil import addListsByValue
import random, types

class DistributedBattleFinalAI(DistributedBattleBaseAI.DistributedBattleBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleFinalAI')

    def __init__(self, air, bossCog, roundCallback, finishCallback, battleSide):
        DistributedBattleBaseAI.DistributedBattleBaseAI.__init__(self, air, bossCog.zoneId, finishCallback)
        self.bossCogId = bossCog.doId
        self.battleNumber = bossCog.battleNumber
        self.rewardDuration = bossCog.getEndOfBattleMovieDuration()
        self.battleSide = battleSide
        self.streetBattle = 0
        self.roundCallback = roundCallback
        self.elevatorPos = Point3(0, 0, 0)
        self.pos = Point3(0, 30, 0)
        self.resumeNeedUpdate = 0
        self.fsm.addState(State.State('ReservesJoining', self.enterReservesJoining, self.exitReservesJoining, [
         'WaitForJoin']))
        offState = self.fsm.getStateNamed('Off')
        offState.addTransition('ReservesJoining')
        waitForJoinState = self.fsm.getStateNamed('WaitForJoin')
        waitForJoinState.addTransition('ReservesJoining')
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('ReservesJoining')

    def getBossCogId(self):
        return self.bossCogId

    def getBattleNumber(self):
        return self.battleNumber

    def getBattleSide(self):
        return self.battleSide

    def startBattle(self, toonIds, cogs):
        self.joinableFsm.request('Joinable')
        for toonId in toonIds:
            if self.addToon(toonId):
                self.activeToons.append(toonId)

        self.d_setMembers()
        for cog in cogs:
            joined = self.cogRequestJoin(cog)

        self.d_setMembers()
        self.b_setState('ReservesJoining')

    def localMovieDone(self, needUpdate, deadToons, deadCogs, lastActiveSuitDied):
        self.timer.stop()
        self.resumeNeedUpdate = needUpdate
        self.resumeDeadToons = deadToons
        self.resumeDeadCogs = deadCogs
        self.resumeLastActiveSuitDied = lastActiveSuitDied
        if len(self.toons) == 0:
            self.d_setMembers()
            self.b_setState('Resume')
        else:
            totalHp = 0
            for cog in self.cogs:
                if cog.currHP > 0:
                    totalHp += cog.currHP

            self.roundCallback(self.activeToons, totalHp, deadCogs)

    def resume(self, joinedReserves):
        if len(joinedReserves) != 0:
            for info in joinedReserves:
                joined = self.cogRequestJoin(info[0])

            self.d_setMembers()
            self.b_setState('ReservesJoining')
        else:
            if len(self.cogs) == 0:
                battleMultiplier = getBossBattleCreditMultiplier(self.battleNumber)
                for toonId in self.activeToons:
                    toon = self.getToon(toonId)
                    if toon:
                        recovered, notRecovered = self.air.questManager.recoverItems(toon, self.cogsKilledThisBattle, self.zoneId)
                        self.toonItems[toonId][0].extend(recovered)
                        self.toonItems[toonId][1].extend(notRecovered)

                self.d_setMembers()
                self.d_setBattleExperience()
                self.b_setState('Reward')
            else:
                if self.resumeNeedUpdate == 1:
                    self.d_setMembers()
                    if len(self.resumeDeadCogs) > 0 and self.resumeLastActiveSuitDied == 0 or len(self.resumeDeadToons) > 0:
                        self.needAdjust = 1
                self.setState('WaitForJoin')
        self.resumeNeedUpdate = 0
        self.resumeDeadToons = []
        self.resumeDeadCogs = []
        self.resumeLastActiveSuitDied = 0

    def enterReservesJoining(self, ts=0):
        self.beginBarrier('ReservesJoining', self.toons, 15, self.__doneReservesJoining)

    def __doneReservesJoining(self, avIds):
        self.b_setState('WaitForJoin')

    def exitReservesJoining(self, ts=0):
        return None

    def enterReward(self):
        self.timer.startCallback(FLOOR_REWARD_TIMEOUT + self.rewardDuration, self.serverRewardDone)
        return None

    def exitReward(self):
        self.timer.stop()
        return None

    def enterResume(self):
        self.joinableFsm.request('Unjoinable')
        self.runableFsm.request('Unrunable')
        DistributedBattleBaseAI.DistributedBattleBaseAI.enterResume(self)
        self.finishCallback(self.zoneId, self.activeToons)
