from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from .BattleSounds import *
from . import MovieCamera
from direct.directnotify import DirectNotifyGlobal
from . import MovieUtil
from . import MovieNPCSOS
from .MovieUtil import calcAvgCogPos
from direct.showutil import Effects
import functools
notify = DirectNotifyGlobal.directNotify.newCategory('MovieDrop')
hitSoundFiles = ('AA_drop_flowerpot.ogg', 'AA_drop_sandbag.ogg', 'AA_drop_anvil.ogg', 'AA_drop_bigweight.ogg', 'AA_drop_safe.ogg', 'AA_drop_piano.ogg', 'AA_drop_boat.ogg')
missSoundFiles = ('AA_drop_flowerpot_miss.ogg', 'AA_drop_sandbag_miss.ogg', 'AA_drop_anvil_miss.ogg', 'AA_drop_bigweight_miss.ogg', 'AA_drop_safe_miss.ogg', 'AA_drop_piano_miss.ogg', 'AA_drop_boat_miss.ogg')
tDropShadow = 1.3
tCogDodges = 2.45 + tDropShadow
tObjectAppears = 3.0 + tDropShadow
tButtonPressed = 2.44
dShrink = 0.3
dShrinkOnMiss = 0.1
dPropFall = 0.6
objects = ('flowerpot', 'sandbag', 'anvil', 'weight', 'safe', 'piano', 'ship')
objZOffsets = (0.75, 0.75, 0.0, 0.0, 0.0, 0.0, 0.0)
objStartingScales = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
landFrames = (12, 4, 1, 11, 11, 11, 2)
shoulderHeights = {'a': 13.28 / 4.0,
 'b': 13.74 / 4.0,
 'c': 10.02 / 4.0}

def doDrops(drops):
    if len(drops) == 0:
        return (None, None)
    npcArrivals, npcDepartures, npcs = MovieNPCSOS.doNPCTeleports(drops)
    cogDropsDict = {}
    groupDrops = []
    for drop in drops:
        track = drop['track']
        level = drop['level']
        targets = drop['target']
        if len(targets) == 1:
            cogId = targets[0]['cog'].doId
            if cogId in cogDropsDict:
                cogDropsDict[cogId].append((drop, targets[0]))
            else:
                cogDropsDict[cogId] = [(drop, targets[0])]
        elif level <= MAX_LEVEL_INDEX and attackAffectsGroup(track, level):
            groupDrops.append(drop)
        else:
            for target in targets:
                cogId = target['cog'].doId
                if cogId in cogDropsDict:
                    otherDrops = cogDropsDict[cogId]
                    alreadyInList = 0
                    for oDrop in otherDrops:
                        if oDrop[0]['toon'] == drop['toon']:
                            alreadyInList = 1

                    if alreadyInList == 0:
                        cogDropsDict[cogId].append((drop, target))
                else:
                    cogDropsDict[cogId] = [(drop, target)]

    cogDrops = list(cogDropsDict.values())

    def compFunc(a, b):
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        return 0

    cogDrops.sort(key=functools.cmp_to_key(compFunc))
    delay = 0.0
    mtrack = Parallel(name='toplevel-drop')
    npcDrops = {}
    for st in cogDrops:
        if len(st) > 0:
            ival = __doCogDrops(st, npcs, npcDrops)
            if ival:
                mtrack.append(Sequence(Wait(delay), ival))
            delay = delay + TOON_DROP_COG_DELAY

    dropTrack = Sequence(npcArrivals, mtrack, npcDepartures)
    camDuration = mtrack.getDuration()
    if groupDrops:
        ival = __doGroupDrops(groupDrops)
        dropTrack.append(ival)
        camDuration += ival.getDuration()
    enterDuration = npcArrivals.getDuration()
    exitDuration = npcDepartures.getDuration()
    camTrack = MovieCamera.chooseDropShot(drops, cogDropsDict, camDuration, enterDuration, exitDuration)
    return (dropTrack, camTrack)


