from . import TownLoader
from . import DGStreet
from toontown.cog import Cog

class DGTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = DGStreet.DGStreet
        self.musicFile = 'phase_8/audio/bgm/DG_SZ.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/DG_SZ.ogg'
        self.townStorageDNAFile = 'phase_8/dna/storage_DG_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Cog.loadCogs(3)
        dnaFile = 'phase_8/dna/daisys_garden_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Cog.unloadCogs(3)
        TownLoader.TownLoader.unload(self)
