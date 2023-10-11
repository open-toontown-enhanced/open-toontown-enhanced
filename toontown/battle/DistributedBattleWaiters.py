import random
from panda3d.core import VBase3, Point3
from direct.interval.IntervalGlobal import Sequence, Wait, Func, Parallel, Track
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattleFinal
from toontown.cog import CogTimings
from toontown.toonbase import ToontownGlobals

class DistributedBattleWaiters(DistributedBattleFinal.DistributedBattleFinal):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleWaiters')

    def __init__(self, cr):
        DistributedBattleFinal.DistributedBattleFinal.__init__(self, cr)
        self.initialReservesJoiningDone = False
        base.dbw = self

    def announceGenerate(self):
        DistributedBattleFinal.DistributedBattleFinal.announceGenerate(self)
        for cog in self.cogs:
            cog.makeWaiter()

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
            self.notify.debug('parenting camera to distributed battle waiters')
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
            cog.makeWaiter()
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
            startPos = destPos + Point3(0, 0, CogTimings.fromSky * ToontownGlobals.CogWalkSpeed)
            self.notify.debug('startPos for %s = %s' % (cog, startPos))
            cog.reparentTo(self)
            cog.setPos(startPos)
            cog.headsUp(self)
            flyIval = cog.beginSupaFlyMove(destPos, True, 'flyIn')
            cogTrack.append(Track((delay, Sequence(flyIval, Func(cog.loop, 'neutral')))))
            delay += 1

        if self.hasLocalToon():
            camera.reparentTo(self)
            if random.choice([0, 1]):
                camera.setPosHpr(20, -4, 7, 60, 0, 0)
            else:
                camera.setPosHpr(-20, -4, 7, -60, 0, 0)
        done = Func(callback)
        track = Sequence(cogTrack, done, name=name)
        track.start(ts)
        self.storeInterval(track, name)
        return

    def enterWaitForInput(self, ts = 0):
        DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput(self, ts)
        if self.hasLocalToon():
            camera.reparentTo(self)
