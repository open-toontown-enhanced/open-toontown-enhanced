from .StatusEffect import *

class StatusEffectDamageBoost(StatusEffect):

    def makeNewStatus(self, damageBoost: int):
        self.damageBoost = damageBoost

    def getDamageBoost(self) -> int:
        return self.damageBoost

    def encodeDatagram(self, dg: PyDatagram):
        dg.addUint8(self.getDamageBoost())

    def decodeDatagram(self, dgi: PyDatagramIterator):
        StatusEffect.decodeDatagram(dgi)
        self.damageBoost = dgi.getUint8()

    def output(self, store: int = -1):
        return f"StatusEffectDamageBoost({self.getDamageBoost()})"