def __getSoundTrack(level, hitCog, node = None):
    if hitCog:
        soundEffect = globalBattleSoundCache.getSound(hitSoundFiles[level])
    else:
        soundEffect = globalBattleSoundCache.getSound(missSoundFiles[level])
    soundTrack = Sequence()
    if soundEffect:
        buttonSound = globalBattleSoundCache.getSound('AA_drop_trigger_box.ogg')
        fallingSound = None
        buttonDelay = tButtonPressed - 0.3
        fallingDuration = 1.5
        if not level == UBER_GAG_LEVEL_INDEX:
            fallingSound = globalBattleSoundCache.getSound('incoming_whistleALT.ogg')
        soundTrack.append(Wait(buttonDelay))
        soundTrack.append(SoundInterval(buttonSound, duration=0.67, node=node))
        if fallingSound:
            soundTrack.append(SoundInterval(fallingSound, duration=fallingDuration, node=node))
        if not level == UBER_GAG_LEVEL_INDEX:
            soundTrack.append(SoundInterval(soundEffect, node=node))
        if level == UBER_GAG_LEVEL_INDEX:
            if hitCog:
                uberDelay = tButtonPressed
            else:
                uberDelay = tButtonPressed - 0.1
            oldSoundTrack = soundTrack
            soundTrack = Parallel()
            soundTrack.append(oldSoundTrack)
            uberTrack = Sequence()
            uberTrack.append(Wait(uberDelay))
            uberTrack.append(SoundInterval(soundEffect, node=node))
            soundTrack.append(uberTrack)
    else:
        soundTrack.append(Wait(0.1))
    return soundTrack


def __doCogDrops(dropTargetPairs, npcs, npcDrops):
    toonTracks = Parallel()
    delay = 0.0
    alreadyDodged = 0
    alreadyTeased = 0
    for dropTargetPair in dropTargetPairs:
        drop = dropTargetPair[0]
        level = drop['level']
        objName = objects[level]
        target = dropTargetPair[1]
        track = __dropObjectForSingle(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops)
        if track:
            toonTracks.append(track)
            delay += TOON_DROP_DELAY
        hp = target['hp']
        if hp <= 0:
            if level >= 3:
                alreadyTeased = 1
            else:
                alreadyDodged = 1

    return toonTracks


def __doGroupDrops(groupDrops):
    toonTracks = Parallel()
    delay = 0.0
    alreadyDodged = 0
    alreadyTeased = 0
    for drop in groupDrops:
        battle = drop['battle']
        level = drop['level']
        centerPos = calcAvgCogPos(drop)
        targets = drop['target']
        numTargets = len(targets)
        closestTarget = -1
        nearestDistance = 100000.0
        for i in range(numTargets):
            cog = drop['target'][i]['cog']
            cogPos = cog.getPos(battle)
            displacement = Vec3(centerPos)
            displacement -= cogPos
            distance = displacement.lengthSquared()
            if distance < nearestDistance:
                closestTarget = i
                nearestDistance = distance

        track = __dropGroupObject(drop, delay, closestTarget, alreadyDodged, alreadyTeased)
        if track:
            toonTracks.append(track)
            delay = delay + TOON_DROP_COG_DELAY
        hp = drop['target'][closestTarget]['hp']
        if hp <= 0:
            if level >= 3:
                alreadyTeased = 1
            else:
                alreadyDodged = 1

    return toonTracks


def __dropGroupObject(drop, delay, closestTarget, alreadyDodged, alreadyTeased):
    level = drop['level']
    objName = objects[level]
    target = drop['target'][closestTarget]
    cog = drop['target'][closestTarget]['cog']
    npcDrops = {}
    npcs = []
    returnedParallel = __dropObject(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops)
    for i in range(len(drop['target'])):
        target = drop['target'][i]
        cogTrack = __createCogTrack(drop, delay, level, alreadyDodged, alreadyTeased, target, npcs)
        if cogTrack:
            returnedParallel.append(cogTrack)

    return returnedParallel


def __dropObjectForSingle(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops):
    singleDropParallel = __dropObject(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops)
    cogTrack = __createCogTrack(drop, delay, level, alreadyDodged, alreadyTeased, target, npcs)
    if cogTrack:
        singleDropParallel.append(cogTrack)
    return singleDropParallel


