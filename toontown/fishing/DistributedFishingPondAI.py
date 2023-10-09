from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from .DistributedFishingTargetAI import DistributedFishingTargetAI
from . import FishingTargetGlobals

class DistributedFishingPondAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFishingPondAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.area: int | None = None
        self.targets: dict[int, DistributedFishingTargetAI] = {}

    def generate(self):
        DistributedObjectAI.generate(self)
        for i in range(FishingTargetGlobals.getNumTargets(self.area)):
            target = DistributedFishingTargetAI(self.air, self)
            target.generateWithRequired(self.zoneId)
            self.targets[target.getDoId()] = target

    def delete(self):
        for target in self.targets.values():
            target.requestDelete()
        del self.targets
        DistributedObjectAI.delete(self)

    def hitTarget(self, doId: int):
        senderId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(senderId)
        if not av:
            return
        target = self.targets.get(doId)
        if not target:
            self.air.writeServerEvent('suspicious', senderId, f"Toon tried to hit invalid fishing target {doId}.")
            return

    def setArea(self, area: int):
        self.area = area

    def getArea(self) -> int:
        return self.area
