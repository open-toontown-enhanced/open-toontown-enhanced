from toontown.cog import DistributedFactoryCogAI
from direct.directnotify import DirectNotifyGlobal

class DistributedStageCogAI(DistributedFactoryCogAI.DistributedFactoryCogAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageCogAI')

    def isForeman(self):
        return 0

    def isSupervisor(self):
        return self.boss

    def isVirtual(self):
        return self.virtual
