from . import TownLoader
from . import DLStreet
from toontown.cog import Cog

class DLTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = DLStreet.DLStreet
        self.musicFile = 'phase_8/audio/bgm/DL_SZ.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/DL_SZ_activity.ogg'
        self.townStorageDNAFile = 'phase_8/dna/storage_DL_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Cog.loadCogs(3)
        dnaFile = 'phase_8/dna/donalds_dreamland_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Cog.unloadCogs(3)
        TownLoader.TownLoader.unload(self)
