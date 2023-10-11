from panda3d.core import CollisionNode, CollisionTube, LineSegs, NodePath, Point3, VBase3
from panda3d.otp import NametagGlobals

from direct.actor.Actor import Actor
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedNode import DistributedNode
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.interval.IntervalGlobal import Func, LerpPosInterval, Parallel, Sequence
from direct.showbase.MessengerGlobal import messenger
from direct.task.Task import Task
from direct.task.TaskManagerGlobal import taskMgr
from direct.task.Timer import Timer

from otp.avatar.Emote import globalEmote

from toontown.battle import BattleParticles
from toontown.battle import MovieUtil
from toontown.battle.BattleBase import (
    attackAffectsGroup,
    BattleBase,
    BATTLE_SMALL_VALUE,
    CLIENT_INPUT_TIMEOUT,
    FIRE,
    HEAL,
    levelAffectsGroup,
    LURE,
    MAX_JOIN_T,
    NO_ATTACK,
    NO_TRAP,
    NPCSOS,
    PASS,
    PASS_ATTACK,
    PETSOS,
    SOS,
    TRAP,
    UN_ATTACK
)

from toontown.battle.BattleProps import globalPropPool
from toontown.battle.Movie import Movie
from toontown.distributed.DelayDelete import DelayDelete, cleanupDelayDeletes
from toontown.hood import ZoneUtil
from toontown.cog.Cog import Cog
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toonbase.ToonBaseGlobal import base


