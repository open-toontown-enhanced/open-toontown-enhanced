from panda3d.core import Point3, VBase4
from direct.fsm.FSM import FSM
from direct.interval.IntervalGlobal import Sequence, Parallel, ActorInterval, Func, Wait, ParticleInterval, Track, LerpColorScaleInterval, LerpScaleInterval, LerpHprInterval
from direct.task.Task import Task
from toontown.battle import BattleParticles
from toontown.battle import MovieUtil
from toontown.minigame.MazeCog import MazeCog
from .CogdoMazeGameObjects import CogdoMazeSplattable
from . import CogdoMazeGameGlobals as Globals
import random

class CogdoMazeCog(MazeCog, FSM, CogdoMazeSplattable):
    GagHitEventName = 'CogdoMazeCog_GagHit'
    DeathEventName = 'CogdoMazeCog_Death'
    ThinkEventName = 'CogdoMazeCog_Think'

    def __init__(self, serialNum, maze, randomNumGen, difficulty, startTile, cogdoCogType, walkAnimName = None):
        data = Globals.CogData[cogdoCogType]
        MazeCog.__init__(self, serialNum, maze, randomNumGen, data['cellWalkPeriod'], difficulty, data['dnaName'], startTile=startTile, walkSameDirectionProb=Globals.CogWalkSameDirectionProb, walkTurnAroundProb=Globals.CogWalkTurnAroundProb, uniqueRandomNumGen=False, walkAnimName=walkAnimName)
        FSM.__init__(self, 'CogdoMazeCog')
        CogdoMazeSplattable.__init__(self, self.cog, '%s-%i' % (Globals.CogCollisionName, self.serialNum), 1.5)
        if 'scale' in data:
            self.cog.setScale(data['scale'])
        self.hp = data['hp']
        self.type = cogdoCogType
        self.memos = data['memos']
        self.deathCog = self.cog.getLoseActor()
        self.deathCog.pose('lose', 0)
        BattleParticles.loadParticles()
        self._initSfx()

    def _initSfx(self):
        audioMgr = base.cogdoGameAudioMgr
        self._deathSoundIval = Sequence(audioMgr.createSfxIval('cogSpin', duration=1.6, startTime=0.6, volume=0.8, source=self.deathCog), audioMgr.createSfxIval('cogDeath', volume=0.32, source=self.deathCog))

    def _destroySfx(self):
        if self._deathSoundIval.isPlaying():
            self._deathSoundIval.finish()
        del self._deathSoundIval

    def destroy(self):
        BattleParticles.unloadParticles()
        self.ignoreAll()
        self._destroySfx()
        CogdoMazeSplattable.destroy(self)
        MazeCog.destroy(self)

    def handleEnterSphere(self, collEntry):
        messenger.send(self.COLLISION_EVENT_NAME, [self.type, self.serialNum])

    def gameStart(self, gameStartTime):
        MazeCog.gameStart(self, gameStartTime)
        self.accept(Globals.GagCollisionName + '-into-' + self.gagCollisionName, self.handleGagHit)
        messenger.send(self.ThinkEventName, [self, self.TX, self.TY])

    def initCollisions(self):
        MazeCog.initCollisions(self)
        self.collNodePath.setScale(0.75)
        self.accept(self.uniqueName('again' + self.COLL_SPHERE_NAME), self.handleEnterSphere)

    def think(self, curTic, curT, unwalkables):
        MazeCog.think(self, curTic, curT, unwalkables)
        messenger.send(self.ThinkEventName, [self, self.TX, self.TY])

    def handleGagHit(self, collEntry):
        gagNodePath = collEntry.getFromNodePath().getParent()
        messenger.send(self.GagHitEventName, [self.type, self.serialNum, gagNodePath])

    def _getCogAnimationIval(self, animName, startFrame = 0, duration = 1, partName = None, nextState = None):
        totalFrames = self.cog.getNumFrames(animName)
        frames = totalFrames - 1 - startFrame
        frameRate = self.cog.getFrameRate(animName)
        newRate = frames / duration
        playRate = newRate / frameRate
        ival = Sequence(ActorInterval(self.cog, animName, startTime=startFrame / newRate, endTime=totalFrames / newRate, playRate=playRate, partName=partName))
        if nextState is not None:

            def done():
                self.request(nextState)

            ival.append(Func(done))
        return ival

    def hitByGag(self):
        self.hp = self.hp - 1
        self.doSplat()
        if self.hp <= 0:
            self.explode()

    def explode(self):
        self.doDeathTrack()
        messenger.send(self.DeathEventName, [self.type, self.serialNum])

    def doDeathTrack(self):

        def removeDeathCog(cog, deathCog):
            if not deathCog.isEmpty():
                deathCog.detachNode()
                cog.cleanupLoseActor()

        self.deathCog.reparentTo(self.cog.getParent())
        self.deathCog.setScale(self.cog.getScale())
        self.deathCog.setPos(render, self.cog.getPos(render))
        self.deathCog.setHpr(render, self.cog.getHpr(render))
        self.cog.hide()
        self.collNodePath.reparentTo(self.deathCog)
        gearPoint = Point3(0, 0, self.cog.height / 2.0 + 2.0)
        smallGears = BattleParticles.createParticleEffect(file='gearExplosionSmall')
        singleGear = BattleParticles.createParticleEffect('GearExplosion', numParticles=1)
        smallGearExplosion = BattleParticles.createParticleEffect('GearExplosion', numParticles=10)
        bigGearExplosion = BattleParticles.createParticleEffect('BigGearExplosion', numParticles=30)
        smallGears.setPos(gearPoint)
        singleGear.setPos(gearPoint)
        smallGearExplosion.setPos(gearPoint)
        bigGearExplosion.setPos(gearPoint)
        smallGears.setDepthWrite(False)
        singleGear.setDepthWrite(False)
        smallGearExplosion.setDepthWrite(False)
        bigGearExplosion.setDepthWrite(False)
        cogTrack = Sequence(Func(self.collNodePath.stash), ActorInterval(self.deathCog, 'lose', startFrame=80, endFrame=140), Func(removeDeathCog, self.cog, self.deathCog, name='remove-death-cog'))
        explosionTrack = Sequence(Wait(1.5), MovieUtil.createKapowExplosionTrack(self.deathCog, explosionPoint=gearPoint))
        gears1Track = Sequence(ParticleInterval(smallGears, self.deathCog, worldRelative=0, duration=4.3, cleanup=True), name='gears1Track')
        gears2MTrack = Track((0.0, explosionTrack), (0.7, ParticleInterval(singleGear, self.deathCog, worldRelative=0, duration=5.7, cleanup=True)), (5.2, ParticleInterval(smallGearExplosion, self.deathCog, worldRelative=0, duration=1.2, cleanup=True)), (5.4, ParticleInterval(bigGearExplosion, self.deathCog, worldRelative=0, duration=1.0, cleanup=True)), name='gears2MTrack')

        def removeParticle(particle):
            if particle and hasattr(particle, 'renderParent'):
                particle.cleanup()
                del particle

        removeParticles = Sequence(Func(removeParticle, smallGears), Func(removeParticle, singleGear), Func(removeParticle, smallGearExplosion), Func(removeParticle, bigGearExplosion))
        self.deathTrack = Sequence(Parallel(cogTrack, gears2MTrack, gears1Track, self._deathSoundIval), removeParticles)
        self.deathTrack.start()


