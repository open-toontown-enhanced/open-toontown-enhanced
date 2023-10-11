from panda3d.core import *
from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from .BattleSounds import *
from toontown.toon.ToonDNA import *
from toontown.cog.CogDNA import *
from direct.directnotify import DirectNotifyGlobal
import random
import functools
from . import MovieCamera
from . import MovieUtil
from .MovieUtil import calcAvgCogPos
notify = DirectNotifyGlobal.directNotify.newCategory('MovieThrow')
hitSoundFiles = ('AA_tart_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg', 'AA_wholepie_only.ogg', 'AA_wholepie_only.ogg')
tPieLeavesHand = 2.7
tPieHitsSuit = 3.0
tSuitDodges = 2.45
ratioMissToHit = 1.5
tPieShrink = 0.7
pieFlyTaskName = 'MovieThrow-pieFly'

def addHit(dict, cogId, hitCount):
    if cogId in dict:
        dict[cogId] += hitCount
    else:
        dict[cogId] = hitCount


def doFires(fires):
    if len(fires) == 0:
        return (None, None)

    cogFiresDict = {}
    for fire in fires:
        cogId = fire['target']['cog'].doId
        if cogId in cogFiresDict:
            cogFiresDict[cogId].append(fire)
        else:
            cogFiresDict[cogId] = [fire]

    cogFires = list(cogFiresDict.values())
    def compFunc(a, b):
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        return 0
    cogFires.sort(key=functools.cmp_to_key(compFunc))

    totalHitDict = {}
    singleHitDict = {}
    groupHitDict = {}

    for fire in fires:
        cogId = fire['target']['cog'].doId
        if 1:
            if fire['target']['hp'] > 0:
                addHit(singleHitDict, cogId, 1)
                addHit(totalHitDict, cogId, 1)
            else:
                addHit(singleHitDict, cogId, 0)
                addHit(totalHitDict, cogId, 0)

    notify.debug('singleHitDict = %s' % singleHitDict)
    notify.debug('groupHitDict = %s' % groupHitDict)
    notify.debug('totalHitDict = %s' % totalHitDict)

    delay = 0.0
    mtrack = Parallel()
    firedTargets = []
    for sf in cogFires:
        if len(sf) > 0:
            ival = __doSuitFires(sf)
            if ival:
                mtrack.append(Sequence(Wait(delay), ival))
            delay = delay + TOON_FIRE_COG_DELAY

    retTrack = Sequence()
    retTrack.append(mtrack)
    camDuration = retTrack.getDuration()
    camTrack = MovieCamera.chooseFireShot(fires, cogFiresDict, camDuration)
    return (retTrack, camTrack)

def __doSuitFires(fires):
    toonTracks = Parallel()
    delay = 0.0
    hitCount = 0
    for fire in fires:
        if fire['target']['hp'] > 0:
            hitCount += 1
        else:
            break

    cogList = []
    for fire in fires:
        if fire['target']['cog'] not in cogList:
            cogList.append(fire['target']['cog'])

    for fire in fires:
        showSuitCannon = 1
        if fire['target']['cog'] not in cogList:
            showSuitCannon = 0
        else:
            cogList.remove(fire['target']['cog'])
        tracks = __throwPie(fire, delay, hitCount, showSuitCannon)
        if tracks:
            for track in tracks:
                toonTracks.append(track)

        delay = delay + TOON_THROW_DELAY

    return toonTracks


def __showProp(prop, parent, pos):
    prop.reparentTo(parent)
    prop.setPos(pos)


def __animProp(props, propName, propType):
    if 'actor' == propType:
        for prop in props:
            prop.play(propName)

    elif 'model' == propType:
        pass
    else:
        notify.error('No such propType as: %s' % propType)


def __billboardProp(prop):
    scale = prop.getScale()
    prop.setBillboardPointWorld()
    prop.setScale(scale)


def __cogMissPoint(cog, other = render):
    pnt = cog.getPos(other)
    pnt.setZ(pnt[2] + cog.getHeight() * 1.3)
    return pnt


def __propPreflight(props, cog, toon, battle):
    prop = props[0]
    toon.update(0)
    prop.wrtReparentTo(battle)
    props[1].reparentTo(hidden)
    for ci in range(prop.getNumChildren()):
        prop.getChild(ci).setHpr(0, -90, 0)

    targetPnt = MovieUtil.avatarFacePoint(cog, other=battle)
    prop.lookAt(targetPnt)


def __propPreflightGroup(props, cogs, toon, battle):
    prop = props[0]
    toon.update(0)
    prop.wrtReparentTo(battle)
    props[1].reparentTo(hidden)
    for ci in range(prop.getNumChildren()):
        prop.getChild(ci).setHpr(0, -90, 0)

    avgTargetPt = Point3(0, 0, 0)
    for cog in cogs:
        avgTargetPt += MovieUtil.avatarFacePoint(cog, other=battle)

    avgTargetPt /= len(cogs)
    prop.lookAt(avgTargetPt)


