from typing import Optional
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
import sys

class StatusEffect:
    notify = directNotify.newCategory('StatusEffect')

    def __init__(self, *args):
        self.rounds: int = -1
        if len(args) >= 1 and isinstance(args[0], PyDatagramIterator):
            self.decodeDatagram(*args)
        else:
            self.makeNewStatus(*args)

    def getTypeCode(self) -> int:
        return StatusEffectTypes.StatusEffectTypes[self.__class__]

    def getRounds(self) -> int:
        return self.rounds

    def getDamageBoost(self) -> int:
        return 0

    def makeNewStatus(self):
        return NotImplementedError

    def encodeDatagram(self, dg: PyDatagram):
        pass

    def decodeDatagram(self, dgi: PyDatagramIterator):
        self.rounds = dgi.getUint8()

    def output(self, store: int = -1):
        return "StatusEffect()"

StatusEffectTypesReversed: Optional[dict[int, StatusEffect]] = None

def encodeStatusEffect(dg: PyDatagram, item: StatusEffect):
    typeCode: int = item.getTypeCode()
    dg.addUint8(typeCode)
    item.encodeDatagram(dg)

def decodeStatusEffect(dgi: PyDatagramIterator):
    from . import StatusEffectTypes
    if StatusEffectTypesReserved is None:
        StatusEffectTypesReversed = dict(reversed(list(StatusEffectTypes.StatusEffectTypes.items())))

    startIndex: int = dgi.getCurrentIndex()
    try:
        typeCode: int = dgi.getUint8()
        itemClass = StatusEffectTypesReversed[typeCode]
        item = itemClass(dgi)
    except Exception as e:
        StatusEffect.notify.warning(f'Invalid status effect in stream: {sys.exc_info()[0]}, {e}')
        d = PyDatagram(dgi.getDatagram().getMessage()[startIndex:])
        d.dumpHex(Notify.out())
        from .StatusEffectInvalid import StatusEffectInvalid
        return StatusEffectInvalid()

    return item
    