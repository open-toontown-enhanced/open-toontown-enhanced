from direct.distributed.ClockDelta import globalClockDelta
from toontown.toonbase import TTLocalizer
from .DistCogdoGame import DistCogdoGame
from toontown.cogdominium.DistCogdoMazeGameBase import DistCogdoMazeGameBase
from .CogdoMazeGame import CogdoMazeGame
from .CogdoMaze import CogdoMazeFactory
from . import CogdoMazeGameGlobals
from . import CogdoMazeGameGlobals as Globals

class DistCogdoMazeGame(DistCogdoGame, DistCogdoMazeGameBase):
    notify = directNotify.newCategory('DistCogdoMazeGame')

    def __init__(self, cr):
        DistCogdoGame.__init__(self, cr)
        self.game = CogdoMazeGame(self)
        self._numCogs = (0, 0, 0)
        if __debug__ and base.config.GetBool('schellgames-dev', True):
            self.accept('onCodeReload', self.__sgOnCodeReload)

    def delete(self):
        del self.randomNumGen
        del self.game
        DistCogdoGame.delete(self)

    def getTitle(self):
        return TTLocalizer.CogdoMazeGameTitle

    def getInstructions(self):
        return TTLocalizer.CogdoMazeGameInstructions

    def generate(self):
        self.randomNumGen = self.createRandomNumGen()
        DistCogdoGame.generate(self)

    def placeEntranceElev(self, elev):
        DistCogdoGame.placeEntranceElev(self, elev)
        self.game.placeEntranceElevator(elev)

    def _gameInProgress(self):
        return self.fsm.getCurrentState().getName() == 'Game'

    def enterLoaded(self):
        DistCogdoGame.enterLoaded(self)
        mazeFactory = self.createMazeFactory(self.createRandomNumGen())
        bossCode = None
        if self._numCogs[0] > 0:
            bossCode = ''
            for u in range(self._numCogs[0]):
                bossCode += '%X' % self.randomNumGen.randint(0, 15)

        self.game.load(mazeFactory, self._numCogs, bossCode)
        return

    def exitLoaded(self):
        self.game.unload()
        self.ignoreAll()
        DistCogdoGame.exitLoaded(self)

    def enterVisible(self):
        DistCogdoGame.enterVisible(self)
        self.game.initPlayers()
        self.game.onstage()

    def exitVisible(self):
        DistCogdoGame.exitVisible(self)

    def enterIntro(self):
        DistCogdoGame.enterIntro(self, Globals.IntroDurationSeconds)
        self.game.startIntro()

    def exitIntro(self):
        DistCogdoGame.exitIntro(self)
        self.game.endIntro()
        self.stashEntranceElevator()

    def enterGame(self):
        DistCogdoGame.enterGame(self)
        self.game.start()

    def exitGame(self):
        DistCogdoGame.exitGame(self)
        self.game.exit()

    def enterFinish(self):
        DistCogdoGame.enterFinish(self)
        self.game.startFinish()

    def exitFinish(self):
        DistCogdoGame.exitFinish(self)
        self.game.endFinish()
        self.game.offstage()

    def setNumCogs(self, numCogs):
        self._numCogs = numCogs

    def d_sendRequestAction(self, action, data):
        self.sendUpdate('requestAction', [action, data])

    def toonUsedGag(self, toonId, x, y, h, networkTime):
        if not self._gameInProgress():
            return
        if not self.getToon(base.localAvatar.doId):
            return
        if toonId == localAvatar.doId:
            return
        elapsedTime = globalClockDelta.localElapsedTime(networkTime)
        self.game.toonUsedGag(toonId, x, y, h, elapsedTime)

    def d_requestUseGag(self, x, y, h):
        networkTime = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
        self.sendUpdate('requestUseGag', [x,
         y,
         h,
         networkTime])

    def b_toonUsedGag(self, x, y, h):
        self.d_requestUseGag(x, y, h)
        self.game.toonUsedGag(base.localAvatar.doId, x, y, h)

    def cogHitByGag(self, toonId, cogType, cogNum):
        if not self._gameInProgress():
            return
        if not self.getToon(base.localAvatar.doId):
            return
        if toonId == localAvatar.doId:
            return
        self.game.cogHitByGag(toonId, cogType, cogNum)

    def d_requestSuitHitByGag(self, cogType, cogNum):
        self.sendUpdate('requestSuitHitByGag', [cogType, cogNum])

    def b_cogHitByGag(self, cogType, cogNum):
        self.d_requestSuitHitByGag(cogType, cogNum)
        self.game.cogHitByGag(base.localAvatar.doId, cogType, cogNum)

    def toonHitByGag(self, toonId, hitToon, networkTime):
        if not self._gameInProgress():
            return
        if not self.getToon(base.localAvatar.doId):
            return
        if toonId == localAvatar.doId:
            return
        elapsedTime = globalClockDelta.localElapsedTime(networkTime)
        self.game.toonHitByGag(toonId, hitToon, elapsedTime)

    def d_broadcastSendToonHitByGag(self, toonId):
        pass

    def b_toonHitByGag(self, toonId):
        self.d_broadcastSendToonHitByGag(toonId)
        self.game.toonHitByGag(base.localAvatar.doId, toonId)

    def toonHitBySuit(self, toonId, cogType, cogNum, networkTime):
        if not self._gameInProgress():
            return
        if not self.getToon(base.localAvatar.doId):
            return
        if toonId == localAvatar.doId:
            return
        elapsedTime = globalClockDelta.localElapsedTime(networkTime)
        self.game.toonHitBySuit(toonId, cogType, cogNum, elapsedTime)

    def d_requestHitBySuit(self, cogType, cogNum):
        networkTime = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
        self.sendUpdate('requestHitBySuit', [cogType, cogNum, networkTime])

    def b_toonHitBySuit(self, cogType, cogNum):
        self.d_requestHitBySuit(cogType, cogNum)
        self.game.toonHitBySuit(base.localAvatar.doId, cogType, cogNum)

    def toonHitByDrop(self, toonId):
        if not self._gameInProgress():
            return
        if not self.getToon(base.localAvatar.doId):
            return
        if toonId == localAvatar.doId:
            return
        self.game.toonHitByDrop(toonId)

    def d_requestHitByDrop(self):
        self.sendUpdate('requestHitByDrop', [])

    def b_toonHitByDrop(self):
        self.d_requestHitByDrop()
        self.game.toonHitByDrop(base.localAvatar.doId)

    def d_sendRequestPickUp(self, pickupNum):
        self.sendUpdate('requestPickUp', [pickupNum])

    def pickUp(self, toonId, pickupNum, networkTime):
        if not self._gameInProgress():
            return
        if not self.getToon(base.localAvatar.doId):
            return
        elapsedTime = globalClockDelta.localElapsedTime(networkTime)
        self.game.pickUp(toonId, pickupNum, elapsedTime)

    def d_sendRequestGag(self, waterCoolerIndex):
        self.game.localPlayer.orthoWalk.sendCurrentPosition()
        self.sendUpdate('requestGag', [waterCoolerIndex])

    def hasGag(self, toonId, networkTime):
        if not self._gameInProgress():
            return
        if not self.getToon(base.localAvatar.doId):
            return
        elapsedTime = globalClockDelta.localElapsedTime(networkTime)
        self.game.hasGag(toonId, elapsedTime)

    def doAction(self, action, data, networkTime):
        if not self._gameInProgress():
            return
        if action == Globals.GameActions.RevealDoor:
            self.game.toonRevealsDoor(data)
        elif action == Globals.GameActions.EnterDoor:
            self.game.toonEntersDoor(data)
        elif action == Globals.GameActions.OpenDoor:
            timeLeft = Globals.SecondsUntilGameEnds - globalClockDelta.localElapsedTime(networkTime)
            self.game.openDoor(timeLeft)
        elif action == Globals.GameActions.Countdown:
            countdownTimeLeft = Globals.SecondsUntilTimeout
            self.game.countdown(countdownTimeLeft)
        elif action == Globals.GameActions.TimeAlert:
            self.game.timeAlert()

    def setToonSad(self, toonId):
        DistCogdoGame.setToonSad(self, toonId)
        self.game.handleToonWentSad(toonId)

    def setToonDisconnect(self, toonId):
        DistCogdoGame.setToonDisconnect(self, toonId)
        self.game.handleToonDisconnected(toonId)