def __piePreMiss(missDict, pie, cogPoint, other = render):
    missDict['pie'] = pie
    missDict['startScale'] = pie.getScale()
    missDict['startPos'] = pie.getPos(other)
    v = Vec3(cogPoint - missDict['startPos'])
    endPos = missDict['startPos'] + v * ratioMissToHit
    missDict['endPos'] = endPos


def __pieMissLerpCallback(t, missDict):
    pie = missDict['pie']
    newPos = missDict['startPos'] * (1.0 - t) + missDict['endPos'] * t
    if t < tPieShrink:
        tScale = 0.0001
    else:
        tScale = (t - tPieShrink) / (1.0 - tPieShrink)
    newScale = missDict['startScale'] * max(1.0 - tScale, 0.01)
    pie.setPos(newPos)
    pie.setScale(newScale)


def __piePreMissGroup(missDict, pies, cogPoint, other = render):
    missDict['pies'] = pies
    missDict['startScale'] = pies[0].getScale()
    missDict['startPos'] = pies[0].getPos(other)
    v = Vec3(cogPoint - missDict['startPos'])
    endPos = missDict['startPos'] + v * ratioMissToHit
    missDict['endPos'] = endPos
    notify.debug('startPos=%s' % missDict['startPos'])
    notify.debug('v=%s' % v)
    notify.debug('endPos=%s' % missDict['endPos'])


def __pieMissGroupLerpCallback(t, missDict):
    pies = missDict['pies']
    newPos = missDict['startPos'] * (1.0 - t) + missDict['endPos'] * t
    if t < tPieShrink:
        tScale = 0.0001
    else:
        tScale = (t - tPieShrink) / (1.0 - tPieShrink)
    newScale = missDict['startScale'] * max(1.0 - tScale, 0.01)
    for pie in pies:
        pie.setPos(newPos)
        pie.setScale(newScale)


def __getSoundTrack(level, hitSuit, node = None):
    throwSound = globalBattleSoundCache.getSound('AA_drop_trigger_box.ogg')
    throwTrack = Sequence(Wait(2.15), SoundInterval(throwSound, node=node))
    return throwTrack


