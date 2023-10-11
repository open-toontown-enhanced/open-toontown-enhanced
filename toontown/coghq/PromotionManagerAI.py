from otp.ai.AIBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
import random
from toontown.cog import CogDNA
from . import CogDisguiseGlobals
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toonbase.ToontownBattleGlobals import getInvasionMultiplier
from functools import reduce
MeritMultiplier = 0.5

class PromotionManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('PromotionManagerAI')

    def __init__(self, air):
        self.air = air

    def getPercentChance(self) -> float:
        return 100.0

    def recoverMerits(self, av: DistributedToonAI, cogList: dict, zoneId: int, multiplier: float = 1.0,
                      extraMerits: list[int, int, int, int] = [0, 0, 0, 0]):
        avId = av.getDoId()
        meritsRecovered = [0, 0, 0, 0]
        if self.air.cogInvasionManager.getInvading():
            multiplier *= getInvasionMultiplier()
        for i in range(len(extraMerits)):
            if CogDisguiseGlobals.isSuitComplete(av.getCogParts(), i):
                meritsRecovered[i] += extraMerits[i]
                self.notify.debug(f'recoverMerits: extra merits = {extraMerits[i]}')

        self.notify.debug(f'recoverMerits: multiplier = {multiplier}')
        for cogDict in cogList:
            dept = CogDNA.suitDepts.index(cogDict['track'])
            if avId in cogDict['activeToons']:
                if CogDisguiseGlobals.isSuitComplete(av.getCogParts(), CogDNA.suitDepts.index(cogDict['track'])):
                    self.notify.debug(f'recoverMerits: checking against cogDict: {cogDict}')
                    rand = random.random() * 100
                    if rand <= self.getPercentChance() and not cogDict['isVirtual']:
                        merits = cogDict['level'] * MeritMultiplier
                        merits = int(round(merits))
                        if cogDict['hasRevives']:
                            merits *= 2
                        merits = merits * multiplier
                        merits = int(round(merits))
                        meritsRecovered[dept] += merits
                        self.notify.debug(f'recoverMerits: merits = {merits}')
                    else:
                        self.notify.debug('recoverMerits: virtual cog!')

        if meritsRecovered != [0, 0, 0, 0]:
            actualCounted = [0, 0, 0, 0]
            merits = av.getCogMerits()
            for i in range(len(meritsRecovered)):
                max = CogDisguiseGlobals.getTotalMerits(av, i)
                if max:
                    if merits[i] + meritsRecovered[i] <= max:
                        actualCounted[i] = meritsRecovered[i]
                        merits[i] += meritsRecovered[i]
                    else:
                        actualCounted[i] = max - merits[i]
                        merits[i] = max
                    av.b_setCogMerits(merits)

            if reduce(lambda x, y: x + y, actualCounted):
                self.air.writeServerEvent('merits', avId, f'{actualCounted[0]}|{actualCounted[1]}|{actualCounted[2]}|{actualCounted[3]}')
                self.notify.debug(f'recoverMerits: av {avId} recovered merits {actualCounted}')
        return meritsRecovered