def __dropObject(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops):
    toon = drop['toon']
    repeatNPC = 0
    battle = drop['battle']
    if 'npc' in drop:
        toon = drop['npc']
        if toon in npcDrops:
            repeatNPC = 1
        else:
            npcDrops[toon] = 1
        origHpr = Vec3(0, 0, 0)
    else:
        origHpr = toon.getHpr(battle)
    hpbonus = drop['hpbonus']
    cog = target['cog']
    hp = target['hp']
    hitCog = hp > 0
    died = target['died']
    leftCogs = target['leftCogs']
    rightCogs = target['rightCogs']
    kbbonus = target['kbbonus']
    cogPos = cog.getPos(battle)
    majorObject = level >= 3
    if repeatNPC == 0:
        button = globalPropPool.getProp('button')
        buttonType = globalPropPool.getPropType('button')
        button2 = MovieUtil.copyProp(button)
        buttons = [button, button2]
        hands = toon.getLeftHands()
    object = globalPropPool.getProp(objName)
    objectType = globalPropPool.getPropType(objName)
    if objName == 'weight':
        object.setScale(object.getScale() * 0.75)
    elif objName == 'safe':
        object.setScale(object.getScale() * 0.85)
    node = object.node()
    node.setBounds(OmniBoundingVolume())
    node.setFinal(1)
    soundTrack = __getSoundTrack(level, hitCog, toon)
    toonTrack = Sequence()
    if repeatNPC == 0:
        toonFace = Func(toon.headsUp, battle, cogPos)
        toonTrack.append(Wait(delay))
        toonTrack.append(toonFace)
        toonTrack.append(ActorInterval(toon, 'pushbutton'))
        toonTrack.append(Func(toon.loop, 'neutral'))
        toonTrack.append(Func(toon.setHpr, battle, origHpr))
    buttonTrack = Sequence()
    if repeatNPC == 0:
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
    objectTrack = Sequence()

    def posObject(object, cog, level, majorObject, miss, battle = battle):
        object.reparentTo(battle)
        if battle.isCogLured(cog):
            cogPos, cogHpr = battle.getActorPosHpr(cog)
            object.setPos(cogPos)
            object.setHpr(cogHpr)
            if level >= 3:
                object.setY(object.getY() + 2)
        else:
            object.setPos(cog.getPos(battle))
            object.setHpr(cog.getHpr(battle))
            if miss and level >= 3:
                object.setY(object.getY(battle) + 5)
        if not majorObject:
            if not miss:
                shoulderHeight = shoulderHeights[cog.style.body] * cog.scale
                object.setZ(object.getPos(battle)[2] + shoulderHeight)
        object.setZ(object.getPos(battle)[2] + objZOffsets[level])

    objectTrack.append(Func(battle.movie.needRestoreRenderProp, object))
    objInit = Func(posObject, object, cog, level, majorObject, hp <= 0)
    objectTrack.append(Wait(delay + tObjectAppears))
    objectTrack.append(objInit)
    if hp > 0 or level == 1 or level == 2:
        if hasattr(object, 'getAnimControls'):
            animProp = ActorInterval(object, objName)
            shrinkProp = LerpScaleInterval(object, dShrink, Point3(0.01, 0.01, 0.01), startScale=object.getScale())
            objAnimShrink = ParallelEndTogether(animProp, shrinkProp)
            objectTrack.append(objAnimShrink)
        else:
            startingScale = objStartingScales[level]
            object2 = MovieUtil.copyProp(object)
            posObject(object2, cog, level, majorObject, hp <= 0)
            endingPos = object2.getPos()
            startPos = Point3(endingPos[0], endingPos[1], endingPos[2] + 5)
            startHpr = object2.getHpr()
            endHpr = Point3(startHpr[0] + 90, startHpr[1], startHpr[2])
            animProp = LerpPosInterval(object, landFrames[level] / 24.0, endingPos, startPos=startPos)
            shrinkProp = LerpScaleInterval(object, dShrink, Point3(0.01, 0.01, 0.01), startScale=startingScale)
            bounceProp = Effects.createZBounce(object, 2, endingPos, 0.5, 1.5)
            objAnimShrink = Sequence(Func(object.setScale, startingScale), Func(object.setH, endHpr[0]), animProp, bounceProp, Wait(1.5), shrinkProp)
            objectTrack.append(objAnimShrink)
            MovieUtil.removeProp(object2)
    elif hasattr(object, 'getAnimControls'):
        animProp = ActorInterval(object, objName, duration=landFrames[level] / 24.0)

        def poseProp(prop, animName, level):
            prop.pose(animName, landFrames[level])

        poseProp = Func(poseProp, object, objName, level)
        wait = Wait(1.0)
        shrinkProp = LerpScaleInterval(object, dShrinkOnMiss, Point3(0.01, 0.01, 0.01), startScale=object.getScale())
        objectTrack.append(animProp)
        objectTrack.append(poseProp)
        objectTrack.append(wait)
        objectTrack.append(shrinkProp)
    else:
        startingScale = objStartingScales[level]
        object2 = MovieUtil.copyProp(object)
        posObject(object2, cog, level, majorObject, hp <= 0)
        endingPos = object2.getPos()
        startPos = Point3(endingPos[0], endingPos[1], endingPos[2] + 5)
        startHpr = object2.getHpr()
        endHpr = Point3(startHpr[0] + 90, startHpr[1], startHpr[2])
        animProp = LerpPosInterval(object, landFrames[level] / 24.0, endingPos, startPos=startPos)
        shrinkProp = LerpScaleInterval(object, dShrinkOnMiss, Point3(0.01, 0.01, 0.01), startScale=startingScale)
        bounceProp = Effects.createZBounce(object, 2, endingPos, 0.5, 1.5)
        objAnimShrink = Sequence(Func(object.setScale, startingScale), Func(object.setH, endHpr[0]), animProp, bounceProp, Wait(1.5), shrinkProp)
        objectTrack.append(objAnimShrink)
        MovieUtil.removeProp(object2)
    objectTrack.append(Func(MovieUtil.removeProp, object))
    objectTrack.append(Func(battle.movie.clearRenderProp, object))
    dropShadow = MovieUtil.copyProp(cog.getShadowJoint())
    if level == 0:
        dropShadow.setScale(0.5)
    elif level <= 2:
        dropShadow.setScale(0.8)
    elif level == 3:
        dropShadow.setScale(2.0)
    elif level == 4:
        dropShadow.setScale(2.3)
    else:
        dropShadow.setScale(3.6)

    def posShadow(dropShadow = dropShadow, cog = cog, battle = battle, hp = hp, level = level):
        dropShadow.reparentTo(battle)
        if battle.isCogLured(cog):
            cogPos, cogHpr = battle.getActorPosHpr(cog)
            dropShadow.setPos(cogPos)
            dropShadow.setHpr(cogHpr)
            if level >= 3:
                dropShadow.setY(dropShadow.getY() + 2)
        else:
            dropShadow.setPos(cog.getPos(battle))
            dropShadow.setHpr(cog.getHpr(battle))
            if hp <= 0 and level >= 3:
                dropShadow.setY(dropShadow.getY(battle) + 5)
        dropShadow.setZ(dropShadow.getZ() + 0.5)

    shadowTrack = Sequence(Wait(delay + tButtonPressed), Func(battle.movie.needRestoreRenderProp, dropShadow), Func(posShadow), LerpScaleInterval(dropShadow, tObjectAppears - tButtonPressed, dropShadow.getScale(), startScale=Point3(0.01, 0.01, 0.01)), Wait(0.3), Func(MovieUtil.removeProp, dropShadow), Func(battle.movie.clearRenderProp, dropShadow))
    return Parallel(toonTrack, soundTrack, buttonTrack, objectTrack, shadowTrack)


