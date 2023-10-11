from toontown.cog import DistributedFactoryCog
from direct.directnotify import DirectNotifyGlobal

class DistributedMintCog(DistributedFactoryCog.DistributedFactoryCog):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMintCog')
