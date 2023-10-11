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


def doThrows(throws):
    if len(throws) == 0:
        return (None, None)
    cogThrowsDict = {}
    for throw in throws:
        if attackAffectsGroup(throw['track'], throw['level']):
            pass
        else:
            cogId = throw['target']['cog'].doId
            if cogId in cogThrowsDict:
                cogThrowsDict[cogId].append(throw)
            else:
                cogThrowsDict[cogId] = [throw]

    cogThrows = list(cogThrowsDict.values())

    def compFunc(a, b):
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        return 0

    cogThrows.sort(key=functools.cmp_to_key(compFunc))
    totalHitDict = {}
    singleHitDict = {}
    groupHitDict = {}
    for throw in throws:
        if attackAffectsGroup(throw['track'], throw['level']):
            for i in range(len(throw['target'])):
                target = throw['target'][i]
                cogId = target['cog'].doId
                if target['hp'] > 0:
                    addHit(groupHitDict, cogId, 1)
                    addHit(totalHitDict, cogId, 1)
                else:
                    addHit(groupHitDict, cogId, 0)
                    addHit(totalHitDict, cogId, 0)

        else:
            cogId = throw['target']['cog'].doId
            if throw['target']['hp'] > 0:
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
    for st in cogThrows:
        if len(st) > 0:
            ival = __doSuitThrows(st)
            if ival:
                mtrack.append(Sequence(Wait(delay), ival))
            delay = delay + TOON_THROW_COG_DELAY

    retTrack = Sequence()
    retTrack.append(mtrack)
    groupThrowIvals = Parallel()
    groupThrows = []
    for throw in throws:
        if attackAffectsGroup(throw['track'], throw['level']):
            groupThrows.append(throw)

    for throw in groupThrows:
        tracks = None
        tracks = __throwGroupPie(throw, 0, groupHitDict)
        if tracks:
            for track in tracks:
                groupThrowIvals.append(track)

    retTrack.append(groupThrowIvals)
    camDuration = retTrack.getDuration()
    camTrack = MovieCamera.chooseThrowShot(throws, cogThrowsDict, camDuration)
    return (retTrack, camTrack)


def __doSuitThrows(throws):
    toonTracks = Parallel()
    delay = 0.0
    hitCount = 0
    for throw in throws:
        if throw['target']['hp'] > 0:
            hitCount += 1
        else:
            break

    for throw in throws:
        tracks = __throwPie(throw, delay, hitCount)
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


def __getWeddingCakeSoundTrack(level, hitSuit, node = None):
    throwTrack = Sequence()
    if hitSuit:
        throwSound = globalBattleSoundCache.getSound('AA_throw_wedding_cake.ogg')
        songTrack = Sequence()
        songTrack.append(Wait(1.0))
        songTrack.append(SoundInterval(throwSound, node=node))
        splatSound = globalBattleSoundCache.getSound('AA_throw_wedding_cake_cog.ogg')
        splatTrack = Sequence()
        splatTrack.append(Wait(tPieHitsSuit))
        splatTrack.append(SoundInterval(splatSound, node=node))
        throwTrack.append(Parallel(songTrack, splatTrack))
    else:
        throwSound = globalBattleSoundCache.getSound('AA_throw_wedding_cake_miss.ogg')
        throwTrack.append(Wait(tSuitDodges))
        throwTrack.append(SoundInterval(throwSound, node=node))
    return throwTrack


def __getSoundTrack(level, hitSuit, node = None):
    if level == UBER_GAG_LEVEL_INDEX:
        return __getWeddingCakeSoundTrack(level, hitSuit, node)
    throwSound = globalBattleSoundCache.getSound('AA_pie_throw_only.ogg')
    throwTrack = Sequence(Wait(2.6), SoundInterval(throwSound, node=node))
    if hitSuit:
        hitSound = globalBattleSoundCache.getSound(hitSoundFiles[level])
        hitTrack = Sequence(Wait(tPieLeavesHand), SoundInterval(hitSound, node=node))
        return Parallel(throwTrack, hitTrack)
    else:
        return throwTrack


