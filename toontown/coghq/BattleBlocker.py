from panda3d.core import *
from panda3d.core import *
from direct.interval.IntervalGlobal import *
from otp.level import BasicEntities
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal

class BattleBlocker(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleBlocker')

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)
        self.cogIds = []
        self.battleId = None
        return

    def setActive(self, active):
        self.active = active

    def announceGenerate(self):
        BasicEntities.DistributedNodePathEntity.announceGenerate(self)
        self.initCollisionGeom()

    def disable(self):
        self.ignoreAll()
        self.unloadCollisionGeom()
        BasicEntities.DistributedNodePathEntity.disable(self)

    def destroy(self):
        BasicEntities.DistributedNodePathEntity.destroy(self)

    def setCogs(self, cogIds):
        self.cogIds = cogIds

    def setBattle(self, battleId):
        self.battleId = battleId

    def setBattleFinished(self):
        self.ignoreAll()

    def initCollisionGeom(self):
        self.cSphere = CollisionSphere(0, 0, 0, self.radius)
        self.cSphereNode = CollisionNode('battleBlocker-%s-%s' % (self.level.getLevelId(), self.entId))
        self.cSphereNode.addSolid(self.cSphere)
        self.cSphereNodePath = self.attachNewNode(self.cSphereNode)
        self.cSphereNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.cSphere.setTangible(0)
        self.enterEvent = 'enter' + self.cSphereNode.getName()
        self.accept(self.enterEvent, self.__handleToonEnter)

    def unloadCollisionGeom(self):
        if hasattr(self, 'cSphereNodePath'):
            self.ignore(self.enterEvent)
            del self.cSphere
            del self.cSphereNode
            self.cSphereNodePath.removeNode()
            del self.cSphereNodePath

    def __handleToonEnter(self, collEntry):
        self.notify.debug('__handleToonEnter, %s' % self.entId)
        self.startBattle()

    def startBattle(self):
        if not self.active:
            return
        callback = None
        if self.battleId != None and self.battleId in base.cr.doId2do:
            battle = base.cr.doId2do.get(self.battleId)
            if battle:
                self.notify.debug('act like we collided with battle %d' % self.battleId)
                callback = battle.handleBattleBlockerCollision
        elif len(self.cogIds) > 0:
            for cogId in self.cogIds:
                cog = base.cr.doId2do.get(cogId)
                if cog:
                    self.notify.debug('act like we collided with Cog %d ( in state %s )' % (cogId, cog.fsm.getCurrentState().getName()))
                    callback = cog.handleBattleBlockerCollision
                    break

        self.showReaction(callback)
        return

    def showReaction(self, callback = None):
        if not base.localAvatar.wantBattles:
            return
        track = Sequence()
        if callback:
            track.append(Func(callback))
        track.start()

    if __dev__:

        def attribChanged(self, *args):
            self.unloadCollisionGeom()
            self.initCollisionGeom()
