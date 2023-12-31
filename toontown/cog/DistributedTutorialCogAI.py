from otp.ai.AIBaseGlobal import *

from direct.directnotify import DirectNotifyGlobal
from toontown.battle import CogBattleGlobals
from . import DistributedCogBaseAI


class DistributedTutorialCogAI(DistributedCogBaseAI.DistributedCogBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory(
                                        'DistributedTutorialCogAI')

    def __init__(self, air, cogPlanner):
        """__init__(air, cogPlanner)"""
        DistributedCogBaseAI.DistributedCogBaseAI.__init__(self, air, 
                                                             cogPlanner)

    def delete(self):
        DistributedCogBaseAI.DistributedCogBaseAI.delete(self)
        self.ignoreAll()

    def requestBattle(self, x, y, z, h, p, r):
        """requestBattle(x, y, z, h, p, r)
        """
        toonId = self.air.getAvatarIdFromSender()

        if self.notify.getDebug():
            self.notify.debug( str( self.getDoId() ) + \
                               str( self.zoneId ) + \
                               ': request battle with toon: %d' % toonId )

        # Store the cog's actual pos and hpr on the client
        self.confrontPos = Point3(x, y, z)
        self.confrontHpr = Vec3(h, p, r)

        # Request a battle from the cog planner
        if (self.sp.requestBattle(self.zoneId, self, toonId)):
            self.acceptOnce(self.getDeathEvent(), self._logDeath, [toonId])
            if self.notify.getDebug():
                self.notify.debug( "Cog %d requesting battle in zone %d" %
                                   (self.getDoId(), self.zoneId) )
        else:
            # Cog tells toon to get lost
            if self.notify.getDebug():
                self.notify.debug('requestBattle from cog %d - denied by battle manager' % (self.getDoId()))
            self.b_setBrushOff(CogDialog.getBrushOffIndex(self.getStyleName()))
            self.d_denyBattle( toonId )

    def getConfrontPosHpr(self):
        """ getConfrontPosHpr()
        """
        return (self.confrontPos, self.confrontHpr)

    def _logDeath(self, toonId):
        self.air.writeServerEvent('beatFirstCog', toonId, '')