def __throwPie(throw, delay, hitCount):
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
    pieName = pieNames[level]
    hitSuit = hp > 0
    pie = globalPropPool.getProp(pieName)
    pieType = globalPropPool.getPropType(pieName)
    pie2 = MovieUtil.copyProp(pie)
    pies = [pie, pie2]
    hands = toon.getRightHands()
    splatName = 'splat-' + pieName
    if pieName == 'wedding-cake':
        splatName = 'splat-birthday-cake'
    splat = globalPropPool.getProp(splatName)
    splatType = globalPropPool.getPropType(splatName)
    toonTrack = Sequence()
    toonFace = Func(toon.headsUp, battle, cogPos)
    toonTrack.append(Wait(delay))
    toonTrack.append(toonFace)
    toonTrack.append(ActorInterval(toon, 'throw'))
    toonTrack.append(Func(toon.loop, 'neutral'))
    toonTrack.append(Func(toon.setHpr, battle, origHpr))
    pieShow = Func(MovieUtil.showProps, pies, hands)
    pieAnim = Func(__animProp, pies, pieName, pieType)
    pieScale1 = LerpScaleInterval(pie, 1.0, pie.getScale(), startScale=MovieUtil.PNT3_NEARZERO)
    pieScale2 = LerpScaleInterval(pie2, 1.0, pie2.getScale(), startScale=MovieUtil.PNT3_NEARZERO)
    pieScale = Parallel(pieScale1, pieScale2)
    piePreflight = Func(__propPreflight, pies, cog, toon, battle)
    pieTrack = Sequence(Wait(delay), pieShow, pieAnim, pieScale, Func(battle.movie.needRestoreRenderProp, pies[0]), Wait(tPieLeavesHand - 1.0), piePreflight)
    soundTrack = __getSoundTrack(level, hitSuit, toon)
    if hitSuit:
        pieFly = LerpPosInterval(pie, tPieHitsSuit - tPieLeavesHand, pos=MovieUtil.avatarFacePoint(cog, other=battle), name=pieFlyTaskName, other=battle)
        pieHide = Func(MovieUtil.removeProps, pies)
        splatShow = Func(__showProp, splat, cog, Point3(0, 0, cog.getHeight()))
        splatBillboard = Func(__billboardProp, splat)
        splatAnim = ActorInterval(splat, splatName)
        splatHide = Func(MovieUtil.removeProp, splat)
        pieTrack.append(pieFly)
        pieTrack.append(pieHide)
        pieTrack.append(Func(battle.movie.clearRenderProp, pies[0]))
        pieTrack.append(splatShow)
        pieTrack.append(splatBillboard)
        pieTrack.append(splatAnim)
        pieTrack.append(splatHide)
    else:
        missDict = {}
        if sidestep:
            cogPoint = MovieUtil.avatarFacePoint(cog, other=battle)
        else:
            cogPoint = __cogMissPoint(cog, other=battle)
        piePreMiss = Func(__piePreMiss, missDict, pie, cogPoint, battle)
        pieMiss = LerpFunctionInterval(__pieMissLerpCallback, extraArgs=[missDict], duration=(tPieHitsSuit - tPieLeavesHand) * ratioMissToHit)
        pieHide = Func(MovieUtil.removeProps, pies)
        pieTrack.append(piePreMiss)
        pieTrack.append(pieMiss)
        pieTrack.append(pieHide)
        pieTrack.append(Func(battle.movie.clearRenderProp, pies[0]))
    if hitSuit:
        cogResponseTrack = Sequence()
        showDamage = Func(cog.showHpText, -hp, openEnded=0, attackTrack=THROW_TRACK)
        updateHealthBar = Func(cog.updateHealthBar, hp)
        sival = []
        if kbbonus > 0:
            cogPos, cogHpr = battle.getActorPosHpr(cog)
            cogType = getCogBodyType(cog.getStyleName())
            animTrack = Sequence()
            animTrack.append(ActorInterval(cog, 'pie-small-react', duration=0.2))
            if cogType == 'a':
                animTrack.append(ActorInterval(cog, 'slip-forward', startTime=2.43))
            elif cogType == 'b':
                animTrack.append(ActorInterval(cog, 'slip-forward', startTime=1.94))
            elif cogType == 'c':
                animTrack.append(ActorInterval(cog, 'slip-forward', startTime=2.58))
            animTrack.append(Func(battle.unlureSuit, cog))
            moveTrack = Sequence(Wait(0.2), LerpPosInterval(cog, 0.6, pos=cogPos, other=battle))
            sival = Parallel(animTrack, moveTrack)
        elif hitCount == 1:
            sival = Parallel(ActorInterval(cog, 'pie-small-react'), MovieUtil.createSuitStunInterval(cog, 0.3, 1.3))
        else:
            sival = ActorInterval(cog, 'pie-small-react')
        cogResponseTrack.append(Wait(delay + tPieHitsSuit))
        cogResponseTrack.append(showDamage)
        cogResponseTrack.append(updateHealthBar)
        cogResponseTrack.append(sival)
        bonusTrack = Sequence(Wait(delay + tPieHitsSuit))
        if kbbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(cog.showHpText, -kbbonus, 2, openEnded=0, attackTrack=THROW_TRACK))
        if hpbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(cog.showHpText, -hpbonus, 1, openEnded=0, attackTrack=THROW_TRACK))
        if revived != 0:
            cogResponseTrack.append(MovieUtil.createSuitReviveTrack(cog, toon, battle))
        elif died != 0:
            cogResponseTrack.append(MovieUtil.createSuitDeathTrack(cog, toon, battle))
        else:
            cogResponseTrack.append(Func(cog.loop, 'neutral'))
        cogResponseTrack = Parallel(cogResponseTrack, bonusTrack)
    else:
        cogResponseTrack = MovieUtil.createSuitDodgeMultitrack(delay + tSuitDodges, cog, leftCogs, rightCogs)
    if not hitSuit and delay > 0:
        return [toonTrack, soundTrack, pieTrack]
    else:
        return [toonTrack,
         soundTrack,
         pieTrack,
         cogResponseTrack]


