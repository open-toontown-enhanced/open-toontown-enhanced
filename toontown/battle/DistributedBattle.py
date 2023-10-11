from panda3d.core import *
from panda3d.otp import *
from direct.interval.IntervalGlobal import *
from .BattleBase import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from . import DistributedBattleBase
from direct.directnotify import DirectNotifyGlobal
from . import MovieUtil
from toontown.cog import Cog
from direct.actor import Actor
from toontown.toon import TTEmote
from otp.avatar import Emote
from . import CogBattleGlobals
from toontown.distributed import DelayDelete
import random

class DistributedBattle(DistributedBattleBase.DistributedBattleBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattle')
    camFOMinFov = ToontownBattleGlobals.BattleCamFaceOffMinFov
    camFOPos = ToontownBattleGlobals.BattleCamFaceOffPos
    PlayGameSetPlaceEvent = 'playGameSetPlace'

    def __init__(self, cr):
        townBattle = cr.playGame.hood.loader.townBattle
        DistributedBattleBase.DistributedBattleBase.__init__(self, cr, townBattle)
        self.setupCollisions(self.uniqueBattleName('battle-collide'))

    def generate(self):
        DistributedBattleBase.DistributedBattleBase.generate(self)

    def announceGenerate(self):
        DistributedBattleBase.DistributedBattleBase.generate(self)

    def disable(self):
        DistributedBattleBase.DistributedBattleBase.disable(self)
        self.ignore(self.PlayGameSetPlaceEvent)

    def delete(self):
        DistributedBattleBase.DistributedBattleBase.delete(self)
        self.ignore(self.PlayGameSetPlaceEvent)
        self.removeCollisionData()

    def setInteractivePropTrackBonus(self, trackBonus):
        DistributedBattleBase.DistributedBattleBase.setInteractivePropTrackBonus(self, trackBonus)
        if self.interactivePropTrackBonus >= 0:
            if base.cr.playGame.hood:
                self.calcInteractiveProp()
            else:
                self.acceptOnce(self.PlayGameSetPlaceEvent, self.calcInteractiveProp)

    def calcInteractiveProp(self):
        if base.cr.playGame.hood:
            loader = base.cr.playGame.hood.loader
            if hasattr(loader, 'getInteractiveProp'):
                self.interactiveProp = loader.getInteractiveProp(self.zoneId)
                self.notify.debug('self.interactiveProp = %s' % self.interactiveProp)
            else:
                self.notify.warning('no loader.getInteractiveProp self.interactiveProp is None')
        else:
            self.notify.warning('no hood  self.interactiveProp is None')

    def setMembers(self, cogs, cogsJoining, cogsPending, cogsActive, cogsLured, cogTraps, toons, toonsJoining, toonsPending, toonsActive, toonsRunning, timestamp):
        if self.battleCleanedUp():
            return
        oldtoons = DistributedBattleBase.DistributedBattleBase.setMembers(self, cogs, cogsJoining, cogsPending, cogsActive, cogsLured, cogTraps, toons, toonsJoining, toonsPending, toonsActive, toonsRunning, timestamp)
        if len(self.toons) == 4 and len(oldtoons) < 4:
            self.notify.debug('setMembers() - battle is now full of toons')
            self.closeBattleCollision()
        elif len(self.toons) < 4 and len(oldtoons) == 4:
            self.openBattleCollision()

    def __faceOff(self, ts, name, callback):
        if len(self.cogs) == 0:
            self.notify.warning('__faceOff(): no cogs.')
            return
        if len(self.toons) == 0:
            self.notify.warning('__faceOff(): no toons.')
            return
        cog = self.cogs[0]
        point = self.cogPoints[0][0]
        cogPos = point[0]
        cogHpr = VBase3(point[1], 0.0, 0.0)
        toon = self.toons[0]
        point = self.toonPoints[0][0]
        toonPos = point[0]
        toonHpr = VBase3(point[1], 0.0, 0.0)
        p = toon.getPos(self)
        toon.setPos(self, p[0], p[1], 0.0)
        toon.setShadowHeight(0)
        cog.setState('Battle')
        cogTrack = Sequence()
        toonTrack = Sequence()
        cogTrack.append(Func(cog.loop, 'neutral'))
        cogTrack.append(Func(cog.headsUp, toon))
        taunt = CogBattleGlobals.getFaceoffTaunt(cog.getStyleName(), cog.doId)
        cogTrack.append(Func(cog.setChatAbsolute, taunt, CFSpeech | CFTimeout))
        toonTrack.append(Func(toon.loop, 'neutral'))
        toonTrack.append(Func(toon.headsUp, cog))
        cogHeight = cog.getHeight()
        cogOffsetPnt = Point3(0, 0, cogHeight)
        faceoffTime = self.calcFaceoffTime(self.getPos(), self.initialCogPos)
        faceoffTime = max(faceoffTime, BATTLE_SMALL_VALUE)
        delay = FACEOFF_TAUNT_T
        if self.hasLocalToon():
            MidTauntCamHeight = cogHeight * 0.66
            MidTauntCamHeightLim = cogHeight - 1.8
            if MidTauntCamHeight < MidTauntCamHeightLim:
                MidTauntCamHeight = MidTauntCamHeightLim
            TauntCamY = 16
            TauntCamX = random.choice((-5, 5))
            TauntCamHeight = random.choice((MidTauntCamHeight, 1, 11))
            camTrack = Sequence()
            camTrack.append(Func(camera.wrtReparentTo, cog))
            camTrack.append(Func(base.camLens.setMinFov, self.camFOMinFov))
            camTrack.append(Func(camera.setPos, TauntCamX, TauntCamY, TauntCamHeight))
            camTrack.append(Func(camera.lookAt, cog, cogOffsetPnt))
            camTrack.append(Wait(delay))
            camTrack.append(Func(base.camLens.setMinFov, self.camMinFov))
            camTrack.append(Func(camera.wrtReparentTo, self))
            camTrack.append(Func(camera.setPos, self.camFOPos))
            camTrack.append(Func(camera.lookAt, cog.getPos(self)))
            camTrack.append(Wait(faceoffTime))
            if self.interactiveProp:
                camTrack.append(Func(camera.lookAt, self.interactiveProp.node.getPos(self)))
                camTrack.append(Wait(FACEOFF_LOOK_AT_PROP_T))
        cogTrack.append(Wait(delay))
        toonTrack.append(Wait(delay))
        cogTrack.append(Func(cog.headsUp, self, cogPos))
        cogTrack.append(Func(cog.clearChat))
        toonTrack.append(Func(toon.headsUp, self, toonPos))
        cogTrack.append(Func(cog.loop, 'walk'))
        cogTrack.append(LerpPosInterval(cog, faceoffTime, cogPos, other=self))
        cogTrack.append(Func(cog.loop, 'neutral'))
        cogTrack.append(Func(cog.setHpr, self, cogHpr))
        toonTrack.append(Func(toon.loop, 'run'))
        toonTrack.append(LerpPosInterval(toon, faceoffTime, toonPos, other=self))
        toonTrack.append(Func(toon.loop, 'neutral'))
        toonTrack.append(Func(toon.setHpr, self, toonHpr))
        if base.localAvatar == toon:
            soundTrack = Sequence(Wait(delay), SoundInterval(base.localAvatar.soundRun, loop=1, duration=faceoffTime, node=base.localAvatar))
        else:
            soundTrack = Wait(delay + faceoffTime)
        mtrack = Parallel(cogTrack, toonTrack, soundTrack)
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
            mtrack = Parallel(mtrack, camTrack)
        done = Func(callback)
        track = Sequence(mtrack, done, name=name)
        track.delayDeletes = [DelayDelete.DelayDelete(toon, '__faceOff'), DelayDelete.DelayDelete(cog, '__faceOff')]
        track.start(ts)
        self.storeInterval(track, name)

    def enterFaceOff(self, ts):
        self.notify.debug('enterFaceOff()')
        self.delayDeleteMembers()
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.disableAll(self.toons[0], 'dbattle, enterFaceOff')
        self.__faceOff(ts, self.faceOffName, self.__handleFaceOffDone)
        if self.interactiveProp:
            self.interactiveProp.gotoFaceoff()

    def __handleFaceOffDone(self):
        self.notify.debug('FaceOff done')
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            self.d_faceOffDone(base.localAvatar.doId)

    def exitFaceOff(self):
        self.notify.debug('exitFaceOff()')
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.releaseAll(self.toons[0], 'dbattle exitFaceOff')
        self.finishInterval(self.faceOffName)
        self.clearInterval(self.faceOffName)
        self._removeMembersKeep()

    def enterReward(self, ts):
        self.notify.debug('enterReward()')
        self.disableCollision()
        self.delayDeleteMembers()
        Emote.globalEmote.disableAll(base.localAvatar, 'dbattle, enterReward')
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
            if self.localToonActive() == 0:
                self.removeInactiveLocalToon(base.localAvatar)
        for toon in self.toons:
            toon.startSmooth()

        self.accept('resumeAfterReward', self.handleResumeAfterReward)
        if self.interactiveProp:
            self.interactiveProp.gotoVictory()
        self.playReward(ts)

    def playReward(self, ts):
        self.movie.playReward(ts, self.uniqueName('reward'), self.handleRewardDone)

    def handleRewardDone(self):
        self.notify.debug('Reward done')
        if self.hasLocalToon():
            self.d_rewardDone(base.localAvatar.doId)
        self.movie.resetReward()
        messenger.send('resumeAfterReward')

    def handleResumeAfterReward(self):
        self.fsm.request('Resume')

    def exitReward(self):
        self.notify.debug('exitReward()')
        self.ignore('resumeAfterReward')
        self.movie.resetReward(finish=1)
        self._removeMembersKeep()
        NametagGlobals.setMasterArrowsOn(1)
        Emote.globalEmote.releaseAll(base.localAvatar, 'dbattle, exitReward')

    def enterResume(self, ts = 0):
        self.notify.debug('enterResume()')
        if self.hasLocalToon():
            self.removeLocalToon()
        if self.interactiveProp:
            self.interactiveProp.requestIdleOrSad()

    def exitResume(self):
        pass

    def enterNoLocalToon(self):
        self.notify.debug('enterNoLocalToon()')
        self.enableCollision()

    def exitNoLocalToon(self):
        self.disableCollision()

    def enterWaitForServer(self):
        self.notify.debug('enterWaitForServer()')

    def exitWaitForServer(self):
        pass