class CogdoMazeSlowMinionCog(CogdoMazeCog):

    def __init__(self, serialNum, maze, randomNumGen, difficulty, startTile = None):
        CogdoMazeCog.__init__(self, serialNum, maze, randomNumGen, difficulty, startTile, Globals.CogTypes.SlowMinion)
        self.defaultTransitions = {'Off': ['Normal'],
         'Normal': ['Attack', 'Off'],
         'Attack': ['Normal']}

    def gameStart(self, gameStartTime):
        CogdoMazeCog.gameStart(self, gameStartTime)
        self.request('Normal')

    def enterNormal(self):
        self.startWalkAnim()

    def exitNormal(self):
        pass

    def enterAttack(self, elapsedTime):
        self._attackIval = self._getCogAnimationIval('finger-wag', duration=2.0, nextState='Normal')
        self._attackIval.start(elapsedTime)

    def filterAttack(self, request, args):
        if request == 'Attack':
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitAttack(self):
        self._attackIval.pause()
        del self._attackIval


class CogdoMazeFastMinionCog(CogdoMazeCog):

    def __init__(self, serialNum, maze, randomNumGen, difficulty, startTile = None):
        CogdoMazeCog.__init__(self, serialNum, maze, randomNumGen, difficulty, startTile, Globals.CogTypes.FastMinion)


