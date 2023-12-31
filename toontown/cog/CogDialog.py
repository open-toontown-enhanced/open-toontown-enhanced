import random
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPLocalizer
from toontown.toonbase import TTLocalizer
notify = DirectNotifyGlobal.directNotify.newCategory('CogDialog')

def getBrushOffIndex(cogName):
    if cogName in CogBrushOffs:
        brushoffs = CogBrushOffs[cogName]
    else:
        brushoffs = CogBrushOffs[None]
    num = len(brushoffs)
    chunk = 100 / num
    randNum = random.randint(0, 99)
    count = chunk
    for i in range(num):
        if randNum < count:
            return i
        count += chunk

    notify.error('getBrushOffs() - no brush off found!')
    return


def getBrushOffText(cogName, index):
    if cogName in CogBrushOffs:
        brushoffs = CogBrushOffs[cogName]
    else:
        brushoffs = CogBrushOffs[None]
    return brushoffs[index]


CogBrushOffs = OTPLocalizer.CogBrushOffs
