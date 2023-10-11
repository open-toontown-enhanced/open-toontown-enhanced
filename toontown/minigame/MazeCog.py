from direct.showbase.DirectObject import DirectObject
from direct.interval.MetaInterval import Parallel
from direct.interval.LerpInterval import LerpPosInterval, LerpHprInterval
from direct.showbase.RandomNumGen import RandomNumGen
from panda3d.core import Point3
from panda3d.core import CollisionSphere, CollisionNode
from panda3d.direct import WaitInterval
from toontown.cog import Cog
from toontown.cog import CogDNA
from toontown.toonbase import ToontownGlobals
from . import MazeGameGlobals
import functools

class MazeCog(DirectObject):
    COLL_SPHERE_NAME = 'MazeCogSphere'
    COLLISION_EVENT_NAME = 'MazeCogCollision'
    MOVE_IVAL_NAME = 'moveMazeCog'
    DIR_UP = 0
    DIR_DOWN = 1
    DIR_LEFT = 2
    DIR_RIGHT = 3
    oppositeDirections = [DIR_DOWN,
     DIR_UP,
     DIR_RIGHT,
     DIR_LEFT]
    directionHs = [0,
     180,
     90,
     270]
    DEFAULT_SPEED = 4.0
    COG_Z = 0.1

    def __init__(self, serialNum, maze, randomNumGen, cellWalkPeriod, difficulty, CogDNAName = 'flunky', startTile = None, ticFreq = MazeGameGlobals.COG_TIC_FREQ, walkSameDirectionProb = MazeGameGlobals.WALK_SAME_DIRECTION_PROB, walkTurnAroundProb = MazeGameGlobals.WALK_TURN_AROUND_PROB, uniqueRandomNumGen = True, walkAnimName = None):
        self.serialNum = serialNum
        self.maze = maze
        if uniqueRandomNumGen:
            self.rng = RandomNumGen(randomNumGen)
        else:
            self.rng = randomNumGen
        self.difficulty = difficulty
        self._walkSameDirectionProb = walkSameDirectionProb
        self._walkTurnAroundProb = walkTurnAroundProb
        self._walkAnimName = walkAnimName or 'walk'
        self.cog = Cog.Cog()
        d = CogDNA.CogDNA()
        d.newCog(CogDNAName)
        self.cog.setDNA(d)
        if startTile is None:
            defaultStartPos = MazeGameGlobals.COG_START_POSITIONS[self.serialNum]
            self.startTile = (defaultStartPos[0] * self.maze.width, defaultStartPos[1] * self.maze.height)
        else:
            self.startTile = startTile
        self.ticFreq = ticFreq
        self.ticPeriod = int(cellWalkPeriod)
        self.cellWalkDuration = float(self.ticPeriod) / float(self.ticFreq)
        self.turnDuration = 0.6 * self.cellWalkDuration
        return

    def destroy(self):
        self.cog.delete()

    def uniqueName(self, str):
        return str + repr((self.serialNum))

    def gameStart(self, gameStartTime):
        self.gameStartTime = gameStartTime
        self.initCollisions()
        self.startWalkAnim()
        self.occupiedTiles = [(self.nextTX, self.nextTY)]
        n = 20
        self.nextThinkTic = self.serialNum * self.ticFreq // n
        self.fromPos = Point3(0, 0, 0)
        self.toPos = Point3(0, 0, 0)
        self.fromHpr = Point3(0, 0, 0)
        self.toHpr = Point3(0, 0, 0)
        self.moveIval = WaitInterval(1.0)

    def gameEnd(self):
        self.moveIval.pause()
        del self.moveIval
        self.shutdownCollisions()
        self.cog.loop('neutral')

    def initCollisions(self):
        self.collSphere = CollisionSphere(0, 0, 0, 2.0)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.uniqueName(self.COLL_SPHERE_NAME))
        self.collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.cog.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.accept(self.uniqueName('enter' + self.COLL_SPHERE_NAME), self.handleEnterSphere)

    def shutdownCollisions(self):
        self.ignore(self.uniqueName('enter' + self.COLL_SPHERE_NAME))
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode

    def handleEnterSphere(self, collEntry):
        messenger.send(self.COLLISION_EVENT_NAME, [self.serialNum])

    def __getWorldPos(self, sTX, sTY):
        wx, wy = self.maze.tile2world(sTX, sTY)
        return Point3(wx, wy, self.COG_Z)

    def onstage(self):
        sTX = int(self.startTile[0])
        sTY = int(self.startTile[1])
        c = 0
        lim = 0
        toggle = 0
        direction = 0
        while not self.maze.isWalkable(sTX, sTY):
            if 0 == direction:
                sTX -= 1
            elif 1 == direction:
                sTY -= 1
            elif 2 == direction:
                sTX += 1
            elif 3 == direction:
                sTY += 1
            c += 1
            if c > lim:
                c = 0
                direction = (direction + 1) % 4
                toggle += 1
                if not toggle & 1:
                    lim += 1

        self.TX = sTX
        self.TY = sTY
        self.direction = self.DIR_DOWN
        self.lastDirection = self.direction
        self.nextTX = self.TX
        self.nextTY = self.TY
        self.cog.setPos(self.__getWorldPos(self.TX, self.TY))
        self.cog.setHpr(self.directionHs[self.direction], 0, 0)
        self.cog.reparentTo(render)
        self.cog.pose(self._walkAnimName, 0)
        self.cog.loop('neutral')

    def offstage(self):
        self.cog.reparentTo(hidden)

    def startWalkAnim(self):
        self.cog.loop(self._walkAnimName)
        speed = float(self.maze.cellWidth) / self.cellWalkDuration
        self.cog.setPlayRate(speed / self.DEFAULT_SPEED, self._walkAnimName)

    def __applyDirection(self, dir, TX, TY):
        if self.DIR_UP == dir:
            TY += 1
        elif self.DIR_DOWN == dir:
            TY -= 1
        elif self.DIR_LEFT == dir:
            TX -= 1
        elif self.DIR_RIGHT == dir:
            TX += 1
        return (TX, TY)

    def __chooseNewWalkDirection(self, unwalkables):
        if not self.rng.randrange(self._walkSameDirectionProb):
            newTX, newTY = self.__applyDirection(self.direction, self.TX, self.TY)
            if self.maze.isWalkable(newTX, newTY, unwalkables):
                return self.direction
        if self.difficulty >= 0.5:
            if not self.rng.randrange(self._walkTurnAroundProb):
                oppositeDir = self.oppositeDirections[self.direction]
                newTX, newTY = self.__applyDirection(oppositeDir, self.TX, self.TY)
                if self.maze.isWalkable(newTX, newTY, unwalkables):
                    return oppositeDir
        candidateDirs = [self.DIR_UP,
         self.DIR_DOWN,
         self.DIR_LEFT,
         self.DIR_RIGHT]
        candidateDirs.remove(self.oppositeDirections[self.direction])
        while len(candidateDirs):
            dir = self.rng.choice(candidateDirs)
            newTX, newTY = self.__applyDirection(dir, self.TX, self.TY)
            if self.maze.isWalkable(newTX, newTY, unwalkables):
                return dir
            candidateDirs.remove(dir)

        return self.oppositeDirections[self.direction]

    def getThinkTimestampTics(self, curTic):
        if curTic < self.nextThinkTic:
            return []
        else:
            r = list(range(self.nextThinkTic, curTic + 1, self.ticPeriod))
            self.lastTicBeforeRender = r[-1]
            return r

    def prepareToThink(self):
        self.occupiedTiles = [(self.nextTX, self.nextTY)]

    def think(self, curTic, curT, unwalkables):
        self.TX = self.nextTX
        self.TY = self.nextTY
        self.lastDirection = self.direction
        self.direction = self.__chooseNewWalkDirection(unwalkables)
        self.nextTX, self.nextTY = self.__applyDirection(self.direction, self.TX, self.TY)
        self.occupiedTiles = [(self.TX, self.TY), (self.nextTX, self.nextTY)]
        if curTic == self.lastTicBeforeRender:
            fromCoords = self.maze.tile2world(self.TX, self.TY)
            toCoords = self.maze.tile2world(self.nextTX, self.nextTY)
            self.fromPos.set(fromCoords[0], fromCoords[1], self.COG_Z)
            self.toPos.set(toCoords[0], toCoords[1], self.COG_Z)
            self.moveIval = LerpPosInterval(self.cog, self.cellWalkDuration, self.toPos, startPos=self.fromPos, name=self.uniqueName(self.MOVE_IVAL_NAME))
            if self.direction != self.lastDirection:
                self.fromH = self.directionHs[self.lastDirection]
                toH = self.directionHs[self.direction]
                if self.fromH == 270 and toH == 0:
                    self.fromH = -90
                elif self.fromH == 0 and toH == 270:
                    self.fromH = 360
                self.fromHpr.set(self.fromH, 0, 0)
                self.toHpr.set(toH, 0, 0)
                turnIval = LerpHprInterval(self.cog, self.turnDuration, self.toHpr, startHpr=self.fromHpr, name=self.uniqueName('turnMazeCog'))
                self.moveIval = Parallel(self.moveIval, turnIval, name=self.uniqueName(self.MOVE_IVAL_NAME))
            else:
                self.cog.setH(self.directionHs[self.direction])
            moveStartT = float(self.nextThinkTic) / float(self.ticFreq)
            self.moveIval.start(curT - (moveStartT + self.gameStartTime))
        self.nextThinkTic += self.ticPeriod

    @staticmethod
    def thinkCogs(cogList, startTime, ticFreq = MazeGameGlobals.COG_TIC_FREQ):
        curT = globalClock.getFrameTime() - startTime
        curTic = int(curT * float(ticFreq))
        cogUpdates = []
        for i in range(len(cogList)):
            updateTics = cogList[i].getThinkTimestampTics(curTic)
            cogUpdates.extend(list(zip(updateTics, [i] * len(updateTics))))

        cogUpdates.sort(key=functools.cmp_to_key(lambda a, b: a[0] - b[0]))
        if len(cogUpdates) > 0:
            curTic = 0
            for i in range(len(cogUpdates)):
                update = cogUpdates[i]
                tic = update[0]
                cogIndex = update[1]
                cog = cogList[cogIndex]
                if tic > curTic:
                    curTic = tic
                    j = i + 1
                    while j < len(cogUpdates):
                        if cogUpdates[j][0] > tic:
                            break
                        cogList[cogUpdates[j][1]].prepareToThink()
                        j += 1

                unwalkables = []
                for si in range(cogIndex):
                    unwalkables.extend(cogList[si].occupiedTiles)

                for si in range(cogIndex + 1, len(cogList)):
                    unwalkables.extend(cogList[si].occupiedTiles)

                cog.think(curTic, curT, unwalkables)