def __createCogTrack(drop, delay, level, alreadyDodged, alreadyTeased, target, npcs):
    toon = drop['toon']
    if 'npc' in drop:
        toon = drop['npc']
    battle = drop['battle']
    majorObject = level >= 3
    cog = target['cog']
    hp = target['hp']
    hitCog = hp > 0
    died = target['died']
    revived = target['revived']
    leftCogs = target['leftCogs']
    rightCogs = target['rightCogs']
    kbbonus = target['kbbonus']
    hpbonus = drop['hpbonus']
    if hp > 0:
        cogTrack = Sequence()
        showDamage = Func(cog.showHpText, -hp, openEnded=0)
        updateHealthBar = Func(cog.updateHealthBar, hp)
        if majorObject:
            anim = 'flatten'
        else:
            anim = 'drop-react'
        cogReact = ActorInterval(cog, anim)
        cogTrack.append(Wait(delay + tObjectAppears))
        cogTrack.append(showDamage)
        cogTrack.append(updateHealthBar)
        cogGettingHit = Parallel(cogReact)
        if level == UBER_GAG_LEVEL_INDEX:
            gotHitSound = globalBattleSoundCache.getSound('AA_drop_boat_cog.ogg')
            cogGettingHit.append(SoundInterval(gotHitSound, node=toon))
        cogTrack.append(cogGettingHit)
        bonusTrack = None
        if hpbonus > 0:
            bonusTrack = Sequence(Wait(delay + tObjectAppears + 0.75), Func(cog.showHpText, -hpbonus, 1, openEnded=0))
        if revived != 0:
            cogTrack.append(MovieUtil.createCogReviveTrack(cog, toon, battle, npcs))
        elif died != 0:
            cogTrack.append(MovieUtil.createCogDeathTrack(cog, toon, battle, npcs))
        else:
            cogTrack.append(Func(cog.loop, 'neutral'))
        if bonusTrack != None:
            cogTrack = Parallel(cogTrack, bonusTrack)
    elif kbbonus == 0:
        cogTrack = Sequence(Wait(delay + tObjectAppears), Func(MovieUtil.indicateMissed, cog, 0.6), Func(cog.loop, 'neutral'))
    else:
        if alreadyDodged > 0:
            return
        if level >= 3:
            if alreadyTeased > 0:
                return
            else:
                cogTrack = MovieUtil.createCogTeaseMultiTrack(cog, delay=delay + tObjectAppears)
        else:
            cogTrack = MovieUtil.createCogDodgeMultitrack(delay + tCogDodges, cog, leftCogs, rightCogs)
    return cogTrack
