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
        for suit in self.cogs:
            suit.makeWaiter()

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
        battlePts = self.suitPoints[len(self.suitPendingPoints) - 1]
        for i in range(len(self.cogs)):
            suit = self.cogs[i]
            suit.reparentTo(self)
            destPos, destHpr = self.getActorPosHpr(suit, self.cogs)
            suit.setPos(destPos)
            suit.setHpr(destHpr)

    def showCogsFalling(self, cogs, ts, name, callback):
        if self.bossCog == None:
            return
        cogTrack = Parallel()
        delay = 0
        for suit in cogs:
            suit.makeWaiter()
            suit.setState('Battle')
            if suit.dna.dept == 'l':
                suit.reparentTo(self.bossCog)
                suit.setPos(0, 0, 0)
            if suit in self.joiningCogs:
                i = len(self.pendingCogs) + self.joiningCogs.index(suit)
                destPos, h = self.suitPendingPoints[i]
                destHpr = VBase3(h, 0, 0)
            else:
                destPos, destHpr = self.getActorPosHpr(suit, self.cogs)
            startPos = destPos + Point3(0, 0, CogTimings.fromSky * ToontownGlobals.SuitWalkSpeed)
            self.notify.debug('startPos for %s = %s' % (suit, startPos))
            suit.reparentTo(self)
            suit.setPos(startPos)
            suit.headsUp(self)
            flyIval = suit.beginSupaFlyMove(destPos, True, 'flyIn')
            cogTrack.append(Track((delay, Sequence(flyIval, Func(suit.loop, 'neutral')))))
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
