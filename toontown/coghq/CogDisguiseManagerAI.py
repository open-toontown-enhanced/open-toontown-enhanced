from otp.ai.AIBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
import random
from toontown.cog import CogDNA
from . import CogDisguiseGlobals

class CogDisguiseManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('CogDisguiseManagerAI')

    def __init__(self, air):
        self.air = air

    def recoverPart(self, av, factoryType, cogTrack, zoneId, avList):
        partsRecovered = [
         0, 0, 0, 0]
        part = av.giveGenericCogPart(factoryType, cogTrack)
        if part:
            partsRecovered[CogDisguiseGlobals.dept2deptIndex(cogTrack)] = part
            self.air.questManager.toonRecoveredCogDisguisePart(av, zoneId, avList)
        return partsRecovered
