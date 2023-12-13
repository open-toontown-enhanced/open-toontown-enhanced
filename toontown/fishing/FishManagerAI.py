from typing import Optional, Union
from toontown.fishing.FishGlobals import *
from toontown.fishing.FishBase import FishBase
from toontown.toonbase import ToontownGlobals
from toontown.toon.DistributedToonAI import DistributedToonAI
import random

# TODO: bingo!
class FishManagerAI:

    def __init__(self, air):
        self.air = air

    def creditFishTank(self, av: DistributedToonAI) -> bool:
        oldBonus: int = int(len(av.fishCollection) / FISH_PER_BONUS)

        # give the avatar jellybeans equal to the value of the tank
        value: int = av.fishTank.getTotalValue()
        av.addMoney(value)
        # update the avatar's fish collection...
        for fish in av.fishTank.fishList:
            av.fishCollection.collectFish(fish)
        # now clear the fish tank
        av.b_setFishTank([], [], [])
        # update the avatar's fish collection in the database
        av.d_setFishCollection(*av.fishCollection.getNetLists())

        newBonus = int(len(av.fishCollection) / FISH_PER_BONUS)
        if newBonus > oldBonus:
            oldMaxHp: int = av.getMaxHp()
            newMaxHp: int = min(ToontownGlobals.MaxHpLimit, oldMaxHp + newBonus - oldBonus)
            av.b_setMaxHp(newMaxHp)
            av.toonUp(newMaxHp)
            # give the avatar a new trophy!
            newTrophies: list[int] = av.getFishingTrophies()
            trophyId: int = len(newTrophies)
            newTrophies.append(trophyId)
            av.b_setFishingTrophies(newTrophies)
            return True
        return False

    def getItem(self, av: DistributedToonAI, zoneId: int) -> tuple[Optional[int], Union[FishBase, int, None]]:
        avId: int = av.getDoId()
        rodId: int = av.getFishingRod()

        itemType: int | None = None
        item: FishBase | int | None = self.air.questManager.findItemInWater(av, zoneId)
        if item:
            itemType = QuestItem
        else:
            rand: int = random.random() * 100.0
            for cutoff in SortedProbabilityCutoffs:
                if rand <= cutoff:
                    itemType = ProbabilityDict[cutoff]
                    break

        if itemType == FishItem:
            fishVitals: tuple[bool, int, int, int] = getRandomFishVitals(zoneId, rodId)
            if fishVitals[0]:
                item = FishBase(fishVitals[1], fishVitals[2], fishVitals[3])
                inTankHasBigger: tuple[bool, bool] = av.fishTank.hasFish(fishVitals[1], fishVitals[2], fishVitals[3])
                added = av.addFishToTank(item)
                if added:
                    collectResult = av.fishCollection.getCollectResult(item)
                    if collectResult == COLLECT_NEW_ENTRY:
                        if not inTankHasBigger[0]:
                            itemType = FishItemNewEntry
                        elif not inTankHasBigger[1]:
                            itemType = FishItemNewRecord
                    elif collectResult == COLLECT_NEW_RECORD and not inTankHasBigger[1]:
                        itemType = FishItemNewRecord
                else:
                    itemType = OverTankLimit
            else:
                itemType = BootItem
        elif itemType == JellybeanItem:
            item = Rod2JellybeanDict[rodId]
            av.addMoney(item)

        return (itemType, item)