from .StatusEffect import *

class StatusEffectInvalid(StatusEffect):

    def output(self, store: int = -1):
        return "StatusEffectInvalid()"