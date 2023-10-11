from toontown.cog import DistributedFactoryCogAI
from direct.directnotify import DirectNotifyGlobal

class DistributedMintCogAI(DistributedFactoryCogAI.DistributedFactoryCogAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMintCogAI')

    def isForeman(self):
        return 0

    def isSupervisor(self):
        return self.boss

    def isVirtual(self):
        return 0
