from . import TownLoader
from . import MMStreet
from toontown.cog import Cog

class MMTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = MMStreet.MMStreet
        self.musicFile = 'phase_6/audio/bgm/MM_SZ.ogg'
        self.activityMusicFile = 'phase_6/audio/bgm/MM_SZ_activity.ogg'
        self.townStorageDNAFile = 'phase_6/dna/storage_MM_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Cog.loadCogs(2)
        dnaFile = 'phase_6/dna/minnies_melody_land_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Cog.unloadCogs(2)
        TownLoader.TownLoader.unload(self)
