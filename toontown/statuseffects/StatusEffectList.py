from . import StatusEffect
from toontown.toonutils.BlobList import *

class StatusEffectList(BlobList):

    def makeBlob(self, store):
        dg = PyDatagram()
        if self._list:
            for item in self.__list:
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

    def getDamageBoost(self) -> int:
        if len(self) == 0:
            return 0
        damageBoost: int = 0
        for item in self:
            damageBoost += item.getDamageBoost()

        return damageBoost