class CogdoMazeBossCog(CogdoMazeCog):
    BlinkTaskName = 'CogdoMazeBossBlinkTask'
    ShakeTaskName = 'CogdoMazeBossShakeTask'
    StartWalkTaskName = 'CogdoMazeBossStartWalkTask'
    ShakeEventName = 'CogdoMazeCogShake'

    def __init__(self, serialNum, maze, randomNumGen, difficulty, startTile = None):
        CogdoMazeCog.__init__(self, serialNum, maze, randomNumGen, difficulty, startTile, Globals.CogTypes.Boss, walkAnimName='stomp')
        self.dropTimer = 0
        self._walkSpeed = float(self.maze.cellWidth) / self.cellWalkDuration * 0.5

    def _initSfx(self):
        CogdoMazeCog._initSfx(self)
        audioMgr = base.cogdoGameAudioMgr
        self._stompSfxIval = audioMgr.createSfxIval('cogStomp', source=self.cog, cutoff=Globals.BossStompSfxCutoff, volume=0.3)
        self._hitSfx = audioMgr.createSfx('bossCogAngry', self.cog)

    def _destroySfx(self):
        del self._hitSfx
        if self._stompSfxIval.isPlaying():
            self._stompSfxIval.finish()
        del self._stompSfxIval
        CogdoMazeCog._destroySfx(self)

    def spin(self):
        part = self.cog
        time = Globals.BossSpinTime
        degrees = 360 * Globals.BossSpinCount
        spinIval = LerpHprInterval(part, time, (self.cog.getH() + degrees, 0, 0), blendType='easeOut')
        spinIval.start()

    def hitByGag(self):
        if self.hp >= 2:
            self._hitSfx.play()
            self.spin()
            self.cog.setColorScale(Globals.BlinkColor)
            self.__startBlinkTask()
        elif self.hp == 1:
            self.__stopBlinkTask()
        CogdoMazeCog.hitByGag(self)

    def gameStart(self, gameStartTime):
        CogdoMazeCog.gameStart(self, gameStartTime)

    def startWalkAnim(self):
        self.cog.loop(self._walkAnimName, fromFrame=43, toFrame=81)
        self.cog.setPlayRate(self._walkSpeed * Globals.BossCogStompAnimationPlayrateFactor, self._walkAnimName)
        self.__startShakeTask()

    def destroy(self):
        CogdoMazeCog.destroy(self)
        self.__stopShakeTask()
        self.__stopBlinkTask()

    def pickRandomValidSpot(self, r = 5):
        validSpots = []
        for x in range(self.TX - r, self.TX + r):
            for y in range(self.TY - r, self.TY + r):
                if self.maze.isWalkable(x, y):
                    validSpots.append([x, y])

        return self.rng.choice(validSpots)

    def __startShakeTask(self):
        self.__stopShakeTask()
        taskMgr.doMethodLater(Globals.BossShakeTime, self.__shake, self.uniqueName(CogdoMazeBossCog.ShakeTaskName))
        self.bossShakeLastTime = 0

    def __stopShakeTask(self):
        taskMgr.remove(self.uniqueName(CogdoMazeBossCog.ShakeTaskName))

    def __shake(self, task):
        if task.time - self.bossShakeLastTime > Globals.BossShakeTime:
            self.cog.setPlayRate(self._walkSpeed * Globals.BossCogStompAnimationPlayrateFactor, self._walkAnimName)
            self._stompSfxIval.start()
            messenger.send(self.ShakeEventName, [self, Globals.BossShakeStrength])
            self.bossShakeLastTime = task.time
        return task.cont

    def __startBlinkTask(self):
        self.__stopBlinkTask()
        taskMgr.doMethodLater(Globals.BlinkFrequency, self.__blink, CogdoMazeBossCog.BlinkTaskName)

    def __stopBlinkTask(self):
        taskMgr.remove(CogdoMazeBossCog.BlinkTaskName)

    def __blink(self, task):
        blink = Sequence(LerpColorScaleInterval(self.cog, Globals.BlinkSpeed, VBase4(1.0, 1.0, 1.0, 1.0)), LerpColorScaleInterval(self.cog, Globals.BlinkSpeed, Globals.BlinkColor))
        blink.start()
        return Task.again