class DistributedBattleBase(DistributedNode, BattleBase):
    notify = directNotify.newCategory('DistributedBattleBase')
    id = 0
    camPos = ToontownBattleGlobals.BattleCamDefaultPos
    camHpr = ToontownBattleGlobals.BattleCamDefaultHpr
    camMinFov = ToontownBattleGlobals.BattleCamDefaultMinFov
    camMenuMinFov = ToontownBattleGlobals.BattleCamMenuMinFov
    camJoinPos = ToontownBattleGlobals.BattleCamJoinPos
    camJoinHpr = ToontownBattleGlobals.BattleCamJoinHpr

    def __init__(self, cr, townBattle):
        DistributedNode.__init__(self, cr)
        NodePath.__init__(self)
        self.assign(base.render.attachNewNode(self.uniqueBattleName('distributed-battle')))
        BattleBase.__init__(self)
        self.bossBattle = 0
        self.townBattle = townBattle
        self.__battleCleanedUp = 0
        self.activeIntervals = {}
        self.localToonJustJoined = 0
        self.choseAttackAlready = 0
        self.toons = []
        self.exitedToons = []
        self.cogTraps = ''
        self.membersKeep = None
        self.faceOffName = self.uniqueBattleName('faceoff')
        self.localToonBattleEvent = self.uniqueBattleName('localtoon-battle-event')
        self.adjustName = self.uniqueBattleName('adjust')
        self.timerCountdownTaskName = self.uniqueBattleName('timer-countdown')
        self.movie = Movie(self)
        self.timer = Timer()
        self.needAdjustTownBattle = 0
        self.streetBattle = 1
        self.levelBattle = 0
        self.localToonFsm = ClassicFSM('LocalToon', [State('HasLocalToon', self.enterHasLocalToon, self.exitHasLocalToon, ['NoLocalToon', 'WaitForServer']), State('NoLocalToon', self.enterNoLocalToon, self.exitNoLocalToon, ['HasLocalToon', 'WaitForServer']), State('WaitForServer', self.enterWaitForServer, self.exitWaitForServer, ['HasLocalToon', 'NoLocalToon'])], 'WaitForServer', 'WaitForServer')
        self.localToonFsm.enterInitialState()
        self.fsm = ClassicFSM('DistributedBattle', [State('Off', self.enterOff, self.exitOff, ['FaceOff',
          'WaitForInput',
          'WaitForJoin',
          'MakeMovie',
          'PlayMovie',
          'Reward',
          'Resume']),
         State('FaceOff', self.enterFaceOff, self.exitFaceOff, ['WaitForInput']),
         State('WaitForJoin', self.enterWaitForJoin, self.exitWaitForJoin, ['WaitForInput', 'Resume']),
         State('WaitForInput', self.enterWaitForInput, self.exitWaitForInput, ['WaitForInput', 'PlayMovie', 'Resume']),
         State('MakeMovie', self.enterMakeMovie, self.exitMakeMovie, ['PlayMovie', 'Resume']),
         State('PlayMovie', self.enterPlayMovie, self.exitPlayMovie, ['WaitForInput',
          'WaitForJoin',
          'Reward',
          'Resume']),
         State('Reward', self.enterReward, self.exitReward, ['Resume']),
         State('Resume', self.enterResume, self.exitResume, [])], 'Off', 'Off')
        self.fsm.enterInitialState()
        self.adjustFsm = ClassicFSM('Adjust', [State('Adjusting', self.enterAdjusting, self.exitAdjusting, ['NotAdjusting']), State('NotAdjusting', self.enterNotAdjusting, self.exitNotAdjusting, ['Adjusting'])], 'NotAdjusting', 'NotAdjusting')
        self.adjustFsm.enterInitialState()
        self.interactiveProp = None

    def uniqueBattleName(self, name):
        DistributedBattleBase.id += 1
        return name + '-%d' % DistributedBattleBase.id

    def generate(self):
        self.notify.debug('generate(%s)' % self.doId)
        DistributedNode.generate(self)
        self.__battleCleanedUp = 0
        self.reparentTo(base.render)
        self._skippingRewardMovie = False

    def storeInterval(self, interval, name):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if hasattr(ival, 'delayDelete') or hasattr(ival, 'delayDeletes'):
                self.clearInterval(name, finish=1)

        self.activeIntervals[name] = interval

    def __cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()
            cleanupDelayDeletes(interval)

        self.activeIntervals = {}

    def clearInterval(self, name, finish = 0):
        if name in self.activeIntervals:
            ival = self.activeIntervals[name]
            if finish:
                ival.finish()
            else:
                ival.pause()

            if name in self.activeIntervals:
                cleanupDelayDeletes(ival)
                if name in self.activeIntervals:
                    del self.activeIntervals[name]
        else:
            self.notify.debug('interval: %s already cleared' % name)

    def finishInterval(self, name):
        if name in self.activeIntervals:
            interval = self.activeIntervals[name]
            interval.finish()

    def disable(self):
        self.notify.debug('disable(%s)' % self.doId)
        self.cleanupBattle()
        DistributedNode.disable(self)

    def battleCleanedUp(self):
        return self.__battleCleanedUp

    def cleanupBattle(self):
        if self.__battleCleanedUp:
            return

        self.notify.debug('cleanupBattle(%s)' % self.doId)
        self.__battleCleanedUp = 1
        self.__cleanupIntervals()
        self.fsm.requestFinalState()
        if self.hasLocalToon():
            self.removeLocalToon()
            base.camLens.setMinFov(ToontownGlobals.DefaultCameraMinFov)

        self.localToonFsm.request('WaitForServer')
        self.ignoreAll()
        for cog in self.cogs:
            if cog.battleTrap != NO_TRAP:
                self.notify.debug('250 calling self.removeTrap, cog=%d' % cog.doId)
                self.removeTrap(cog)

            cog.battleTrap = NO_TRAP
            cog.battleTrapProp = None
            self.notify.debug('253 cog.battleTrapProp = None')
            cog.battleTrapIsFresh = 0

        self.cogs = []
        self.pendingCogs = []
        self.joiningCogs = []
        self.activeCogs = []
        self.cogTraps = ''
        self.toons = []
        self.joiningToons = []
        self.pendingToons = []
        self.activeToons = []
        self.runningToons = []
        self.__stopTimer()
        self.__cleanupIntervals()
        self._removeMembersKeep()

    def delete(self):
        self.notify.debug('delete(%s)' % self.doId)
        self.__cleanupIntervals()
        self._removeMembersKeep()
        self.movie.cleanup()
        del self.townBattle
        self.removeNode()
        self.fsm = None
        self.localToonFsm = None
        self.adjustFsm = None
        self.__stopTimer()
        self.timer = None
        DistributedNode.delete(self)

    def loadTrap(self, cog, trapid):
        self.notify.debug('loadTrap() trap: %d cog: %d' % (trapid, cog.doId))
        trapName = ToontownBattleGlobals.AvProps[TRAP][trapid]
        trap = globalPropPool.getProp(trapName)
        cog.battleTrap = trapid
        cog.battleTrapIsFresh = 0
        cog.battleTrapProp = trap
        self.notify.debug('cog.battleTrapProp = trap %s' % trap)
        if trap.getName() == 'traintrack':
            pass
        else:
            trap.wrtReparentTo(cog)

        distance = MovieUtil.COG_TRAP_DISTANCE
        if trapName == 'rake':
            distance = MovieUtil.COG_TRAP_RAKE_DISTANCE
            distance += MovieUtil.getCogRakeOffset(cog)
            trap.setH(180)
            trap.setScale(0.7)
        elif trapName == 'trapdoor' or trapName == 'quicksand':
            trap.setScale(1.7)
        elif trapName == 'marbles':
            distance = MovieUtil.COG_TRAP_MARBLES_DISTANCE
            trap.setH(94)
        elif trapName == 'tnt':
            trap.setP(90)
            tip = trap.find('**/joint_attachEmitter')
            sparks = BattleParticles.createParticleEffect(file='tnt')
            trap.sparksEffect = sparks
            sparks.start(tip)

        trap.setPos(0, distance, 0)
        if isinstance(trap, Actor):
            frame = trap.getNumFrames(trapName) - 1
            trap.pose(trapName, frame)

    def removeTrap(self, cog, removeTrainTrack = False):
        self.notify.debug('removeTrap() from cog: %d, removeTrainTrack=%s' % (cog.doId, removeTrainTrack))
        if cog.battleTrapProp == None:
            self.notify.debug('cog.battleTrapProp == None, cog.battleTrap=%s setting to NO_TRAP, returning' % cog.battleTrap)
            cog.battleTrap = NO_TRAP
            return

        if cog.battleTrap == ToontownBattleGlobals.UBER_GAG_LEVEL_INDEX:
            if removeTrainTrack:
                self.notify.debug('doing removeProp on traintrack')
                MovieUtil.removeProp(cog.battleTrapProp)
                for otherCog in self.cogs:
                    if not otherCog == cog:
                        otherCog.battleTrapProp = None
                        self.notify.debug('351 otherCog=%d otherCog.battleTrapProp = None' % otherCog.doId)
                        otherCog.battleTrap = NO_TRAP
                        otherCog.battleTrapIsFresh = 0
            else:
                self.notify.debug('deliberately not doing removeProp on traintrack')
        else:
            self.notify.debug('cog.battleTrap != UBER_GAG_LEVEL_INDEX')
            MovieUtil.removeProp(cog.battleTrapProp)

        cog.battleTrapProp = None
        self.notify.debug('360 cog.battleTrapProp = None')
        cog.battleTrap = NO_TRAP
        cog.battleTrapIsFresh = 0

    def pause(self):
        self.timer.stop()

    def unpause(self):
        self.timer.resume()

    def findCog(self, id):
        for s in self.cogs:
            if s.doId == id:
                return s

    def findToon(self, id):
        toon = self.getToon(id)
        if toon == None:
            return

        for t in self.toons:
            if t == toon:
                return t

    def isCogLured(self, cog):
        if self.luredCogs.count(cog) != 0:
            return 1

        return 0

    def unlureCog(self, cog):
        self.notify.debug('movie unluring cog %s' % cog.doId)
        if self.luredCogs.count(cog) != 0:
            self.luredCogs.remove(cog)
            self.needAdjustTownBattle = 1

    def lureCog(self, cog):
        self.notify.debug('movie luring cog %s' % cog.doId)
        if self.luredCogs.count(cog) == 0:
            self.luredCogs.append(cog)
            self.needAdjustTownBattle = 1

    def getActorPosHpr(self, actor, actorList = []):
        if isinstance(actor, Cog):
            if actorList == []:
                actorList = self.activeCogs

            if actorList.count(actor) != 0:
                numCogs = len(actorList) - 1
                index = actorList.index(actor)
                point = self.cogPoints[numCogs][index]
                return (Point3(point[0]), VBase3(point[1], 0.0, 0.0))
            else:
                self.notify.warning('getActorPosHpr() - cog not active')
        else:
            if actorList == []:
                actorList = self.activeToons

            if actorList.count(actor) != 0:
                numToons = len(actorList) - 1
                index = actorList.index(actor)
                point = self.toonPoints[numToons][index]
                return (Point3(point[0]), VBase3(point[1], 0.0, 0.0))
            else:
                self.notify.warning('getActorPosHpr() - toon not active')

    def setLevelDoId(self, levelDoId):
        pass

    def setBattleCellId(self, battleCellId):
        pass

    def setInteractivePropTrackBonus(self, trackBonus):
        self.interactivePropTrackBonus = trackBonus

    def getInteractivePropTrackBonus(self):
        return self.interactivePropTrackBonus

    def setPosition(self, x, y, z):
        self.notify.debug('setPosition() - %d %d %d' % (x, y, z))
        pos = Point3(x, y, z)
        self.setPos(pos)

    def setInitialCogPos(self, x, y, z):
        self.initialCogPos = Point3(x, y, z)
        self.headsUp(self.initialCogPos)

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def setBossBattle(self, value):
        self.bossBattle = value

    def setState(self, state, timestamp):
        if self.__battleCleanedUp:
            return

        self.notify.debug('setState(%s)' % state)
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def setMembers(self, cogs, cogsJoining, cogsPending, cogsActive, cogsLured, cogTraps, toons, toonsJoining, toonsPending, toonsActive, toonsRunning, timestamp):
        if self.__battleCleanedUp:
            return

        self.notify.debug('setMembers() - cogs: %s cogsJoining: %s cogsPending: %s cogsActive: %s cogsLured: %s cogTraps: %s toons: %s toonsJoining: %s toonsPending: %s toonsActive: %s toonsRunning: %s' % (cogs,
         cogsJoining,
         cogsPending,
         cogsActive,
         cogsLured,
         cogTraps,
         toons,
         toonsJoining,
         toonsPending,
         toonsActive,
         toonsRunning))
        ts = globalClockDelta.localElapsedTime(timestamp)
        oldcogs = self.cogs
        self.cogs = []
        cogGone = 0
        for s in cogs:
            if s in self.cr.doId2do:
                cog = self.cr.doId2do[s]
                cog.setState('Battle')
                self.cogs.append(cog)
                cog.interactivePropTrackBonus = self.interactivePropTrackBonus
                try:
                    cog.battleTrap
                except:
                    cog.battleTrap = NO_TRAP
                    cog.battleTrapProp = None
                    self.notify.debug('496 cog.battleTrapProp = None')
                    cog.battleTrapIsFresh = 0
            else:
                self.notify.warning('setMembers() - no cog in repository: %d' % s)
                self.cogs.append(None)
                cogGone = 1

        numCogsThatDied = 0
        for s in oldcogs:
            if self.cogs.count(s) == 0:
                self.__removeCog(s)
                numCogsThatDied += 1
                self.notify.debug('cog %d dies, numCogsThatDied=%d' % (s.doId, numCogsThatDied))

        if numCogsThatDied == 4:
            trainTrap = self.find('**/traintrack')
            if not trainTrap.isEmpty():
                self.notify.debug('removing old train trap when 4 cogs died')
                trainTrap.removeNode()

        for s in cogsJoining:
            cog = self.cogs[int(s)]
            if cog != None and self.joiningCogs.count(cog) == 0:
                self.makeCogJoin(cog, ts)

        for s in cogsPending:
            cog = self.cogs[int(s)]
            if cog != None and self.pendingCogs.count(cog) == 0:
                self.__makeCogPending(cog)

        activeCogs = []
        for s in cogsActive:
            cog = self.cogs[int(s)]
            if cog != None and self.activeCogs.count(cog) == 0:
                activeCogs.append(cog)

        oldLuredCogs = self.luredCogs
        self.luredCogs = []
        for s in cogsLured:
            cog = self.cogs[int(s)]
            if cog != None:
                self.luredCogs.append(cog)
                if oldLuredCogs.count(cog) == 0:
                    self.needAdjustTownBattle = 1

        if self.needAdjustTownBattle == 0:
            for s in oldLuredCogs:
                if self.luredCogs.count(s) == 0:
                    self.needAdjustTownBattle = 1

        index = 0
        oldCogTraps = self.cogTraps
        self.cogTraps = cogTraps
        for s in cogTraps:
            trapid = int(s)
            if trapid == 9:
                trapid = -1

            cog = self.cogs[index]
            index += 1
            if cog != None:
                if (trapid == NO_TRAP or trapid != cog.battleTrap) and cog.battleTrapProp != None:
                    self.notify.debug('569 calling self.removeTrap, cog=%d' % cog.doId)
                    self.removeTrap(cog)

                if trapid != NO_TRAP and cog.battleTrapProp == None:
                    if self.fsm.getCurrentState().getName() != 'PlayMovie':
                        self.loadTrap(cog, trapid)

        if len(oldCogTraps) != len(self.cogTraps):
            self.needAdjustTownBattle = 1
        else:
            for i in range(len(oldCogTraps)):
                if oldCogTraps[i] == '9' and self.cogTraps[i] != '9' or oldCogTraps[i] != '9' and self.cogTraps[i] == '9':
                    self.needAdjustTownBattle = 1
                    break

        if cogGone:
            validCogs = []
            for s in self.cogs:
                if s != None:
                    validCogs.append(s)

            self.cogs = validCogs
            self.needAdjustTownBattle = 1

        oldtoons = self.toons
        self.toons = []
        toonGone = 0
        for t in toons:
            toon = self.getToon(t)
            if toon == None:
                self.notify.warning('setMembers() - toon not in cr!')
                self.toons.append(None)
                toonGone = 1
                continue

            self.toons.append(toon)
            if oldtoons.count(toon) == 0:
                self.notify.debug('setMembers() - add toon: %d' % toon.doId)
                self.__listenForUnexpectedExit(toon)
                toon.stopLookAround()
                toon.stopSmooth()

        for t in oldtoons:
            if self.toons.count(t) == 0:
                if self.__removeToon(t) == 1:
                    self.notify.debug('setMembers() - local toon left battle')
                    return []

        for t in toonsJoining:
            if int(t) < len(self.toons):
                toon = self.toons[int(t)]
                if toon != None and self.joiningToons.count(toon) == 0:
                    self.__makeToonJoin(toon, toonsPending, ts)
            else:
                self.notify.warning('setMembers toonsJoining t=%s not in self.toons %s' % (t, self.toons))

        for t in toonsPending:
            if int(t) < len(self.toons):
                toon = self.toons[int(t)]
                if toon != None and self.pendingToons.count(toon) == 0:
                    self.__makeToonPending(toon, ts)
            else:
                self.notify.warning('setMembers toonsPending t=%s not in self.toons %s' % (t, self.toons))

        for t in toonsRunning:
            toon = self.toons[int(t)]
            if toon != None and self.runningToons.count(toon) == 0:
                self.__makeToonRun(toon, ts)

        activeToons = []
        for t in toonsActive:
            toon = self.toons[int(t)]
            if toon != None and self.activeToons.count(toon) == 0:
                activeToons.append(toon)

        if len(activeCogs) > 0 or len(activeToons) > 0:
            self.__makeAvsActive(activeCogs, activeToons)

        if toonGone == 1:
            validToons = []
            for toon in self.toons:
                if toon != None:
                    validToons.append(toon)

            self.toons = validToons

        if len(self.activeToons) > 0:
            self.__requestAdjustTownBattle()

        currStateName = self.localToonFsm.getCurrentState().getName()
        if self.toons.count(base.localAvatar):
            if oldtoons.count(base.localAvatar) == 0:
                self.notify.debug('setMembers() - local toon just joined')
                if self.streetBattle == 1:
                    base.cr.playGame.getPlace().enterZone(self.zoneId)

                self.localToonJustJoined = 1

            if currStateName != 'HasLocalToon':
                self.localToonFsm.request('HasLocalToon')
        else:
            if oldtoons.count(base.localAvatar):
                self.notify.debug('setMembers() - local toon just ran')
                if self.levelBattle:
                    self.unlockLevelViz()

            if currStateName != 'NoLocalToon':
                self.localToonFsm.request('NoLocalToon')

        return oldtoons

    def adjust(self, timestamp):
        if self.__battleCleanedUp:
            return

        self.notify.debug('adjust(%f) from server' % globalClockDelta.localElapsedTime(timestamp))
        self.adjustFsm.request('Adjusting', [globalClockDelta.localElapsedTime(timestamp)])

    def setMovie(self, active, toons, cogs, id0, tr0, le0, tg0, hp0, ac0, hpb0, kbb0, died0, revive0, id1, tr1, le1, tg1, hp1, ac1, hpb1, kbb1, died1, revive1, id2, tr2, le2, tg2, hp2, ac2, hpb2, kbb2, died2, revive2, id3, tr3, le3, tg3, hp3, ac3, hpb3, kbb3, died3, revive3, sid0, at0, stg0, dm0, sd0, sb0, st0, sid1, at1, stg1, dm1, sd1, sb1, st1, sid2, at2, stg2, dm2, sd2, sb2, st2, sid3, at3, stg3, dm3, sd3, sb3, st3):
        if self.__battleCleanedUp:
            return

        self.notify.debug('setMovie()')
        if int(active) == 1:
            self.notify.debug('setMovie() - movie is active')
            self.movie.genAttackDicts(toons, cogs, id0, tr0, le0, tg0, hp0, ac0, hpb0, kbb0, died0, revive0, id1, tr1, le1, tg1, hp1, ac1, hpb1, kbb1, died1, revive1, id2, tr2, le2, tg2, hp2, ac2, hpb2, kbb2, died2, revive2, id3, tr3, le3, tg3, hp3, ac3, hpb3, kbb3, died3, revive3, sid0, at0, stg0, dm0, sd0, sb0, st0, sid1, at1, stg1, dm1, sd1, sb1, st1, sid2, at2, stg2, dm2, sd2, sb2, st2, sid3, at3, stg3, dm3, sd3, sb3, st3)

    def setChosenToonAttacks(self, ids, tracks, levels, targets):
        if self.__battleCleanedUp:
            return

        self.notify.debug('setChosenToonAttacks() - (%s), (%s), (%s), (%s)' % (ids,
         tracks,
         levels,
         targets))
        toonIndices = []
        targetIndices = []
        unAttack = 0
        localToonInList = 0
        for i in range(len(ids)):
            track = tracks[i]
            level = levels[i]
            toon = self.findToon(ids[i])
            if toon == None or self.activeToons.count(toon) == 0:
                self.notify.warning('setChosenToonAttacks() - toon gone or not in battle: %d!' % ids[i])
                toonIndices.append(-1)
                tracks.append(-1)
                levels.append(-1)
                targetIndices.append(-1)
                continue

            if toon == base.localAvatar:
                localToonInList = 1

            toonIndices.append(self.activeToons.index(toon))
            if track == SOS:
                targetIndex = -1
            elif track == NPCSOS:
                targetIndex = -1
            elif track == PETSOS:
                targetIndex = -1
            elif track == PASS:
                targetIndex = -1
                tracks[i] = PASS_ATTACK
            elif attackAffectsGroup(track, level):
                targetIndex = -1
            elif track == HEAL:
                target = self.findToon(targets[i])
                if target != None and self.activeToons.count(target) != 0:
                    targetIndex = self.activeToons.index(target)
                else:
                    targetIndex = -1
            elif track == UN_ATTACK:
                targetIndex = -1
                tracks[i] = NO_ATTACK
                if toon == base.localAvatar:
                    unAttack = 1
                    self.choseAttackAlready = 0
            elif track == NO_ATTACK:
                targetIndex = -1
            else:
                target = self.findCog(targets[i])
                if target != None and self.activeCogs.count(target) != 0:
                    targetIndex = self.activeCogs.index(target)
                else:
                    targetIndex = -1

            targetIndices.append(targetIndex)

        for i in range(4 - len(ids)):
            toonIndices.append(-1)
            tracks.append(-1)
            levels.append(-1)
            targetIndices.append(-1)

        self.townBattleAttacks = (toonIndices,
         tracks,
         levels,
         targetIndices)
        if self.localToonActive() and localToonInList == 1:
            if unAttack == 1 and self.fsm.getCurrentState().getName() == 'WaitForInput':
                if self.townBattle.fsm.getCurrentState().getName() != 'Attack':
                    self.townBattle.setState('Attack')

            self.townBattle.updateChosenAttacks(self.townBattleAttacks[0], self.townBattleAttacks[1], self.townBattleAttacks[2], self.townBattleAttacks[3])

    def setBattleExperience(self, id0, origExp0, earnedExp0, origQuests0, items0, missedItems0, origMerits0, merits0, parts0, id1, origExp1, earnedExp1, origQuests1, items1, missedItems1, origMerits1, merits1, parts1, id2, origExp2, earnedExp2, origQuests2, items2, missedItems2, origMerits2, merits2, parts2, id3, origExp3, earnedExp3, origQuests3, items3, missedItems3, origMerits3, merits3, parts3, deathList, uberList, helpfulToonsList):
        if self.__battleCleanedUp:
            return

        self.movie.genRewardDicts(id0, origExp0, earnedExp0, origQuests0, items0, missedItems0, origMerits0, merits0, parts0, id1, origExp1, earnedExp1, origQuests1, items1, missedItems1, origMerits1, merits1, parts1, id2, origExp2, earnedExp2, origQuests2, items2, missedItems2, origMerits2, merits2, parts2, id3, origExp3, earnedExp3, origQuests3, items3, missedItems3, origMerits3, merits3, parts3, deathList, uberList, helpfulToonsList)

    def __listenForUnexpectedExit(self, toon):
        self.accept(toon.uniqueName('disable'), self.__handleUnexpectedExit, extraArgs=[toon])
        self.accept(toon.uniqueName('died'), self.__handleDied, extraArgs=[toon])

    def __handleUnexpectedExit(self, toon):
        self.notify.warning('handleUnexpectedExit() - toon: %d' % toon.doId)
        self.__removeToon(toon, unexpected=1)

    def __handleDied(self, toon):
        self.notify.warning('handleDied() - toon: %d' % toon.doId)
        if toon == base.localAvatar:
            self.d_toonDied(toon.doId)
            self.cleanupBattle()

    def delayDeleteMembers(self):
        membersKeep = []
        for t in self.toons:
            membersKeep.append(DelayDelete(t, 'delayDeleteMembers'))

        for s in self.cogs:
            membersKeep.append(DelayDelete(s, 'delayDeleteMembers'))

        self._removeMembersKeep()
        self.membersKeep = membersKeep

    def _removeMembersKeep(self):
        if self.membersKeep:
            for delayDelete in self.membersKeep:
                delayDelete.destroy()

        self.membersKeep = None

    def __removeCog(self, cog):
        self.notify.debug('__removeCog(%d)' % cog.doId)
        if self.cogs.count(cog) != 0:
            self.cogs.remove(cog)

        if self.joiningCogs.count(cog) != 0:
            self.joiningCogs.remove(cog)

        if self.pendingCogs.count(cog) != 0:
            self.pendingCogs.remove(cog)

        if self.activeCogs.count(cog) != 0:
            self.activeCogs.remove(cog)

        self.cogGone = 1
        if cog.battleTrap != NO_TRAP:
            self.notify.debug('882 calling self.removeTrap, cog=%d' % cog.doId)
            self.removeTrap(cog)

        cog.battleTrap = NO_TRAP
        cog.battleTrapProp = None
        self.notify.debug('883 cog.battleTrapProp = None')
        cog.battleTrapIsFresh = 0

    def __removeToon(self, toon, unexpected = 0):
        self.notify.debug('__removeToon(%d)' % toon.doId)
        self.exitedToons.append(toon)
        if self.toons.count(toon) != 0:
            self.toons.remove(toon)

        if self.joiningToons.count(toon) != 0:
            self.clearInterval(self.taskName('to-pending-toon-%d' % toon.doId))
            if toon in self.joiningToons:
                self.joiningToons.remove(toon)

        if self.pendingToons.count(toon) != 0:
            self.pendingToons.remove(toon)

        if self.activeToons.count(toon) != 0:
            self.activeToons.remove(toon)

        if self.runningToons.count(toon) != 0:
            self.clearInterval(self.taskName('running-%d' % toon.doId), finish=1)
            if toon in self.runningToons:
                self.runningToons.remove(toon)

        self.ignore(toon.uniqueName('disable'))
        self.ignore(toon.uniqueName('died'))
        self.toonGone = 1
        if toon == base.localAvatar:
            self.removeLocalToon()
            self.__teleportToSafeZone(toon)
            return 1

        return 0

    def removeLocalToon(self):
        if self._skippingRewardMovie:
            return

        if base.cr.playGame.getPlace() != None:
            base.cr.playGame.getPlace().setState('walk')

        base.localAvatar.earnedExperience = None
        self.localToonFsm.request('NoLocalToon')

    def removeInactiveLocalToon(self, toon):
        self.notify.debug('removeInactiveLocalToon(%d)' % toon.doId)
        self.exitedToons.append(toon)
        if self.toons.count(toon) != 0:
            self.toons.remove(toon)

        if self.joiningToons.count(toon) != 0:
            self.clearInterval(self.taskName('to-pending-toon-%d' % toon.doId), finish=1)
            if toon in self.joiningToons:
                self.joiningToons.remove(toon)

        if self.pendingToons.count(toon) != 0:
            self.pendingToons.remove(toon)

        self.ignore(toon.uniqueName('disable'))
        self.ignore(toon.uniqueName('died'))
        base.cr.playGame.getPlace().setState('walk')
        self.localToonFsm.request('WaitForServer')

    def __createJoinInterval(self, av, destPos, destHpr, name, ts, callback, toon = 0):
        joinTrack = Sequence()
        joinTrack.append(Func(globalEmote.disableAll, av, 'dbattlebase, createJoinInterval'))
        avPos = av.getPos(self)
        avPos = Point3(avPos[0], avPos[1], 0.0)
        av.setShadowHeight(0)
        plist = self.buildJoinPointList(avPos, destPos, toon)
        if len(plist) == 0:
            joinTrack.append(Func(av.headsUp, self, destPos))
            if toon == 0:
                timeToDest = self.calcCogMoveTime(avPos, destPos)
                joinTrack.append(Func(av.loop, 'walk'))
            else:
                timeToDest = self.calcToonMoveTime(avPos, destPos)
                joinTrack.append(Func(av.loop, 'run'))

            if timeToDest > BATTLE_SMALL_VALUE:
                joinTrack.append(LerpPosInterval(av, timeToDest, destPos, other=self))
                totalTime = timeToDest
            else:
                totalTime = 0
        else:
            timeToPerimeter = 0
            if toon == 0:
                timeToPerimeter = self.calcCogMoveTime(plist[0], avPos)
                timePerSegment = 10.0 / BattleBase.cogSpeed
                timeToDest = self.calcCogMoveTime(BattleBase.posA, destPos)
            else:
                timeToPerimeter = self.calcToonMoveTime(plist[0], avPos)
                timePerSegment = 10.0 / BattleBase.toonSpeed
                timeToDest = self.calcToonMoveTime(BattleBase.posE, destPos)

            totalTime = timeToPerimeter + (len(plist) - 1) * timePerSegment + timeToDest
            if totalTime > MAX_JOIN_T:
                self.notify.warning('__createJoinInterval() - time: %f' % totalTime)

            joinTrack.append(Func(av.headsUp, self, plist[0]))
            if toon == 0:
                joinTrack.append(Func(av.loop, 'walk'))
            else:
                joinTrack.append(Func(av.loop, 'run'))

            joinTrack.append(LerpPosInterval(av, timeToPerimeter, plist[0], other=self))
            for p in plist[1:]:
                joinTrack.append(Func(av.headsUp, self, p))
                joinTrack.append(LerpPosInterval(av, timePerSegment, p, other=self))

            joinTrack.append(Func(av.headsUp, self, destPos))
            joinTrack.append(LerpPosInterval(av, timeToDest, destPos, other=self))

        joinTrack.append(Func(av.loop, 'neutral'))
        joinTrack.append(Func(av.headsUp, self, Point3(0, 0, 0)))
        tval = totalTime - ts
        if tval < 0:
            tval = totalTime

        joinTrack.append(Func(globalEmote.releaseAll, av, 'dbattlebase, createJoinInterval'))
        joinTrack.append(Func(callback, av, tval))
        if av == base.localAvatar:
            camTrack = Sequence()

            def setCamMinFov(minFov: float):
                base.camLens.setMinFov(minFov)

            camTrack.append(Func(setCamMinFov, self.camMinFov))
            camTrack.append(Func(base.camera.wrtReparentTo, self))
            camTrack.append(Func(base.camera.setPos, self.camJoinPos))
            camTrack.append(Func(base.camera.setHpr, self.camJoinHpr))
            return Parallel(joinTrack, camTrack, name=name)
        else:
            return Sequence(joinTrack, name=name)

    def makeCogJoin(self, cog, ts):
        self.notify.debug('makeCogJoin(%d)' % cog.doId)
        spotIndex = len(self.pendingCogs) + len(self.joiningCogs)
        self.joiningCogs.append(cog)
        cog.setState('Battle')
        openSpot = self.cogPendingPoints[spotIndex]
        pos = openSpot[0]
        hpr = VBase3(openSpot[1], 0.0, 0.0)
        trackName = self.taskName('to-pending-cog-%d' % cog.doId)
        track = self.__createJoinInterval(cog, pos, hpr, trackName, ts, self.__handleCogJoinDone)
        track.start(ts)
        track.delayDelete = DelayDelete(cog, 'makeCogJoin')
        self.storeInterval(track, trackName)
        if ToontownBattleGlobals.SkipMovie:
            track.finish()

    def __handleCogJoinDone(self, cog, ts):
        self.notify.debug('cog: %d is now pending' % cog.doId)
        if self.hasLocalToon():
            self.d_joinDone(base.localAvatar.doId, cog.doId)

    def __makeCogPending(self, cog):
        self.notify.debug('__makeCogPending(%d)' % cog.doId)
        self.clearInterval(self.taskName('to-pending-cog-%d' % cog.doId), finish=1)
        if self.joiningCogs.count(cog):
            self.joiningCogs.remove(cog)

        self.pendingCogs.append(cog)

    def __teleportToSafeZone(self, toon):
        self.notify.debug('teleportToSafeZone(%d)' % toon.doId)
        hoodId = ZoneUtil.getCanonicalHoodId(self.zoneId)
        if hoodId in base.localAvatar.hoodsVisited:
            target_sz = ZoneUtil.getSafeZoneId(self.zoneId)
        else:
            target_sz = ZoneUtil.getSafeZoneId(base.localAvatar.defaultZone)

        base.cr.playGame.getPlace().fsm.request('teleportOut', [{'loader': ZoneUtil.getLoaderName(target_sz),
          'where': ZoneUtil.getWhereName(target_sz, 1),
          'how': 'teleportIn',
          'hoodId': target_sz,
          'zoneId': target_sz,
          'shardId': None,
          'avId': -1,
          'battle': 1}])

    def __makeToonJoin(self, toon, pendingToons, ts):
        self.notify.debug('__makeToonJoin(%d)' % toon.doId)
        spotIndex = len(pendingToons) + len(self.joiningToons)
        self.joiningToons.append(toon)
        openSpot = self.toonPendingPoints[spotIndex]
        pos = openSpot[0]
        hpr = VBase3(openSpot[1], 0.0, 0.0)
        trackName = self.taskName('to-pending-toon-%d' % toon.doId)
        track = self.__createJoinInterval(toon, pos, hpr, trackName, ts, self.__handleToonJoinDone, toon=1)
        if toon != base.localAvatar:
            toon.animFSM.request('off')

        track.start(ts)
        track.delayDelete = DelayDelete(toon, '__makeToonJoin')
        self.storeInterval(track, trackName)

    def __handleToonJoinDone(self, toon, ts):
        self.notify.debug('__handleToonJoinDone() - pending: %d' % toon.doId)
        if self.hasLocalToon():
            self.d_joinDone(base.localAvatar.doId, toon.doId)

    def __makeToonPending(self, toon, ts):
        self.notify.debug('__makeToonPending(%d)' % toon.doId)
        self.clearInterval(self.taskName('to-pending-toon-%d' % toon.doId), finish=1)
        if self.joiningToons.count(toon):
            self.joiningToons.remove(toon)

        spotIndex = len(self.pendingToons)
        self.pendingToons.append(toon)
        openSpot = self.toonPendingPoints[spotIndex]
        pos = openSpot[0]
        hpr = VBase3(openSpot[1], 0.0, 0.0)
        toon.loop('neutral')
        toon.setPosHpr(self, pos, hpr)

    def __makeAvsActive(self, cogs, toons):
        self.notify.debug('__makeAvsActive()')
        self.__stopAdjusting()
        for s in cogs:
            if self.joiningCogs.count(s):
                self.notify.warning('cog: %d was in joining list!' % s.doId)
                self.joiningCogs.remove(s)

            if self.pendingCogs.count(s):
                self.pendingCogs.remove(s)

            self.notify.debug('__makeAvsActive() - cog: %d' % s.doId)
            self.activeCogs.append(s)

        if len(self.activeCogs) >= 1:
            for cog in self.activeCogs:
                cogPos, cogHpr = self.getActorPosHpr(cog)
                if self.isCogLured(cog) == 0:
                    cog.setPosHpr(self, cogPos, cogHpr)
                else:
                    spos = Point3(cogPos[0], cogPos[1] - MovieUtil.COG_LURE_DISTANCE, cogPos[2])
                    cog.setPosHpr(self, spos, cogHpr)

                cog.loop('neutral')

        for toon in toons:
            if self.joiningToons.count(toon):
                self.notify.warning('toon: %d was in joining list!' % toon.doId)
                self.joiningToons.remove(toon)

            if self.pendingToons.count(toon):
                self.pendingToons.remove(toon)

            self.notify.debug('__makeAvsActive() - toon: %d' % toon.doId)
            if self.activeToons.count(toon) == 0:
                self.activeToons.append(toon)
            else:
                self.notify.warning('makeAvsActive() - toon: %d is active!' % toon.doId)

        if len(self.activeToons) >= 1:
            for toon in self.activeToons:
                toonPos, toonHpr = self.getActorPosHpr(toon)
                toon.setPosHpr(self, toonPos, toonHpr)
                toon.loop('neutral')

        if self.fsm.getCurrentState().getName() == 'WaitForInput' and self.localToonActive() and self.localToonJustJoined == 1:
            self.notify.debug('makeAvsActive() - local toon just joined')
            self.__enterLocalToonWaitForInput()
            self.localToonJustJoined = 0
            self.startTimer()

    def __makeToonRun(self, toon, ts):
        self.notify.debug('__makeToonRun(%d)' % toon.doId)
        if self.activeToons.count(toon):
            self.activeToons.remove(toon)

        self.runningToons.append(toon)
        self.toonGone = 1
        self.__stopTimer()
        if self.localToonRunning():
            self.townBattle.setState('Off')

        runMTrack = MovieUtil.getToonTeleportOutInterval(toon)
        runName = self.taskName('running-%d' % toon.doId)
        self.notify.debug('duration: %f' % runMTrack.getDuration())
        runMTrack.start(ts)
        runMTrack.delayDelete = DelayDelete(toon, '__makeToonRun')
        self.storeInterval(runMTrack, runName)

    def getToon(self, toonId):
        if toonId in self.cr.doId2do:
            return self.cr.doId2do[toonId]
        else:
            self.notify.warning('getToon() - toon: %d not in repository!' % toonId)

    def d_toonRequestJoin(self, toonId, pos):
        self.notify.debug('network:toonRequestJoin()')
        self.sendUpdate('toonRequestJoin', [pos[0], pos[1], pos[2]])

    def d_toonRequestRun(self, toonId):
        self.notify.debug('network:toonRequestRun()')
        self.sendUpdate('toonRequestRun', [])

    def d_toonDied(self, toonId):
        self.notify.debug('network:toonDied()')
        self.sendUpdate('toonDied', [])

    def d_faceOffDone(self, toonId):
        self.notify.debug('network:faceOffDone()')
        self.sendUpdate('faceOffDone', [])

    def d_adjustDone(self, toonId):
        self.notify.debug('network:adjustDone()')
        self.sendUpdate('adjustDone', [])

    def d_timeout(self, toonId):
        self.notify.debug('network:timeout()')
        self.sendUpdate('timeout', [])

    def d_movieDone(self, toonId):
        self.notify.debug('network:movieDone()')
        self.sendUpdate('movieDone', [])

    def d_rewardDone(self, toonId):
        self.notify.debug('network:rewardDone()')
        self.sendUpdate('rewardDone', [])

    def d_joinDone(self, toonId, avId):
        self.notify.debug('network:joinDone(%d)' % avId)
        self.sendUpdate('joinDone', [avId])

    def d_requestAttack(self, toonId, track, level, av):
        self.notify.debug('network:requestAttack(%d, %d, %d)' % (track, level, av))
        self.sendUpdate('requestAttack', [track, level, av])

    def d_requestPetProxy(self, toonId, av):
        self.notify.debug('network:requestPetProxy(%s)' % av)
        self.sendUpdate('requestPetProxy', [av])

    def enterOff(self, ts = 0):
        self.localToonFsm.requestFinalState()

    def exitOff(self):
        pass

    def enterFaceOff(self, ts = 0):
        pass

    def exitFaceOff(self):
        pass

    def enterWaitForJoin(self, ts = 0):
        self.notify.debug('enterWaitForJoin()')

    def exitWaitForJoin(self):
        pass

    def __enterLocalToonWaitForInput(self):
        self.notify.debug('enterLocalToonWaitForInput()')
        base.camera.setPosHpr(self.camPos, self.camHpr)
        base.camLens.setMinFov(self.camMenuMinFov)
        NametagGlobals.setMasterArrowsOn(0)
        self.townBattle.setState('Attack')
        self.accept(self.localToonBattleEvent, self.__handleLocalToonBattleEvent)

    def startTimer(self, ts = 0):
        self.notify.debug('startTimer()')
        if ts >= CLIENT_INPUT_TIMEOUT:
            self.notify.warning('startTimer() - ts: %f timeout: %f' % (ts, CLIENT_INPUT_TIMEOUT))
            self.__timedOut()
            return

        self.timer.startCallback(CLIENT_INPUT_TIMEOUT - ts, self.__timedOut)
        timeTask = Task.loop(Task(self.__countdown), Task.pause(0.2))
        taskMgr.add(timeTask, self.timerCountdownTaskName)

    def __stopTimer(self):
        self.notify.debug('__stopTimer()')
        self.timer.stop()
        taskMgr.remove(self.timerCountdownTaskName)

    def __countdown(self, task):
        if hasattr(self.townBattle, 'timer'):
            self.townBattle.updateTimer(int(self.timer.getT()))
        else:
            self.notify.warning('__countdown has tried to update a timer that has been deleted. Stopping timer')
            self.__stopTimer()

        return task.done

    def enterWaitForInput(self, ts = 0):
        self.notify.debug('enterWaitForInput()')
        if self.interactiveProp:
            self.interactiveProp.gotoBattleCheer()

        self.choseAttackAlready = 0
        if self.localToonActive():
            self.__enterLocalToonWaitForInput()
            self.startTimer(ts)

        if self.needAdjustTownBattle == 1:
            self.__adjustTownBattle()

    def exitWaitForInput(self):
        self.notify.debug('exitWaitForInput()')
        if self.localToonActive():
            self.townBattle.setState('Off')
            base.camLens.setMinFov(self.camMinFov)
            self.ignore(self.localToonBattleEvent)
            self.__stopTimer()

    def __handleLocalToonBattleEvent(self, response):
        mode = response['mode']
        noAttack = 0
        if mode == 'Attack':
            self.notify.debug('got an attack')
            track = response['track']
            level = response['level']
            target = response['target']
            targetId = target
            if track == HEAL and not levelAffectsGroup(HEAL, level):
                if target >= 0 and target < len(self.activeToons):
                    targetId = self.activeToons[target].doId
                else:
                    self.notify.warning('invalid toon target: %d' % target)
                    track = -1
                    level = -1
                    targetId = -1
            elif track == HEAL and len(self.activeToons) == 1:
                self.notify.warning('invalid group target for heal')
                track = -1
                level = -1
            elif not attackAffectsGroup(track, level):
                if target >= 0 and target < len(self.activeCogs):
                    targetId = self.activeCogs[target].doId
                else:
                    target = -1

            if len(self.luredCogs) > 0:
                if track == TRAP or track == LURE and not levelAffectsGroup(LURE, level):
                    if target != -1:
                        cog = self.findCog(targetId)
                        if self.luredCogs.count(cog) != 0:
                            self.notify.warning('Cog: %d was lured!' % targetId)
                            track = -1
                            level = -1
                            targetId = -1
                elif track == LURE:
                    if levelAffectsGroup(LURE, level) and len(self.activeCogs) == len(self.luredCogs):
                        self.notify.warning('All cogs are lured!')
                        track = -1
                        level = -1
                        targetId = -1

            if track == TRAP:
                if target != -1:
                    if attackAffectsGroup(track, level):
                        pass
                    else:
                        cog = self.findCog(targetId)
                        if cog.battleTrap != NO_TRAP:
                            self.notify.warning('Cog: %d was already trapped!' % targetId)
                            track = -1
                            level = -1
                            targetId = -1

            self.d_requestAttack(base.localAvatar.doId, track, level, targetId)
        elif mode == 'Run':
            self.notify.debug('got a run')
            self.d_toonRequestRun(base.localAvatar.doId)
        elif mode == 'SOS':
            targetId = response['id']
            self.notify.debug('got an SOS for friend: %d' % targetId)
            self.d_requestAttack(base.localAvatar.doId, SOS, -1, targetId)
        elif mode == 'NPCSOS':
            targetId = response['id']
            self.notify.debug('got an NPCSOS for friend: %d' % targetId)
            self.d_requestAttack(base.localAvatar.doId, NPCSOS, -1, targetId)
        elif mode == 'PETSOS':
            targetId = response['id']
            trickId = response['trickId']
            self.notify.debug('got an PETSOS for pet: %d' % targetId)
            self.d_requestAttack(base.localAvatar.doId, PETSOS, trickId, targetId)
        elif mode == 'PETSOSINFO':
            petProxyId = response['id']
            self.notify.debug('got a PETSOSINFO for pet: %d' % petProxyId)
            if petProxyId in base.cr.doId2do:
                self.notify.debug('pet: %d was already in the repository' % petProxyId)
                proxyGenerateMessage = 'petProxy-%d-generated' % petProxyId
                messenger.send(proxyGenerateMessage)
            else:
                self.d_requestPetProxy(base.localAvatar.doId, petProxyId)

            noAttack = 1
        elif mode == 'Pass':
            targetId = response['id']
            self.notify.debug('got a Pass')
            self.d_requestAttack(base.localAvatar.doId, PASS, -1, -1)
        elif mode == 'UnAttack':
            self.d_requestAttack(base.localAvatar.doId, UN_ATTACK, -1, -1)
            noAttack = 1
        elif mode == 'Fire':
            target = response['target']
            targetId = self.activeCogs[target].doId
            self.d_requestAttack(base.localAvatar.doId, FIRE, -1, targetId)
        else:
            self.notify.warning('unknown battle response')
            return

        if noAttack == 1:
            self.choseAttackAlready = 0
        else:
            self.choseAttackAlready = 1

    def __timedOut(self):
        if self.choseAttackAlready == 1:
            return

        self.notify.debug('WaitForInput timed out')
        if self.localToonActive():
            self.notify.debug('battle timed out')
            self.d_timeout(base.localAvatar.doId)

    def enterMakeMovie(self, ts = 0):
        self.notify.debug('enterMakeMovie()')

    def exitMakeMovie(self):
        pass

    def enterPlayMovie(self, ts):
        self.notify.debug('enterPlayMovie()')
        self.delayDeleteMembers()
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)

        if ToontownBattleGlobals.SkipMovie:
            self.movie.play(ts, self.__handleMovieDone)
            self.movie.finish()
        else:
            self.movie.play(ts, self.__handleMovieDone)

    def __handleMovieDone(self):
        self.notify.debug('__handleMovieDone()')
        if self.hasLocalToon():
            self.d_movieDone(base.localAvatar.doId)

        self.movie.reset()

    def exitPlayMovie(self):
        self.notify.debug('exitPlayMovie()')
        self.movie.reset(finish=1)
        self._removeMembersKeep()
        self.townBattleAttacks = ([-1,
          -1,
          -1,
          -1],
         [-1,
          -1,
          -1,
          -1],
         [-1,
          -1,
          -1,
          -1],
         [0,
          0,
          0,
          0])

    def hasLocalToon(self):
        return self.toons.count(base.localAvatar) > 0

    def localToonPendingOrActive(self):
        return self.pendingToons.count(base.localAvatar) > 0 or self.activeToons.count(base.localAvatar) > 0

    def localToonActive(self):
        return self.activeToons.count(base.localAvatar) > 0

    def localToonActiveOrRunning(self):
        return self.activeToons.count(base.localAvatar) > 0 or self.runningToons.count(base.localAvatar) > 0

    def localToonRunning(self):
        return self.runningToons.count(base.localAvatar) > 0

    def enterHasLocalToon(self):
        self.notify.debug('enterHasLocalToon()')
        if base.cr.playGame.getPlace() != None:
            base.cr.playGame.getPlace().setState('battle', self.localToonBattleEvent)
            if base.localAvatar and hasattr(base.localAvatar, 'inventory') and base.localAvatar.inventory:
                base.localAvatar.inventory.setInteractivePropTrackBonus(self.interactivePropTrackBonus)

        base.camera.wrtReparentTo(self)
        base.camLens.setMinFov(self.camMinFov)

    def exitHasLocalToon(self):
        self.ignore(self.localToonBattleEvent)
        self.__stopTimer()
        if base.localAvatar and hasattr(base.localAvatar, 'inventory') and base.localAvatar.inventory:
            base.localAvatar.inventory.setInteractivePropTrackBonus(-1)

        stateName = None
        place = base.cr.playGame.getPlace()
        if place:
            stateName = place.fsm.getCurrentState().getName()

        if stateName == 'died':
            self.movie.reset()
            base.camera.reparentTo(base.render)
            base.camera.setPosHpr(base.localAvatar, 5.2, 5.45, base.localAvatar.getHeight() * 0.66, 131.5, 3.6, 0)
        else:
            base.camera.wrtReparentTo(base.localAvatar)
            messenger.send('localToonLeftBattle')

        base.camLens.setMinFov(ToontownGlobals.DefaultCameraMinFov)

    def enterNoLocalToon(self):
        self.notify.debug('enterNoLocalToon()')

    def exitNoLocalToon(self):
        pass

    def setSkippingRewardMovie(self):
        self._skippingRewardMovie = True

    def enterWaitForServer(self):
        self.notify.debug('enterWaitForServer()')

    def exitWaitForServer(self):
        pass

    def createAdjustInterval(self, av, destPos, destHpr, toon = 0, run = 0):
        if run == 1:
            adjustTime = self.calcToonMoveTime(destPos, av.getPos(self))
        else:
            adjustTime = self.calcCogMoveTime(destPos, av.getPos(self))

        self.notify.debug('creating adjust interval for: %d' % av.doId)
        adjustTrack = Sequence()
        if run == 1:
            adjustTrack.append(Func(av.loop, 'run'))
        else:
            adjustTrack.append(Func(av.loop, 'walk'))

        adjustTrack.append(Func(av.headsUp, self, destPos))
        adjustTrack.append(LerpPosInterval(av, adjustTime, destPos, other=self))
        adjustTrack.append(Func(av.setHpr, self, destHpr))
        adjustTrack.append(Func(av.loop, 'neutral'))
        return adjustTrack

    def __adjust(self, ts, callback):
        self.notify.debug('__adjust(%f)' % ts)
        adjustTrack = Parallel()
        if len(self.pendingCogs) > 0 or self.cogGone == 1:
            self.cogGone = 0
            numCogs = len(self.pendingCogs) + len(self.activeCogs) - 1
            index = 0
            for cog in self.activeCogs:
                point = self.cogPoints[numCogs][index]
                pos = cog.getPos(self)
                destPos = point[0]
                if self.isCogLured(cog) == 1:
                    destPos = Point3(destPos[0], destPos[1] - MovieUtil.COG_LURE_DISTANCE, destPos[2])

                if pos != destPos:
                    destHpr = VBase3(point[1], 0.0, 0.0)
                    adjustTrack.append(self.createAdjustInterval(cog, destPos, destHpr))

                index += 1

            for cog in self.pendingCogs:
                point = self.cogPoints[numCogs][index]
                destPos = point[0]
                destHpr = VBase3(point[1], 0.0, 0.0)
                adjustTrack.append(self.createAdjustInterval(cog, destPos, destHpr))
                index += 1

        if len(self.pendingToons) > 0 or self.toonGone == 1:
            self.toonGone = 0
            numToons = len(self.pendingToons) + len(self.activeToons) - 1
            index = 0
            for toon in self.activeToons:
                point = self.toonPoints[numToons][index]
                pos = toon.getPos(self)
                destPos = point[0]
                if pos != destPos:
                    destHpr = VBase3(point[1], 0.0, 0.0)
                    adjustTrack.append(self.createAdjustInterval(toon, destPos, destHpr))

                index += 1

            for toon in self.pendingToons:
                point = self.toonPoints[numToons][index]
                destPos = point[0]
                destHpr = VBase3(point[1], 0.0, 0.0)
                adjustTrack.append(self.createAdjustInterval(toon, destPos, destHpr))
                index += 1

        if len(adjustTrack) > 0:
            self.notify.debug('creating adjust multitrack')
            e = Func(self.__handleAdjustDone)
            track = Sequence(adjustTrack, e, name=self.adjustName)
            self.storeInterval(track, self.adjustName)
            track.start(ts)
            if ToontownBattleGlobals.SkipMovie:
                track.finish()
        else:
            self.notify.warning('adjust() - nobody needed adjusting')
            self.__adjustDone()

    def __handleAdjustDone(self):
        self.notify.debug('__handleAdjustDone() - client adjust finished')
        self.clearInterval(self.adjustName)
        self.__adjustDone()

    def __stopAdjusting(self):
        self.notify.debug('__stopAdjusting()')
        self.clearInterval(self.adjustName)
        if self.adjustFsm.getCurrentState().getName() == 'Adjusting':
            self.adjustFsm.request('NotAdjusting')

    def __requestAdjustTownBattle(self):
        self.notify.debug('__requestAdjustTownBattle() curstate = %s' % self.fsm.getCurrentState().getName())
        if self.fsm.getCurrentState().getName() == 'WaitForInput':
            self.__adjustTownBattle()
        else:
            self.needAdjustTownBattle = 1

    def __adjustTownBattle(self):
        self.notify.debug('__adjustTownBattle()')
        if self.localToonActive() and len(self.activeCogs) > 0:
            self.notify.debug('__adjustTownBattle() - adjusting town battle')
            luredCogs = []
            for cog in self.luredCogs:
                if cog not in self.activeCogs:
                    self.notify.error('lured cog not in self.activeCogs')

                luredCogs.append(self.activeCogs.index(cog))

            trappedCogs = []
            for cog in self.activeCogs:
                if cog.battleTrap != NO_TRAP:
                    trappedCogs.append(self.activeCogs.index(cog))

            self.townBattle.adjustCogsAndToons(self.activeCogs, luredCogs, trappedCogs, self.activeToons)
            if hasattr(self, 'townBattleAttacks'):
                self.townBattle.updateChosenAttacks(self.townBattleAttacks[0], self.townBattleAttacks[1], self.townBattleAttacks[2], self.townBattleAttacks[3])

        self.needAdjustTownBattle = 0

    def __adjustDone(self):
        self.notify.debug('__adjustDone()')
        if self.hasLocalToon():
            self.d_adjustDone(base.localAvatar.doId)

        self.adjustFsm.request('NotAdjusting')

    def enterAdjusting(self, ts):
        self.notify.debug('enterAdjusting()')
        if self.localToonActive():
            self.__stopTimer()

        self.delayDeleteMembers()
        self.__adjust(ts, self.__handleAdjustDone)

    def exitAdjusting(self):
        self.notify.debug('exitAdjusting()')
        self.finishInterval(self.adjustName)
        self._removeMembersKeep()
        currStateName = self.fsm.getCurrentState().getName()
        if currStateName == 'WaitForInput' and self.localToonActive():
            self.startTimer()

    def enterNotAdjusting(self):
        self.notify.debug('enterNotAdjusting()')

    def exitNotAdjusting(self):
        pass

    def visualize(self):
        try:
            self.isVisualized
        except:
            self.isVisualized = 0

        if self.isVisualized:
            self.vis.removeNode()
            del self.vis
            self.detachNode()
            self.isVisualized = 0
        else:
            lsegs = LineSegs()
            lsegs.setColor(0.5, 0.5, 1, 1)
            lsegs.moveTo(0, 0, 0)
            for p in BattleBase.allPoints:
                lsegs.drawTo(p[0], p[1], p[2])

            p = BattleBase.allPoints[0]
            lsegs.drawTo(p[0], p[1], p[2])
            self.vis = self.attachNewNode(lsegs.create())
            self.reparentTo(base.render)
            self.isVisualized = 1

    def setupCollisions(self, name):
        self.lockout = CollisionTube(0, 0, 0, 0, 0, 9, 9)
        lockoutNode = CollisionNode(name)
        lockoutNode.addSolid(self.lockout)
        lockoutNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.lockoutNodePath = self.attachNewNode(lockoutNode)
        self.lockoutNodePath.detachNode()

    def removeCollisionData(self):
        del self.lockout
        self.lockoutNodePath.removeNode()
        del self.lockoutNodePath

    def enableCollision(self):
        self.lockoutNodePath.reparentTo(self)
        if len(self.toons) < 4:
            self.accept(self.getCollisionName(), self.__handleLocalToonCollision)

    def __handleLocalToonCollision(self, collEntry):
        self.notify.debug('localToonCollision')
        if self.fsm.getCurrentState().getName() == 'Off':
            self.notify.debug('ignoring collision in Off state')
            return

        if not base.localAvatar.wantBattles:
            return

        if self._skippingRewardMovie:
            return

        base.cr.playGame.getPlace().setState('WaitForBattle')
        toon = base.localAvatar
        self.d_toonRequestJoin(toon.doId, toon.getPos(self))
        base.localAvatar.preBattleHpr = base.localAvatar.getHpr(base.render)
        self.localToonFsm.request('WaitForServer')
        self.onWaitingForJoin()

    def onWaitingForJoin(self):
        pass

    def denyLocalToonJoin(self):
        self.notify.debug('denyLocalToonJoin()')
        place = self.cr.playGame.getPlace()
        if place.fsm.getCurrentState().getName() == 'WaitForBattle':
            place.setState('walk')

        self.localToonFsm.request('NoLocalToon')

    def disableCollision(self):
        self.ignore(self.getCollisionName())
        self.lockoutNodePath.detachNode()

    def openBattleCollision(self):
        if not self.hasLocalToon():
            self.enableCollision()

    def closeBattleCollision(self):
        self.ignore(self.getCollisionName())

    def getCollisionName(self):
        return 'enter' + self.lockoutNodePath.getName()
