from typing import Union
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedNodeAI import DistributedNodeAI
from direct.distributed.ClockDelta import *
from direct.task.Task import Task
from . import FishingTargetGlobals
import random, math

class DistributedFishingTargetAI(DistributedNodeAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFishingTargetAI')

    def __init__(self, air, pond):
        DistributedNodeAI.__init__(self, air)
        self.pondDoId: int = pond.getDoId()
        self.angle: float = 0.0
        self.radius: float = 0.0
        self.time: float = 0.0

        self.targetCenter: tuple[float, float, float] = FishingTargetGlobals.getTargetCenter(pond.getArea())
        self.targetRadius: float = FishingTargetGlobals.getTargetRadius(pond.getArea())

    def generate(self):
        DistributedNodeAI.generate(self)
        self.moveFishingTarget()

    def delete(self):
        self.removeTask(self.uniqueName('moveFishingTarget'))
        DistributedNodeAI.delete(self)

    def getPondDoId(self) -> float:
        return self.pondDoId

    def getState(self) -> list[float, float, float, int]:
        return [self.angle, self.radius, self.time, globalClockDelta.getRealNetworkTime()]

    def moveFishingTarget(self, task: Union[Task, None] = None):
        # Send the current position.
        self.d_setPos(
            (self.radius * math.cos(self.angle)) + self.targetCenter[0], # x
            (self.radius * math.sin(self.angle)) + self.targetCenter[1], # y
            self.targetCenter[2]                                         # z
        )
        # Make the new angle and radius
        self.angle = random.random() * 360
        self.radius = random.random() * self.targetRadius
        # Pick the travel duration
        self.time = 6.0 * (6.0 * random.random())
        # Send our new information to the clients...
        self.sendUpdate('setState', self.getState())
        # Move the target again in x seconds
        self.doMethodLater(self.time + (1.0 + random.random() * 4.0), 
                           self.moveFishingTarget,
                           self.uniqueName('moveFishingTarget'))
