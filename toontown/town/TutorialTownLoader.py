from . import TownLoader
from . import TTTownLoader
from . import TutorialStreet
from toontown.cog import Cog
from toontown.toon import Toon
from toontown.hood import ZoneUtil

class TutorialTownLoader(TTTownLoader.TTTownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TTTownLoader.TTTownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = TutorialStreet.TutorialStreet

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Cog.loadTutorialCog()
        dnaFile = 'phase_3.5/dna/tutorial_street.dna'
        self.createHood(dnaFile, loadStorage=0)
        self.alterDictionaries()

    def loadBattleAnims(self):
        Toon.loadTutorialBattleAnims()

    def unloadBattleAnims(self):
        Toon.unloadTutorialBattleAnims()

    def alterDictionaries(self):
        zoneId = ZoneUtil.tutorialDict['exteriors'][0]
        self.nodeDict[zoneId] = self.nodeDict[20001]
        del self.nodeDict[20001]
