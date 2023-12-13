from typing import Optional
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.hood import ZoneUtil
from .DistributedFishingTargetAI import DistributedFishingTargetAI
from . import FishingTargetGlobals

class DistributedFishingPondAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFishingPondAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.area: int | None = None
        self.targets: dict[int, DistributedFishingTargetAI] = {}
        self.canonicalZoneId: int | None = None

    def generate(self):
        DistributedObjectAI.generate(self)
        for i in range(FishingTargetGlobals.getNumTargets(self.area)):
            target = DistributedFishingTargetAI(self.air, self)
            target.generateWithRequired(self.zoneId)
            self.targets[target.getDoId()] = target
        self.canonicalZoneId = ZoneUtil.getCanonicalZoneId(self.zoneId)

    def delete(self):
        for target in self.targets.values():
            target.requestDelete()
        del self.targets
        DistributedObjectAI.delete(self)

    def getTarget(self, targetId: int) -> Optional[DistributedFishingTargetAI]:
        return self.targets.get(targetId, None)

    def setArea(self, area: int):
        self.area = area

    def getArea(self) -> int:
        return self.area
