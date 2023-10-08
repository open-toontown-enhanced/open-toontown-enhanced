from panda3d.core import *
from panda3d.toontown import DNAStorage
from direct.particles.ParticleEffect import ParticleEffect
from direct.fsm.ClassicFSM import ClassicFSM
from direct.task.Task import Task
from . import ToonHood
from toontown.battle import BattleParticles
from toontown.town import BRTownLoader
from toontown.safezone import BRSafeZoneLoader
from toontown.toonbase.ToontownGlobals import *
import random

class BRHood(ToonHood.ToonHood):

    def __init__(self, parentFSM: ClassicFSM, doneEvent: str, dnaStore: DNAStorage, hoodId: int):
        ToonHood.ToonHood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.id: int = TheBrrrgh
        self.townLoaderClass = BRTownLoader.BRTownLoader
        self.safeZoneLoaderClass = BRSafeZoneLoader.BRSafeZoneLoader
        self.storageDNAFile: str = 'phase_8/dna/storage_BR.dna'
        self.holidayStorageDNADict: dict[int, list[str]] = {WINTER_DECORATIONS: ['phase_8/dna/winter_storage_BR.dna'],
         WACKY_WINTER_DECORATIONS: ['phase_8/dna/winter_storage_BR.dna'],
         HALLOWEEN_PROPS: ['phase_8/dna/halloween_props_storage_BR.dna'],
         SPOOKY_PROPS: ['phase_8/dna/halloween_props_storage_BR.dna']}
        self.skyFile: str = 'phase_3.5/models/props/BR_sky'
        self.spookySkyFile: str = 'phase_3.5/models/props/BR_sky'
        self.titleColor: Vec4 = Vec4(0.3, 0.6, 1.0, 1.0)
        self.nextWindTime: float | None = None
        self.wind1Sound: AudioSound | None = None
        self.wind2Sound: AudioSound | None = None
        self.wind3Sound: AudioSound | None = None
        self.snow: ParticleEffect | None = None
        self.snowRender: NodePath | None = None

    def load(self):
        ToonHood.ToonHood.load(self)
        self.wind1Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_1.ogg')
        self.wind2Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_2.ogg')
        self.wind3Sound = base.loader.loadSfx('phase_8/audio/sfx/SZ_TB_wind_3.ogg')
        self.snow = BattleParticles.loadParticleFile('snowdisk.ptf')
        self.snow.setPos(0, 0, 5)
        self.snowRender = render.attachNewNode('snowRender')
        self.snowRender.setDepthWrite(0)
        self.snowRender.setBin('fixed', 1)
        self.parentFSM.getStateNamed('BRHood').addChild(self.fsm)

    def unload(self):
        self.snow.cleanup()
        del self.wind1Sound
        del self.wind2Sound
        del self.wind3Sound
        del self.snow
        del self.snowRender
        self.parentFSM.getStateNamed('BRHood').removeChild(self.fsm)
        ToonHood.ToonHood.unload(self)

    def startSnowAndWind(self):
        self.snow.start(base.camera, self.snowRender)
        self.nextWindTime = 0.0
        self.addTask(self.__windTask, 'tbr-wind')

    def stopSnowAndWind(self):
        self.removeTask('tbr-wind')
        self.snow.disable()

    def __windTask(self, task) -> Task.cont:
        now = globalClock.getFrameTime()
        if now < self.nextWindTime:
            return Task.cont
        randNum = random.random()
        wind = int(randNum * 100) % 3 + 1
        if wind == 1:
            base.playSfx(self.wind1Sound)
        elif wind == 2:
            base.playSfx(self.wind2Sound)
        elif wind == 3:
            base.playSfx(self.wind3Sound)
        self.nextWindTime = now + randNum * 8.0
        return Task.cont