def __createWeddingCakeFlight(throw, groupHitDict, pie, pies):
    toon = throw['toon']
    battle = throw['battle']
    level = throw['level']
    sidestep = throw['sidestep']
    hpbonus = throw['hpbonus']
    numTargets = len(throw['target'])
    pieName = pieNames[level]
    splatName = 'splat-' + pieName
    if pieName == 'wedding-cake':
        splatName = 'splat-birthday-cake'
    splat = globalPropPool.getProp(splatName)
    splats = [splat]
    for i in range(numTargets - 1):
        splats.append(MovieUtil.copyProp(splat))

    splatType = globalPropPool.getPropType(splatName)
    cakePartStrs = ['cake1',
     'cake2',
     'cake3',
     'caketop']
    cakeParts = []
    for part in cakePartStrs:
        cakeParts.append(pie.find('**/%s' % part))

    cakePartDivisions = {}
    cakePartDivisions[1] = [[cakeParts[0],
      cakeParts[1],
      cakeParts[2],
      cakeParts[3]]]
    cakePartDivisions[2] = [[cakeParts[0], cakeParts[1]], [cakeParts[2], cakeParts[3]]]
    cakePartDivisions[3] = [[cakeParts[0], cakeParts[1]], [cakeParts[2]], [cakeParts[3]]]
    cakePartDivisions[4] = [[cakeParts[0]],
     [cakeParts[1]],
     [cakeParts[2]],
     [cakeParts[3]]]
    cakePartDivToUse = cakePartDivisions[len(throw['target'])]
    groupPieTracks = Parallel()
    for i in range(numTargets):
        target = throw['target'][i]
        cog = target['cog']
        hitSuit = target['hp'] > 0
        singlePieTrack = Sequence()
        if hitSuit:
            piePartReparent = Func(reparentCakePart, pie, cakePartDivToUse[i])
            singlePieTrack.append(piePartReparent)
            cakePartTrack = Parallel()
            for cakePart in cakePartDivToUse[i]:
                pieFly = LerpPosInterval(cakePart, tPieHitsSuit - tPieLeavesHand, pos=MovieUtil.avatarFacePoint(cog, other=battle), name=pieFlyTaskName, other=battle)
                cakePartTrack.append(pieFly)

            singlePieTrack.append(cakePartTrack)
            pieRemoveCakeParts = Func(MovieUtil.removeProps, cakePartDivToUse[i])
            pieHide = Func(MovieUtil.removeProps, pies)
            splatShow = Func(__showProp, splats[i], cog, Point3(0, 0, cog.getHeight()))
            splatBillboard = Func(__billboardProp, splats[i])
            splatAnim = ActorInterval(splats[i], splatName)
            splatHide = Func(MovieUtil.removeProp, splats[i])
            singlePieTrack.append(pieRemoveCakeParts)
            singlePieTrack.append(pieHide)
            singlePieTrack.append(Func(battle.movie.clearRenderProp, pies[0]))
            singlePieTrack.append(splatShow)
            singlePieTrack.append(splatBillboard)
            singlePieTrack.append(splatAnim)
            singlePieTrack.append(splatHide)
        else:
            missDict = {}
            if sidestep:
                cogPoint = MovieUtil.avatarFacePoint(cog, other=battle)
            else:
                cogPoint = __cogMissPoint(cog, other=battle)
            piePartReparent = Func(reparentCakePart, pie, cakePartDivToUse[i])
            piePreMiss = Func(__piePreMissGroup, missDict, cakePartDivToUse[i], cogPoint, battle)
            pieMiss = LerpFunctionInterval(__pieMissGroupLerpCallback, extraArgs=[missDict], duration=(tPieHitsSuit - tPieLeavesHand) * ratioMissToHit)
            pieHide = Func(MovieUtil.removeProps, pies)
            pieRemoveCakeParts = Func(MovieUtil.removeProps, cakePartDivToUse[i])
            singlePieTrack.append(piePartReparent)
            singlePieTrack.append(piePreMiss)
            singlePieTrack.append(pieMiss)
            singlePieTrack.append(pieRemoveCakeParts)
            singlePieTrack.append(pieHide)
            singlePieTrack.append(Func(battle.movie.clearRenderProp, pies[0]))
        groupPieTracks.append(singlePieTrack)

    return groupPieTracks


