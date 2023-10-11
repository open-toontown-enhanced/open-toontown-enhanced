from toontown.cog import DistributedFactoryCog
from toontown.cog.Cog import *
from direct.directnotify import DirectNotifyGlobal
from direct.actor import Actor
from otp.avatar import Avatar
from . import CogDNA
from toontown.toonbase import ToontownGlobals
from panda3d.core import *
from toontown.battle import CogBattleGlobals
from direct.task import Task
from toontown.battle import BattleProps
from toontown.toonbase import TTLocalizer
import string

class DistributedStageCog(DistributedFactoryCog.DistributedFactoryCog):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageCog')

    def setCogSpec(self, spec):
        self.spec = spec
        self.setPos(spec['pos'])
        self.setH(spec['h'])
        self.originalPos = spec['pos']
        self.escapePos = spec['pos']
        self.pathEntId = spec['path']
        self.behavior = spec['behavior']
        self.skeleton = spec['skeleton']
        self.boss = spec['boss']
        self.revives = spec.get('revives')
        if self.reserve:
            self.reparentTo(hidden)
        else:
            self.doReparent()
