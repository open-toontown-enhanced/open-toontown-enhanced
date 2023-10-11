import random
from panda3d.core import VBase3, Point3
from direct.interval.IntervalGlobal import Sequence, Wait, Func, Parallel, Track, LerpPosInterval, ProjectileInterval, SoundInterval, ActorInterval
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattleFinal
from toontown.cog import CogTimings
from toontown.toonbase import ToontownGlobals
from toontown.battle import BattleProps

class DistributedBattleDiners(DistributedBattleFinal.DistributedBattleFinal):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleDiners')

    def __init__(self, cr):
        DistributedBattleFinal.DistributedBattleFinal.__init__(self, cr)
        self.initialReservesJoiningDone = False
        base.dbw = self

    def announceGenerate(self):
        DistributedBattleFinal.DistributedBattleFinal.announceGenerate(self)
        self.moveCogsToInitialPos()

    def showCogsJoining(self, cogs, ts, name, callback):
        if len(cogs) == 0 and not self.initialReservesJoiningDone:
            self.initialReservesJoiningDone = True
            self.doInitialCogsJoining(ts, name, callback)
            return
        self.showCogsFalling(cogs, ts, name, callback)

    def doInitialCogsJoining(self, ts, name, callback):
        done = Func(callback)
        if self.hasLocalToon():
            camera.reparentTo(self)
            if random.choice([0, 1]):
                camera.setPosHpr(20, -4, 7, 60, 0, 0)
            else:
                camera.setPosHpr(-20, -4, 7, -60, 0, 0)
        track = Sequence(Wait(0.5), done, name=name)
        track.start(ts)
        self.storeInterval(track, name)

    def moveCogsToInitialPos(self):
        battlePts = self.cogPoints[len(self.cogPendingPoints) - 1]
        for i in range(len(self.cogs)):
            cog = self.cogs[i]
            cog.reparentTo(self)
            destPos, destHpr = self.getActorPosHpr(cog, self.cogs)
            cog.setPos(destPos)
            cog.setHpr(destHpr)

    def showCogsFalling(self, cogs, ts, name, callback):
        if self.bossCog == None:
            return
        cogTrack = Parallel()
        delay = 0
        for cog in cogs:
            cog.setState('Battle')
            if cog.dna.dept == 'l':
                cog.reparentTo(self.bossCog)
                cog.setPos(0, 0, 0)
            if cog in self.joiningCogs:
                i = len(self.pendingCogs) + self.joiningCogs.index(cog)
                destPos, h = self.cogPendingPoints[i]
                destHpr = VBase3(h, 0, 0)
            else:
                destPos, destHpr = self.getActorPosHpr(cog, self.cogs)
            startPos = destPos + Point3(0, 0, CogTimings.fromSky * ToontownGlobals.SuitWalkSpeed)
            self.notify.debug('startPos for %s = %s' % (cog, startPos))
            cog.reparentTo(self)
            cog.setPos(startPos)
            cog.headsUp(self)
            moveIval = Sequence()
            chairInfo = self.bossCog.claimOneChair()
            if chairInfo:
                moveIval = self.createDinerMoveIval(cog, destPos, chairInfo)
            cogTrack.append(Track((delay, Sequence(moveIval, Func(cog.loop, 'neutral')))))
            delay += 1

        if self.hasLocalToon():
            camera.reparentTo(self)
            self.notify.debug('self.battleSide =%s' % self.battleSide)
            camHeading = -20
            camX = -4
            if self.battleSide == 0:
                camHeading = 20
                camX = 4
            camera.setPosHpr(camX, -15, 7, camHeading, 0, 0)
        done = Func(callback)
        track = Sequence(cogTrack, done, name=name)
        track.start(ts)
        self.storeInterval(track, name)
        return

    def createDinerMoveIval(self, cog, destPos, chairInfo):
        dur = cog.getDuration('landing')
        fr = cog.getFrameRate('landing')
        landingDur = dur
        totalDur = 7.3
        animTimeInAir = totalDur - dur
        flyingDur = animTimeInAir
        impactLength = dur - animTimeInAir
        tableIndex = chairInfo[0]
        chairIndex = chairInfo[1]
        table = self.bossCog.tables[tableIndex]
        chairLocator = table.chairLocators[chairIndex]
        chairPos = chairLocator.getPos(self)
        chairHpr = chairLocator.getHpr(self)
        cog.setPos(chairPos)
        table.setDinerStatus(chairIndex, table.HIDDEN)
        cog.setHpr(chairHpr)
        wayPoint = (chairPos + destPos) / 2.0
        wayPoint.setZ(wayPoint.getZ() + 20)
        moveIval = Sequence(Func(cog.headsUp, self), Func(cog.pose, 'landing', 0), ProjectileInterval(cog, duration=flyingDur, startPos=chairPos, endPos=destPos, gravityMult=0.25), ActorInterval(cog, 'landing'))
        if cog.prop == None:
            cog.prop = BattleProps.globalPropPool.getProp('propeller')
        propDur = cog.prop.getDuration('propeller')
        lastSpinFrame = 8
        fr = cog.prop.getFrameRate('propeller')
        spinTime = lastSpinFrame / fr
        openTime = (lastSpinFrame + 1) / fr
        cog.attachPropeller()
        propTrack = Parallel(SoundInterval(cog.propInSound, duration=flyingDur, node=cog), Sequence(ActorInterval(cog.prop, 'propeller', constrainedLoop=1, duration=flyingDur + 1, startTime=0.0, endTime=spinTime), ActorInterval(cog.prop, 'propeller', duration=landingDur, startTime=openTime), Func(cog.detachPropeller)))
        result = Parallel(moveIval, propTrack)
        return result
