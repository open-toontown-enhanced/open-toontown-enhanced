from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import DistributedCogHQDoor
from toontown.toonbase import TTLocalizer
from . import CogDisguiseGlobals

class DistributedSellbotHQDoor(DistributedCogHQDoor.DistributedCogHQDoor):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSellbotHQDoor')

    def __init__(self, cr):
        DistributedCogHQDoor.DistributedCogHQDoor.__init__(self, cr)

    def informPlayer(self, cogType):
        self.notify.debugStateCall(self)
        if cogType == CogDisguiseGlobals.cogTypes.NoSuit:
            popupMsg = TTLocalizer.SellbotRentalSuitMessage
        elif cogType == CogDisguiseGlobals.cogTypes.NoMerits:
            popupMsg = TTLocalizer.SellbotCogSuitNoMeritsMessage
        elif cogType == CogDisguiseGlobals.cogTypes.FullSuit:
            popupMsg = TTLocalizer.SellbotCogSuitHasMeritsMessage
        else:
            popupMsg = TTLocalizer.FADoorCodes_SB_DISGUISE_INCOMPLETE
        localAvatar.elevatorNotifier.showMeWithoutStopping(popupMsg, pos=(0, 0, 0.26), ttDialog=True)
        localAvatar.elevatorNotifier.setOkButton()
        localAvatar.elevatorNotifier.doneButton.setZ(-0.3)