def __throwGroupPie(throw, delay, groupHitDict):
    toon = throw['toon']
    battle = throw['battle']
    level = throw['level']
    sidestep = throw['sidestep']
    hpbonus = throw['hpbonus']
    numTargets = len(throw['target'])
    avgCogPos = calcAvgCogPos(throw)
    origHpr = toon.getHpr(battle)
    toonTrack = Sequence()
    toonFace = Func(toon.headsUp, battle, avgCogPos)
    toonTrack.append(Wait(delay))
    toonTrack.append(toonFace)
    toonTrack.append(ActorInterval(toon, 'throw'))
    toonTrack.append(Func(toon.loop, 'neutral'))
    toonTrack.append(Func(toon.setHpr, battle, origHpr))
    cogs = []
    for i in range(numTargets):
        cogs.append(throw['target'][i]['cog'])

    pieName = pieNames[level]
    pie = globalPropPool.getProp(pieName)
    pieType = globalPropPool.getPropType(pieName)
    pie2 = MovieUtil.copyProp(pie)
    pies = [pie, pie2]
    hands = toon.getRightHands()
    pieShow = Func(MovieUtil.showProps, pies, hands)
    pieAnim = Func(__animProp, pies, pieName, pieType)
    pieScale1 = LerpScaleInterval(pie, 1.0, pie.getScale() * 1.5, startScale=MovieUtil.PNT3_NEARZERO)
    pieScale2 = LerpScaleInterval(pie2, 1.0, pie2.getScale() * 1.5, startScale=MovieUtil.PNT3_NEARZERO)
    pieScale = Parallel(pieScale1, pieScale2)
    piePreflight = Func(__propPreflightGroup, pies, cogs, toon, battle)
    pieTrack = Sequence(Wait(delay), pieShow, pieAnim, pieScale, Func(battle.movie.needRestoreRenderProp, pies[0]), Wait(tPieLeavesHand - 1.0), piePreflight)
    if level == UBER_GAG_LEVEL_INDEX:
        groupPieTracks = __createWeddingCakeFlight(throw, groupHitDict, pie, pies)
    else:
        notify.error('unhandled throw level %d' % level)
    pieTrack.append(groupPieTracks)
    didThrowHitAnyone = False
    for i in range(numTargets):
        target = throw['target'][i]
        hitSuit = target['hp'] > 0
        if hitSuit:
            didThrowHitAnyone = True

    soundTrack = __getSoundTrack(level, didThrowHitAnyone, toon)
    groupSuitResponseTrack = Parallel()
    for i in range(numTargets):
        target = throw['target'][i]
        cog = target['cog']
        hitSuit = target['hp'] > 0
        leftCogs = target['leftCogs']
        rightCogs = target['rightCogs']
        hp = target['hp']
        kbbonus = target['kbbonus']
        died = target['died']
        revived = target['revived']
        if hitSuit:
            singleSuitResponseTrack = Sequence()
            showDamage = Func(cog.showHpText, -hp, openEnded=0, attackTrack=THROW_TRACK)
            updateHealthBar = Func(cog.updateHealthBar, hp)
            sival = []
            if kbbonus > 0:
                cogPos, cogHpr = battle.getActorPosHpr(cog)
                cogType = getCogBodyType(cog.getStyleName())
                animTrack = Sequence()
                animTrack.append(ActorInterval(cog, 'pie-small-react', duration=0.2))
                if cogType == 'a':
                    animTrack.append(ActorInterval(cog, 'slip-forward', startTime=2.43))
                elif cogType == 'b':
                    animTrack.append(ActorInterval(cog, 'slip-forward', startTime=1.94))
                elif cogType == 'c':
                    animTrack.append(ActorInterval(cog, 'slip-forward', startTime=2.58))
                animTrack.append(Func(battle.unlureSuit, cog))
                moveTrack = Sequence(Wait(0.2), LerpPosInterval(cog, 0.6, pos=cogPos, other=battle))
                sival = Parallel(animTrack, moveTrack)
            elif groupHitDict[cog.doId] == 1:
                sival = Parallel(ActorInterval(cog, 'pie-small-react'), MovieUtil.createSuitStunInterval(cog, 0.3, 1.3))
            else:
                sival = ActorInterval(cog, 'pie-small-react')
            singleSuitResponseTrack.append(Wait(delay + tPieHitsSuit))
            singleSuitResponseTrack.append(showDamage)
            singleSuitResponseTrack.append(updateHealthBar)
            singleSuitResponseTrack.append(sival)
            bonusTrack = Sequence(Wait(delay + tPieHitsSuit))
            if kbbonus > 0:
                bonusTrack.append(Wait(0.75))
                bonusTrack.append(Func(cog.showHpText, -kbbonus, 2, openEnded=0, attackTrack=THROW_TRACK))
            if hpbonus > 0:
                bonusTrack.append(Wait(0.75))
                bonusTrack.append(Func(cog.showHpText, -hpbonus, 1, openEnded=0, attackTrack=THROW_TRACK))
            if revived != 0:
                singleSuitResponseTrack.append(MovieUtil.createSuitReviveTrack(cog, toon, battle))
            elif died != 0:
                singleSuitResponseTrack.append(MovieUtil.createSuitDeathTrack(cog, toon, battle))
            else:
                singleSuitResponseTrack.append(Func(cog.loop, 'neutral'))
            singleSuitResponseTrack = Parallel(singleSuitResponseTrack, bonusTrack)
        else:
            groupHitValues = list(groupHitDict.values())
            if groupHitValues.count(0) == len(groupHitValues):
                singleSuitResponseTrack = MovieUtil.createSuitDodgeMultitrack(delay + tSuitDodges, cog, leftCogs, rightCogs)
            else:
                singleSuitResponseTrack = Sequence(Wait(tPieHitsSuit - 0.1), Func(MovieUtil.indicateMissed, cog, 1.0))
        groupSuitResponseTrack.append(singleSuitResponseTrack)

    return [toonTrack,
     pieTrack,
     soundTrack,
     groupSuitResponseTrack]


def reparentCakePart(pie, cakeParts):
    pieParent = pie.getParent()
    notify.debug('pieParent = %s' % pieParent)
    for cakePart in cakeParts:
        cakePart.wrtReparentTo(pieParent)
