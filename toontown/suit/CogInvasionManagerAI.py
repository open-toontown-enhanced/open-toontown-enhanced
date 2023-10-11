from typing import Optional
from panda3d.core import ConfigVariableInt
from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.task import Task
from toontown.battle import SuitBattleGlobals
import random

class CogInvasionManagerAI(DirectObject):
    notify = directNotify.newCategory('CogInvasionManagerAI')
    # Invasions may contain x number of Cogs randomly picked from this tuple.
    INVADING_NUM_LIST = (1000, 2000, 3000, 4000)
    # No more than one invasion every 2 days (by default).
    INVASION_MIN_DELAY = ConfigVariableInt('invasion-min-delay', 172800).getValue()
    # At least one invasion every 7 days (by default).
    INVASION_MAX_DELAY = ConfigVariableInt('invasion-max-delay', 604800).getValue()
    INVADING_COG_TYPES = (
        # Bossbots
        'flunky',
        'head_hunter',
        'corporate_raider',
        # Sellbots
        'two_face',
        'the_mingler',
        # Cashbots
        'money_bags',
        'loan_shark',
        # Lawbots
        'spin_doctor',
        'legal_eagle'
    )

    def __init__(self, air):
        DirectObject.__init__(self)
        self.air = air

        self.totalNumCogs: int = 0
        self.numCogsRemaining: int = 0
        self.isInvading: bool = False
        self.cogType: str | None = None
        self.isSkelecog: bool = False

        self.waitForNextInvasion()

    def computeInvasionDelay(self) -> float:
        # Compute the invasion delay until the next invasion.
        return (self.INVASION_MAX_DELAY - self.INVASION_MIN_DELAY) * random.random() \
                + self.INVASION_MIN_DELAY

    def tryInvasionAndWaitForNext(self, task: Task) -> Task.done:
        # Start the invasion if there is not one already
        if self.getInvading():
            self.notify.warning("invasionTask: tried to start random invasion, but one is in progress")
        else:
            self.notify.info("invasionTask: starting random invasion")
            cogType = random.choice(self.INVADING_COG_TYPES)
            totalNumCogs = random.choice(self.INVADING_NUM_LIST)
            self.startInvasion(cogType, totalNumCogs)
        # In either case, fire off the next invasion
        self.waitForNextInvasion()
        return Task.done

    def waitForNextInvasion(self):
        self.removeTask("cogInvasionMgr")
        delay = self.computeInvasionDelay()
        self.notify.info("invasionTask: waiting %s seconds until next invasion" % delay)
        self.doMethodLater(delay, self.tryInvasionAndWaitForNext,
                           "cogInvasionMgr")

    def getInvading(self) -> bool:
        return self.isInvading

    def getCogType(self) -> tuple[str, bool]:
        return (self.cogType, self.isSkelecog)

    def getNumCogsRemaining(self) -> int:
        return self.numCogsRemaining

    def getTotalNumCogs(self) -> int:
        return self.totalNumCogs

    def startInvasion(self, cogType: str, totalNumCogs: int, skeleton: bool = False) -> bool:
        if self.isInvading:
            self.notify.warning(f"startInvasion: already invading cogType: {cogType} numCogsRemaining: {self.numCogsRemaining}")
            return False
        if not SuitBattleGlobals.SuitAttributes.get(cogType):
            self.notify.warning(f"startInvasion: unknown cogType: {cogType}")
            return False

        self.notify.info(f"startInvasion: cogType: {cogType} totalNumCogs: {totalNumCogs} skeleton: {skeleton}")
        self.isInvading = True
        self.cogType = cogType
        self.isSkeleton = skeleton
        self.totalNumCogs = totalNumCogs
        self.numCogsRemaining = self.totalNumCogs

        # Tell the news manager that an invasion is beginning
        self.air.newsManager.invasionBegin(self.cogType, self.totalNumCogs, self.isSkeleton)

        # Get rid of all the current cogs on the streets
        # (except those already in battle, they can stay)
        for suitPlanner in self.air.suitPlanners.values():
            suitPlanner.flySuits()
        # Success!
        return True

    def getInvadingCog(self) -> tuple[Optional[str], Optional[bool]]:
        if self.isInvading:
            self.notify.debug(f"getInvadingCog: returned cog: {self.cogType}, num remaining: {self.numCogsRemaining}")
            return (self.cogType, self.isSkeleton)
        else:
            self.notify.debug("getInvadingCog: not currently invading")
            return (None, None)

    def subtractNumCogsRemaining(self, amount: int):
        if self.isInvading:
            self.numCogsRemaining -= amount
            if self.numCogsRemaining <= 0:
                self.stopInvasion()

    def stopInvasion(self):
        self.notify.info("stopInvasion: invasion is over now")
        # Tell the news manager that an invasion is ending
        self.air.newsManager.invasionEnd(self.cogType, 0, self.isSkeleton)
        self.isInvading = 0
        self.cogType = None
        self.isSkeleton = 0
        self.totalNumCogs = 0
        self.numCogsRemaining = 0
        # Get rid of all the current invasion cogs on the streets
        # (except those already in battle, they can stay)
        for suitPlanner in self.air.suitPlanners.values():
            suitPlanner.flySuits()