def __throwPie(throw, delay, hitCount, showCannon = 1):
    toon = throw['toon']
    hpbonus = throw['hpbonus']
    target = throw['target']
    cog = target['cog']
    hp = target['hp']
    kbbonus = target['kbbonus']
    sidestep = throw['sidestep']
    died = target['died']
    revived = target['revived']
    leftCogs = target['leftCogs']
    rightCogs = target['rightCogs']
    level = throw['level']
    battle = throw['battle']
    cogPos = cog.getPos(battle)
    origHpr = toon.getHpr(battle)
    notify.debug('toon: %s throws tart at cog: %d for hp: %d died: %d' % (toon.getName(),
     cog.doId,
     hp,
     died))
    pieName = pieNames[0]
    hitSuit = hp > 0
    button = globalPropPool.getProp('button')
    buttonType = globalPropPool.getPropType('button')
    button2 = MovieUtil.copyProp(button)
    buttons = [button, button2]
    hands = toon.getLeftHands()
    toonTrack = Sequence()
    toonFace = Func(toon.headsUp, battle, cogPos)
    toonTrack.append(Wait(delay))
    toonTrack.append(toonFace)
    toonTrack.append(ActorInterval(toon, 'pushbutton'))
    toonTrack.append(ActorInterval(toon, 'wave', duration=2.0))
    toonTrack.append(ActorInterval(toon, 'duck'))
    toonTrack.append(Func(toon.loop, 'neutral'))
    toonTrack.append(Func(toon.setHpr, battle, origHpr))
    buttonTrack = Sequence()
    buttonShow = Func(MovieUtil.showProps, buttons, hands)
    buttonScaleUp = LerpScaleInterval(button, 1.0, button.getScale(), startScale=Point3(0.01, 0.01, 0.01))
    buttonScaleDown = LerpScaleInterval(button, 1.0, Point3(0.01, 0.01, 0.01), startScale=button.getScale())
    buttonHide = Func(MovieUtil.removeProps, buttons)
    buttonTrack.append(Wait(delay))
    buttonTrack.append(buttonShow)
    buttonTrack.append(buttonScaleUp)
    buttonTrack.append(Wait(2.5))
    buttonTrack.append(buttonScaleDown)
    buttonTrack.append(buttonHide)
    soundTrack = __getSoundTrack(level, hitSuit, toon)
    cogResponseTrack = Sequence()
    reactIval = Sequence()
    if showCannon:
        showDamage = Func(cog.showHpText, -hp, openEnded=0)
        updateHealthBar = Func(cog.updateHealthBar, hp)
        cannon = loader.loadModel('phase_4/models/minigames/toon_cannon')
        barrel = cannon.find('**/cannon')
        barrel.setHpr(0, 90, 0)
        cannonHolder = render.attachNewNode('CannonHolder')
        cannon.reparentTo(cannonHolder)
        cannon.setPos(0, 0, -8.6)
        cannonHolder.setPos(cog.getPos(render))
        cannonHolder.setHpr(cog.getHpr(render))
        cannonAttachPoint = barrel.attachNewNode('CannonAttach')
        kapowAttachPoint = barrel.attachNewNode('kapowAttach')
        scaleFactor = 1.6
        iScale = 1 / scaleFactor
        barrel.setScale(scaleFactor, 1, scaleFactor)
        cannonAttachPoint.setScale(iScale, 1, iScale)
        cannonAttachPoint.setPos(0, 6.7, 0)
        kapowAttachPoint.setPos(0, -0.5, 1.9)
        cog.reparentTo(cannonAttachPoint)
        cog.setPos(0, 0, 0)
        cog.setHpr(0, -90, 0)
        cogLevel = cog.getActualLevel()
        deep = 2.5 + cogLevel * 0.2
        cogScale = 0.9
        import math
        cogScale = 0.9 - math.sqrt(cogLevel) * 0.1
        sival = []
        posInit = cannonHolder.getPos()
        posFinal = Point3(posInit[0] + 0.0, posInit[1] + 0.0, posInit[2] + 7.0)
        kapow = globalPropPool.getProp('kapow')
        kapow.reparentTo(kapowAttachPoint)
        kapow.hide()
        kapow.setScale(0.25)
        kapow.setBillboardPointEye()
        smoke = loader.loadModel('phase_4/models/props/test_clouds')
        smoke.reparentTo(cannonAttachPoint)
        smoke.setScale(0.5)
        smoke.hide()
        smoke.setBillboardPointEye()
        soundBomb = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.ogg')
        playSoundBomb = SoundInterval(soundBomb, node=cannonHolder)
        soundFly = base.loader.loadSfx('phase_4/audio/sfx/firework_whistle_01.ogg')
        playSoundFly = SoundInterval(soundFly, node=cannonHolder)
        soundCannonAdjust = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_adjust.ogg')
        playSoundCannonAdjust = SoundInterval(soundCannonAdjust, duration=0.6, node=cannonHolder)
        soundCogPanic = base.loader.loadSfx('phase_5/audio/sfx/ENC_cogafssm.ogg')
        playSoundCogPanic = SoundInterval(soundCogPanic, node=cannonHolder)
        reactIval = Parallel(ActorInterval(cog, 'pie-small-react'), Sequence(Wait(0.0), LerpPosInterval(cannonHolder, 2.0, posFinal, startPos=posInit, blendType='easeInOut'), Parallel(LerpHprInterval(barrel, 0.6, Point3(0, 45, 0), startHpr=Point3(0, 90, 0), blendType='easeIn'), playSoundCannonAdjust), Wait(2.0), Parallel(LerpHprInterval(barrel, 0.6, Point3(0, 90, 0), startHpr=Point3(0, 45, 0), blendType='easeIn'), playSoundCannonAdjust), LerpPosInterval(cannonHolder, 1.0, posInit, startPos=posFinal, blendType='easeInOut')), Sequence(Wait(0.0), Parallel(ActorInterval(cog, 'flail'), cog.scaleInterval(1.0, cogScale), LerpPosInterval(cog, 0.25, Point3(0, -1.0, 0.0)), Sequence(Wait(0.25), Parallel(playSoundCogPanic, LerpPosInterval(cog, 1.5, Point3(0, -deep, 0.0), blendType='easeIn')))), Wait(2.5), Parallel(playSoundBomb, playSoundFly, Sequence(Func(smoke.show), Parallel(LerpScaleInterval(smoke, 0.5, 3), LerpColorScaleInterval(smoke, 0.5, Vec4(2, 2, 2, 0))), Func(smoke.hide)), Sequence(Func(kapow.show),
ActorInterval(kapow, 'kapow'), Func(kapow.hide)), LerpPosInterval(cog, 3.0, Point3(0, 150.0, 0.0)), cog.scaleInterval(3.0, 0.01)), Func(cog.hide)))
        if hitCount == 1:
            sival = Sequence(Parallel(reactIval, MovieUtil.createSuitStunInterval(cog, 0.3, 1.3)), Wait(0.0), Func(cannonHolder.remove))
        else:
            sival = reactIval
        cogResponseTrack.append(Wait(delay + tPieHitsSuit))
        cogResponseTrack.append(showDamage)
        cogResponseTrack.append(updateHealthBar)
        cogResponseTrack.append(sival)
        bonusTrack = Sequence(Wait(delay + tPieHitsSuit))
        if kbbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(cog.showHpText, -kbbonus, 2, openEnded=0))
        if hpbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(cog.showHpText, -hpbonus, 1, openEnded=0))
        cogResponseTrack = Parallel(cogResponseTrack, bonusTrack)
    return [toonTrack,
     soundTrack,
     buttonTrack,
     cogResponseTrack]