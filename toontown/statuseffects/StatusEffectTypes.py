from .StatusEffectInvalid import StatusEffectInvalid
from .StatusEffectDamageBoost import StatusEffectDamageBoost

INVALID_EFFECT = 0
DAMAGE_BOOST_EFFECT = 1
StatusEffectTypes = {
    StatusEffectInvalid: INVALID_EFFECT,
    StatusEffectDamageBoost: DAMAGE_BOOST_EFFECT
}