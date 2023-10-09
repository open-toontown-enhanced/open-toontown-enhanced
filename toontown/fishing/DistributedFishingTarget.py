from panda3d.core import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedNode import DistributedNode
from direct.distributed.DistributedObject import DistributedObject
from direct.actor import Actor
from . import FishingTargetGlobals
import math
from toontown.effects import Bubbles

class DistributedFishingTarget(DistributedNode):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFishingTarget')
    radius = 2.5

    def __init__(self, cr):
        DistributedNode.__init__(self, cr)
        NodePath.__init__(self)
        self.pond: DistributedObject | None = None
        self.centerPoint: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.maxRadius: float = 1.0
        self.track: Sequence = None

    def generate(self):
        self.assign(render.attachNewNode('DistributedFishingTarget'))
        shadow = loader.loadModel('phase_3/models/props/drop_shadow')
        shadow.setPos(0, 0, -0.1)
        shadow.setScale(0.33)
        shadow.setColorScale(1, 1, 1, 0.75)
        shadow.reparentTo(self)
        self.bubbles = Bubbles.Bubbles(self, render)
        self.bubbles.renderParent.setDepthWrite(0)
        self.bubbles.start()
        DistributedNode.generate(self)

    def disable(self):
        if self.track:
            self.track.finish()
            self.track = None
        self.bubbles.destroy()
        del self.bubbles
        self.pond.removeTarget(self)
        self.pond = None
        DistributedNode.disable(self)

    def delete(self):
        del self.pond
        DistributedNode.delete(self)

    def setPondDoId(self, pondDoId: int):
        self.pond = base.cr.doId2do[pondDoId]
        self.pond.addTarget(self)
        self.centerPoint = FishingTargetGlobals.getTargetCenter(self.pond.getArea())
        self.maxRadius = FishingTargetGlobals.getTargetRadius(self.pond.getArea())

    def getDestPos(self, angle: float, radius: float) -> tuple[float, float, float]:
        x = radius * math.cos(angle) + self.centerPoint[0]
        y = radius * math.sin(angle) + self.centerPoint[1]
        z = self.centerPoint[2]
        return (x, y, z)

    def setState(self, angle: float, radius: float, time: float, timeStamp: int):
        ts = globalClockDelta.localElapsedTime(timeStamp)
        pos = self.getDestPos(angle, radius)
        if self.track and self.track.isPlaying():
            self.track.finish()
        self.track = Sequence(LerpPosInterval(self, time - ts, Point3(*pos), blendType='easeInOut'))
        self.track.start()

    def getRadius(self) -> float:
        return self.radius
