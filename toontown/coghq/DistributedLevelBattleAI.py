from toontown.battle import DistributedBattleAI
from toontown.battle import DistributedBattleBaseAI
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import State
from direct.fsm import ClassicFSM
from toontown.battle.BattleBase import *
from . import CogDisguiseGlobals
from direct.showbase.PythonUtil import addListsByValue

class DistributedLevelBattleAI(DistributedBattleAI.DistributedBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLevelBattleAI')

    def __init__(self, air, battleMgr, pos, cog, toonId, zoneId, level, battleCellId, winState, roundCallback=None, finishCallback=None, maxCogs=4):
        self.blocker = None
        self.level = level
        self.battleCellId = battleCellId
        self.winState = winState
        self.roundCallback = roundCallback
        self.cogTrack = cog.dna.dept
        DistributedBattleAI.DistributedBattleAI.__init__(self, air, battleMgr, pos, cog, toonId, zoneId, finishCallback, maxCogs, tutorialFlag=0, levelFlag=1)
        isBossBattle = 0
        for cog in self.battleMgr.level.planner.battleCellId2cogs[battleCellId]:
            if cog.boss:
                isBossBattle = 1
                break

        self.setBossBattle(isBossBattle)
        self.bossDefeated = 0
        return

    def generate(self):
        DistributedBattleAI.DistributedBattleAI.generate(self)
        battleBlocker = self.battleMgr.battleBlockers.get(self.battleCellId)
        if battleBlocker:
            self.blocker = battleBlocker
            battleBlocker.b_setBattle(self.doId)

    def getLevelDoId(self):
        return self.level.doId

    def getBattleCellId(self):
        return self.battleCellId

    def getTaskZoneId(self):
        pass

    def localMovieDone(self, needUpdate, deadToons, deadCogs, lastActiveCogDied):
        self.timer.stop()
        self.resumeNeedUpdate = needUpdate
        self.resumeDeadToons = deadToons
        self.resumeDeadCogs = deadCogs
        self.resumeLastActiveCogDied = lastActiveCogDied
        if len(self.toons) == 0:
            self.d_setMembers()
            self.b_setState('Resume')
        else:
            totalHp = 0
            for cog in self.cogs:
                if cog.currHP > 0:
                    totalHp += cog.currHP

            self.roundCallback(self.battleCellId, self.activeToons, totalHp, deadCogs)

    def storeCogsKilledThisBattle(self):
        self.cogsKilledPerFloor.append(self.cogsKilledThisBattle)

    def resume(self, topFloor=0):
        if len(self.cogs) == 0:
            avList = []
            for toonId in self.activeToons:
                toon = self.getToon(toonId)
                if toon:
                    avList.append(toon)

            self.d_setMembers()
            self.storeCogsKilledThisBattle()
            if self.bossBattle == 0:
                self.b_setState('Reward')
            else:
                self.handleToonsWon(avList)
                self.d_setBattleExperience()
                self.b_setState(self.winState)
            if self.blocker:
                if len(self.activeToons):
                    self.blocker.b_setBattleFinished()
        else:
            if self.resumeNeedUpdate == 1:
                self.d_setMembers()
                if len(self.resumeDeadCogs) > 0 and self.resumeLastActiveCogDied == 0 or len(self.resumeDeadToons) > 0:
                    self.needAdjust = 1
            self.setState('WaitForJoin')
        self.resumeNeedUpdate = 0
        self.resumeDeadToons = []
        self.resumeDeadCogs = []
        self.resumeLastActiveCogDied = 0

    def handleToonsWon(self, toons):
        pass

    def enterFaceOff(self):
        self.notify.debug('DistributedLevelBattleAI.enterFaceOff()')
        self.joinableFsm.request('Joinable')
        self.runableFsm.request('Unrunable')
        self.cogs[0].releaseControl()
        faceOffTime = self.calcToonMoveTime(self.pos, self.initialCogPos) + FACEOFF_TAUNT_T + SERVER_BUFFER_TIME
        self.notify.debug('faceOffTime = %s' % faceOffTime)
        self.timer.startCallback(faceOffTime, self.__serverFaceOffDone)
        return None

    def __serverFaceOffDone(self):
        self.notify.debug('faceoff timed out on server')
        self.ignoreFaceOffDone = 1
        self.handleFaceOffDone()

    def exitFaceOff(self):
        self.notify.debug('DistributedLevelBattleAI.exitFaceOff()')
        self.timer.stop()
        return None

    def faceOffDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreFaceOffDone == 1:
            self.notify.debug('faceOffDone() - ignoring toon: %d' % toonId)
            return
        else:
            if self.fsm.getCurrentState().getName() != 'FaceOff':
                self.notify.warning('faceOffDone() - in state: %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('faceOffDone() - toon: %d not in toon list' % toonId)
                    return
        self.notify.debug('toon: %d done facing off' % toonId)
        if not self.ignoreFaceOffDone:
            self.handleFaceOffDone()

    def cogRequestJoin(self, cog):
        self.notify.debug('DistributedLevelBattleAI.cogRequestJoin(%d)' % cog.getDoId())
        if cog in self.cogs:
            self.notify.warning('cog %s already in this battle' % cog.getDoId())
            return 0
        DistributedBattleBaseAI.DistributedBattleBaseAI.cogRequestJoin(self, cog)

    def enterReward(self):
        self.joinableFsm.request('Unjoinable')
        self.runableFsm.request('Unrunable')
        self.timer.startCallback(FLOOR_REWARD_TIMEOUT, self.serverRewardDone)
        return None

    def exitReward(self):
        self.timer.stop()
        return None
