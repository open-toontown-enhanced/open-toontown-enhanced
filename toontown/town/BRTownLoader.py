from . import TownLoader
from . import BRStreet
from toontown.cog import Cog

class BRTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = BRStreet.BRStreet
        self.musicFile = 'phase_8/audio/bgm/TB_SZ.ogg'
        self.activityMusicFile = 'phase_8/audio/bgm/TB_SZ_activity.ogg'
        self.townStorageDNAFile = 'phase_8/dna/storage_BR_town.dna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Cog.loadCogs(3)
        dnaFile = 'phase_8/dna/the_burrrgh_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

    def unload(self):
        Cog.unloadCogs(3)
        TownLoader.TownLoader.unload(self)
