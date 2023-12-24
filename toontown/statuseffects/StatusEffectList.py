from . import StatusEffect
from toontown.toonutils.BlobList import *

class StatusEffectList(BlobList):

    def makeBlob(self, store):
        dg = PyDatagram()
        if self._list:
            for item in self._list:
                StatusEffect.encodeStatusEffect(dg, item)

        return dg.getMessage()

    def makeList(self, store):
        _list = []
        if self._blob:
            dg = PyDatagram(self.__blob)
            di = PyDatagramIterator(dg)
            while di.getRemainingSize() > 0:
                item = StatusEffect.decodeStatusEffect(di)
                _list.append(item)

        return _list

    def decRounds(self):
        needsUpdate: bool = False
        if self._list:
            for item in self._list[:]:
                rounds: int = item.getRounds()
                if rounds != -1:
                    item.setRounds(rounds - 1)
                    if item.getRounds() == 0:
                        self._list.remove(item)
                    needsUpdate = True

        return needsUpdate

    def getDamageBoost(self) -> int:
        if len(self) == 0:
            return 0
        damageBoost: int = 0
        for item in self:
            damageBoost += item.getDamageBoost()

        return damageBoost