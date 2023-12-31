from otp.ai.AIBaseGlobal import *
from otp.avatar import DistributedAvatarAI
from . import CogPlannerBase, CogBase, CogDNA
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import CogBattleGlobals

class DistributedCogBaseAI(DistributedAvatarAI.DistributedAvatarAI, CogBase.CogBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogBaseAI')

    def __init__(self, air, cogPlanner):
        DistributedAvatarAI.DistributedAvatarAI.__init__(self, air)
        CogBase.CogBase.__init__(self)
        self.sp = cogPlanner
        self.maxHP = 10
        self.currHP = 10
        self.zoneId = 0
        self.dna = None
        self.virtual = 0
        self.skeleRevives = 0
        self.maxSkeleRevives = 0
        self.reviveTrack: int | None = None
        self.buildingHeight = None

    def generate(self):
        DistributedAvatarAI.DistributedAvatarAI.generate(self)

    def delete(self):
        self.sp = None
        del self.dna
        DistributedAvatarAI.DistributedAvatarAI.delete(self)

    def requestRemoval(self):
        if self.sp != None:
            self.sp.removeCog(self)
        else:
            self.requestDelete()
        return

    def setLevel(self, lvl=None):
        attributes = CogBattleGlobals.CogAttributes[self.dna.name]
        if lvl:
            self.level = lvl - attributes['level'] - 1
        else:
            self.level = CogBattleGlobals.pickFromFreqList(attributes['freq'])
        self.notify.debug('Assigning level ' + str(lvl))
        if hasattr(self, 'doId'):
            self.d_setLevelDist(self.level)
        hp = attributes['hp'][self.level]
        self.maxHP = hp
        self.currHP = hp

    def getLevelDist(self):
        return self.getLevel()

    def d_setLevelDist(self, level):
        self.sendUpdate('setLevelDist', [level])

    def setupCogDNA(self, level, type, track):
        dna = CogDNA.CogDNA()
        dna.newCogRandom(type, track)
        self.dna = dna
        self.track = track
        self.setLevel(level)
        return None

    def getDNAString(self):
        if self.dna:
            return self.dna.makeNetString()
        else:
            self.notify.debug('No dna has been created for cog %d!' % self.getDoId())
            return ''

    def b_setBrushOff(self, index):
        self.setBrushOff(index)
        self.d_setBrushOff(index)
        return None

    def d_setBrushOff(self, index):
        self.sendUpdate('setBrushOff', [index])

    def setBrushOff(self, index):
        pass

    def d_denyBattle(self, toonId):
        self.sendUpdateToAvatarId(toonId, 'denyBattle', [])

    def b_setSkeleRevives(self, num):
        if num == None:
            num = 0
        self.setSkeleRevives(num)
        self.d_setSkeleRevives(self.getSkeleRevives())
        return

    def d_setSkeleRevives(self, num):
        self.sendUpdate('setSkeleRevives', [num])

    def getSkeleRevives(self):
        return self.skeleRevives

    def setSkeleRevives(self, num):
        if num == None:
            num = 0
        self.skeleRevives = num
        if num > self.maxSkeleRevives:
            self.maxSkeleRevives = num
        return

    def getMaxSkeleRevives(self):
        return self.maxSkeleRevives

    def useSkeleRevive(self, track = None):
        self.skeleRevives -= 1
        self.currHP = self.maxHP
        self.reviveTrack = track

    def reviveCheckAndClear(self) -> bool:
        if self.reviveTrack is not None:
            self.reviveTrack = None
            return True
        return False

    def getHP(self):
        return self.currHP

    def setHP(self, hp):
        if hp > self.maxHP:
            self.currHP = self.maxHP
        else:
            self.currHP = hp
        return None

    def b_setHP(self, hp):
        self.setHP(hp)
        self.d_setHP(hp)

    def d_setHP(self, hp):
        self.sendUpdate('setHP', [hp])

    def releaseControl(self):
        return None

    def getDeathEvent(self):
        return 'cogDead-%s' % self.doId

    def resume(self):
        self.notify.debug('resume, hp=%s' % self.currHP)
        if self.currHP <= 0:
            messenger.send(self.getDeathEvent())
            self.requestRemoval()
        return None

    def prepareToJoinBattle(self):
        pass

    def b_setSkelecog(self, flag):
        self.setSkelecog(flag)
        self.d_setSkelecog(flag)

    def setSkelecog(self, flag):
        CogBase.CogBase.setSkelecog(self, flag)

    def d_setSkelecog(self, flag):
        self.sendUpdate('setSkelecog', [flag])

    def isForeman(self):
        return 0

    def isSupervisor(self):
        return 0

    def setVirtual(self, virtual):
        pass

    def getVirtual(self):
        return 0

    def isVirtual(self):
        return self.getVirtual()
