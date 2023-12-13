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
        self.avsFishingHere: list[int] = []

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

    def addAvId(self, avId: int):
        if avId not in self.avsFishingHere:
            self.avsFishingHere.append(avId)

    def removeAvId(self, avId: int):
        if avId in self.avsFishingHere:
            self.avsFishingHere.remove(avId)

    def hitTarget(self, avId: int):
        senderId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(senderId)
        if not av:
            return
        target = self.targets.get(avId)
        if not target:
            self.air.writeServerEvent('suspicious', senderId, f"Toon tried to hit invalid fishing target: {avId}.")
            return
        if avId not in self.avsFishingHere:
            self.air.writeServerEvent('suspicious', senderId, f'Toon tried to hit a target despite not being in a spot: {avId}.')
            return

    def setArea(self, area: int):
        self.area = area

    def getArea(self) -> int:
        return self.area
