from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from direct.directnotify import DirectNotifyGlobal
import random
from direct.particles import ParticleEffect
from . import BattleParticles
from . import BattleProps
from toontown.toonbase import TTLocalizer
notify = DirectNotifyGlobal.directNotify.newCategory('MovieUtil')
COG_LOSE_DURATION = 6.0
COG_LURE_DISTANCE = 2.6
COG_LURE_DOLLAR_DISTANCE = 5.1
COG_EXTRA_REACH_DISTANCE = 0.9
COG_EXTRA_RAKE_DISTANCE = 1.1
COG_TRAP_DISTANCE = 2.6
COG_TRAP_RAKE_DISTANCE = 4.5
COG_TRAP_MARBLES_DISTANCE = 3.7
COG_TRAP_TNT_DISTANCE = 5.1
PNT3_NEARZERO = Point3(0.01, 0.01, 0.01)
PNT3_ZERO = Point3(0.0, 0.0, 0.0)
PNT3_ONE = Point3(1.0, 1.0, 1.0)
largeCogs = ['flunky',
 'cold_caller',
 'glad_hander',
 'tightwad',
 'bottom_feeder',
 'short_change',
 'downsizer',
 'head_hunter',
 'corporate_raider',
 'the_big_cheese',
 'back_stabber',
 'spin_doctor',
 'legal_eagle',
 'big_wig',
 'number_cruncher',
 'money_bags',
 'loan_shark',
 'robber_baron',
 'mover_and_shaker',
 'two_face',
 'the_mingler',
 'mr_hollywood']
shotDirection = 'left'

def avatarDodge(leftAvatars, rightAvatars, leftData, rightData):
    if len(leftAvatars) > len(rightAvatars):
        PoLR = rightAvatars
        PoMR = leftAvatars
    else:
        PoLR = leftAvatars
        PoMR = rightAvatars
    upper = 1 + 4 * abs(len(leftAvatars) - len(rightAvatars))
    if random.randint(0, upper) > 0:
        avDodgeList = PoLR
    else:
        avDodgeList = PoMR
    if avDodgeList is leftAvatars:
        data = leftData
    else:
        data = rightData
    return (avDodgeList, data)


def avatarHide(avatar):
    notify.debug('avatarHide(%d)' % avatar.doId)
    if hasattr(avatar, 'battleTrapProp'):
        notify.debug('avatar.battleTrapProp = %s' % avatar.battleTrapProp)
    avatar.detachNode()


def copyProp(prop):
    from direct.actor import Actor
    if isinstance(prop, Actor.Actor):
        return Actor.Actor(other=prop)
    else:
        return prop.copyTo(hidden)


def showProp(prop, hand, pos = None, hpr = None, scale = None):
    prop.reparentTo(hand)
    if pos:
        if callable(pos):
            pos = pos()
        prop.setPos(pos)
    if hpr:
        if callable(hpr):
            hpr = hpr()
        prop.setHpr(hpr)
    if scale:
        if callable(scale):
            scale = scale()
        prop.setScale(scale)


def showProps(props, hands, pos = None, hpr = None, scale = None):
    index = 0
    for prop in props:
        prop.reparentTo(hands[index])
        if pos:
            prop.setPos(pos)
        if hpr:
            prop.setHpr(hpr)
        if scale:
            prop.setScale(scale)
        index += 1


def hideProps(props):
    for prop in props:
        prop.detachNode()


def removeProp(prop):
    from direct.actor import Actor
    if prop.isEmpty() == 1 or prop == None:
        return
    prop.detachNode()
    if isinstance(prop, Actor.Actor):
        prop.cleanup()
    else:
        prop.removeNode()
    return


def removeProps(props):
    for prop in props:
        removeProp(prop)


def getActorIntervals(props, anim):
    tracks = Parallel()
    for prop in props:
        tracks.append(ActorInterval(prop, anim))

    return tracks


def getScaleIntervals(props, duration, startScale, endScale):
    tracks = Parallel()
    for prop in props:
        tracks.append(LerpScaleInterval(prop, duration, endScale, startScale=startScale))

    return tracks


def avatarFacePoint(av, other = render):
    pnt = av.getPos(other)
    pnt.setZ(pnt[2] + av.getHeight())
    return pnt


def insertDeathCog(cog, deathCog, battle = None, pos = None, hpr = None):
    holdParent = cog.getParent()
    if cog.getVirtual():
        virtualize(deathCog)
    avatarHide(cog)
    if deathCog != None and not deathCog.isEmpty():
        if holdParent and 0:
            deathCog.reparentTo(holdParent)
        else:
            deathCog.reparentTo(render)
        if battle != None and pos != None:
            deathCog.setPos(battle, pos)
        if battle != None and hpr != None:
            deathCog.setHpr(battle, hpr)
    return


def removeDeathCog(cog, deathCog):
    notify.debug('removeDeathCog()')
    if not deathCog.isEmpty():
        deathCog.detachNode()
        cog.cleanupLoseActor()


def insertReviveCog(cog, deathCog, battle = None, pos = None, hpr = None):
    holdParent = cog.getParent()
    if cog.getVirtual():
        virtualize(deathCog)
    cog.hide()
    if deathCog != None and not deathCog.isEmpty():
        if holdParent and 0:
            deathCog.reparentTo(holdParent)
        else:
            deathCog.reparentTo(render)
        if battle != None and pos != None:
            deathCog.setPos(battle, pos)
        if battle != None and hpr != None:
            deathCog.setHpr(battle, hpr)
    return


def removeReviveCog(cog, deathCog):
    notify.debug('removeDeathCog()')
    cog.setSkelecog(1)
    cog.show()
    if not deathCog.isEmpty():
        deathCog.detachNode()
        cog.cleanupLoseActor()
    cog.healthBar.show()
    cog.reseatHealthBarForSkele()


def virtualize(deathcog):
    actorNode = deathcog.find('**/__Actor_modelRoot')
    actorCollection = actorNode.findAllMatches('*')
    parts = ()
    for thingIndex in range(0, actorCollection.getNumPaths()):
        thing = actorCollection[thingIndex]
        if thing.getName() not in ('joint_attachMeter', 'joint_nameTag', 'def_nameTag'):
            thing.setColorScale(1.0, 0.0, 0.0, 1.0)
            thing.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
            thing.setDepthWrite(False)
            thing.setBin('fixed', 1)


def createTrainTrackAppearTrack(dyingCog, toon, battle, npcs):
    retval = Sequence()
    return retval
    possibleCogs = []
    for cogAttack in battle.movie.cogAttackDicts:
        cog = cogAttack['cog']
        if not cog == dyingCog:
            if hasattr(cog, 'battleTrapProp') and cog.battleTrapProp and cog.battleTrapProp.getName() == 'traintrack':
                possibleCogs.append(cogAttack['cog'])

    closestXDistance = 10000
    closestCog = None
    for cog in possibleCogs:
        cogPoint, cogHpr = battle.getActorPosHpr(cog)
        xDistance = abs(cogPoint.getX())
        if xDistance < closestXDistance:
            closestCog = cog
            closestXDistance = xDistance

    if closestCog and closestCog.battleTrapProp.isHidden():
        closestCog.battleTrapProp.setColorScale(1, 1, 1, 0)
        closestCog.battleTrapProp.show()
        newRelativePos = dyingCog.battleTrapProp.getPos(closestCog)
        newHpr = dyingCog.battleTrapProp.getHpr(closestCog)
        closestCog.battleTrapProp.setPos(newRelativePos)
        closestCog.battleTrapProp.setHpr(newHpr)
        retval.append(LerpColorScaleInterval(closestCog.battleTrapProp, 3.0, Vec4(1, 1, 1, 1)))
    else:
        notify.debug('could not find closest cog, returning empty sequence')
    return retval


def createCogReviveTrack(cog, toon, battle, npcs = []):
    cogTrack = Sequence()
    cogPos, cogHpr = battle.getActorPosHpr(cog)
    if hasattr(cog, 'battleTrapProp') and cog.battleTrapProp and cog.battleTrapProp.getName() == 'traintrack' and not cog.battleTrapProp.isHidden():
        cogTrack.append(createTrainTrackAppearTrack(cog, toon, battle, npcs))
    deathCog = cog.getLoseActor()
    cogTrack.append(Func(notify.debug, 'before insertDeathCog'))
    cogTrack.append(Func(insertReviveCog, cog, deathCog, battle, cogPos, cogHpr))
    cogTrack.append(Func(notify.debug, 'before actorInterval lose'))
    cogTrack.append(ActorInterval(deathCog, 'lose', duration=COG_LOSE_DURATION))
    cogTrack.append(Func(notify.debug, 'before removeDeathCog'))
    cogTrack.append(Func(removeReviveCog, cog, deathCog, name='remove-death-cog'))
    cogTrack.append(Func(notify.debug, 'after removeDeathCog'))
    cogTrack.append(Func(cog.loop, 'neutral'))
    spinningSound = base.loader.loadSfx('phase_3.5/audio/sfx/Cog_Death.ogg')
    deathSound = base.loader.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.ogg')
    deathSoundTrack = Sequence(Wait(0.8), SoundInterval(spinningSound, duration=1.2, startTime=1.5, volume=0.2, node=cog), SoundInterval(spinningSound, duration=3.0, startTime=0.6, volume=0.8, node=cog), SoundInterval(deathSound, volume=0.32, node=cog))
    BattleParticles.loadParticles()
    smallGears = BattleParticles.createParticleEffect(file='gearExplosionSmall')
    singleGear = BattleParticles.createParticleEffect('GearExplosion', numParticles=1)
    smallGearExplosion = BattleParticles.createParticleEffect('GearExplosion', numParticles=10)
    bigGearExplosion = BattleParticles.createParticleEffect('BigGearExplosion', numParticles=30)
    gearPoint = Point3(cogPos.getX(), cogPos.getY(), cogPos.getZ() + cog.height - 0.2)
    smallGears.setPos(gearPoint)
    singleGear.setPos(gearPoint)
    smallGears.setDepthWrite(False)
    singleGear.setDepthWrite(False)
    smallGearExplosion.setPos(gearPoint)
    bigGearExplosion.setPos(gearPoint)
    smallGearExplosion.setDepthWrite(False)
    bigGearExplosion.setDepthWrite(False)
    explosionTrack = Sequence()
    explosionTrack.append(Wait(5.4))
    explosionTrack.append(createKapowExplosionTrack(battle, explosionPoint=gearPoint))
    gears1Track = Sequence(Wait(2.1), ParticleInterval(smallGears, battle, worldRelative=0, duration=4.3, cleanup=True), name='gears1Track')
    gears2MTrack = Track((0.0, explosionTrack), (0.7, ParticleInterval(singleGear, battle, worldRelative=0, duration=5.7, cleanup=True)), (5.2, ParticleInterval(smallGearExplosion, battle, worldRelative=0, duration=1.2, cleanup=True)), (5.4, ParticleInterval(bigGearExplosion, battle, worldRelative=0, duration=1.0, cleanup=True)), name='gears2MTrack')
    toonMTrack = Parallel(name='toonMTrack')
    for mtoon in battle.toons:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    for mtoon in npcs:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    return Parallel(cogTrack, deathSoundTrack, gears1Track, gears2MTrack, toonMTrack)


def createCogDeathTrack(cog, toon, battle, npcs = []):
    cogTrack = Sequence()
    cogPos, cogHpr = battle.getActorPosHpr(cog)
    if hasattr(cog, 'battleTrapProp') and cog.battleTrapProp and cog.battleTrapProp.getName() == 'traintrack' and not cog.battleTrapProp.isHidden():
        cogTrack.append(createTrainTrackAppearTrack(cog, toon, battle, npcs))
    deathCog = cog.getLoseActor()
    cogTrack.append(Func(notify.debug, 'before insertDeathCog'))
    cogTrack.append(Func(insertDeathCog, cog, deathCog, battle, cogPos, cogHpr))
    cogTrack.append(Func(notify.debug, 'before actorInterval lose'))
    cogTrack.append(ActorInterval(deathCog, 'lose', duration=COG_LOSE_DURATION))
    cogTrack.append(Func(notify.debug, 'before removeDeathCog'))
    cogTrack.append(Func(removeDeathCog, cog, deathCog, name='remove-death-cog'))
    cogTrack.append(Func(notify.debug, 'after removeDeathCog'))
    spinningSound = base.loader.loadSfx('phase_3.5/audio/sfx/Cog_Death.ogg')
    deathSound = base.loader.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.ogg')
    deathSoundTrack = Sequence(Wait(0.8), SoundInterval(spinningSound, duration=1.2, startTime=1.5, volume=0.2, node=deathCog), SoundInterval(spinningSound, duration=3.0, startTime=0.6, volume=0.8, node=deathCog), SoundInterval(deathSound, volume=0.32, node=deathCog))
    BattleParticles.loadParticles()
    smallGears = BattleParticles.createParticleEffect(file='gearExplosionSmall')
    singleGear = BattleParticles.createParticleEffect('GearExplosion', numParticles=1)
    smallGearExplosion = BattleParticles.createParticleEffect('GearExplosion', numParticles=10)
    bigGearExplosion = BattleParticles.createParticleEffect('BigGearExplosion', numParticles=30)
    gearPoint = Point3(cogPos.getX(), cogPos.getY(), cogPos.getZ() + cog.height - 0.2)
    smallGears.setPos(gearPoint)
    singleGear.setPos(gearPoint)
    smallGears.setDepthWrite(False)
    singleGear.setDepthWrite(False)
    smallGearExplosion.setPos(gearPoint)
    bigGearExplosion.setPos(gearPoint)
    smallGearExplosion.setDepthWrite(False)
    bigGearExplosion.setDepthWrite(False)
    explosionTrack = Sequence()
    explosionTrack.append(Wait(5.4))
    explosionTrack.append(createKapowExplosionTrack(battle, explosionPoint=gearPoint))
    gears1Track = Sequence(Wait(2.1), ParticleInterval(smallGears, battle, worldRelative=0, duration=4.3, cleanup=True), name='gears1Track')
    gears2MTrack = Track((0.0, explosionTrack), (0.7, ParticleInterval(singleGear, battle, worldRelative=0, duration=5.7, cleanup=True)), (5.2, ParticleInterval(smallGearExplosion, battle, worldRelative=0, duration=1.2, cleanup=True)), (5.4, ParticleInterval(bigGearExplosion, battle, worldRelative=0, duration=1.0, cleanup=True)), name='gears2MTrack')
    toonMTrack = Parallel(name='toonMTrack')
    for mtoon in battle.toons:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    for mtoon in npcs:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    return Parallel(cogTrack, deathSoundTrack, gears1Track, gears2MTrack, toonMTrack)


def createCogDodgeMultitrack(tDodge, cog, leftCogs, rightCogs):
    cogTracks = Parallel()
    cogDodgeList, sidestepAnim = avatarDodge(leftCogs, rightCogs, 'sidestep-left', 'sidestep-right')
    for s in cogDodgeList:
        cogTracks.append(Sequence(ActorInterval(s, sidestepAnim), Func(s.loop, 'neutral')))

    cogTracks.append(Sequence(ActorInterval(cog, sidestepAnim), Func(cog.loop, 'neutral')))
    cogTracks.append(Func(indicateMissed, cog))
    return Sequence(Wait(tDodge), cogTracks)


def createToonDodgeMultitrack(tDodge, toon, leftToons, rightToons):
    toonTracks = Parallel()
    if len(leftToons) > len(rightToons):
        PoLR = rightToons
        PoMR = leftToons
    else:
        PoLR = leftToons
        PoMR = rightToons
    upper = 1 + 4 * abs(len(leftToons) - len(rightToons))
    if random.randint(0, upper) > 0:
        toonDodgeList = PoLR
    else:
        toonDodgeList = PoMR
    if toonDodgeList is leftToons:
        sidestepAnim = 'sidestep-left'
        for t in toonDodgeList:
            toonTracks.append(Sequence(ActorInterval(t, sidestepAnim), Func(t.loop, 'neutral')))

    else:
        sidestepAnim = 'sidestep-right'
    toonTracks.append(Sequence(ActorInterval(toon, sidestepAnim), Func(toon.loop, 'neutral')))
    toonTracks.append(Func(indicateMissed, toon))
    return Sequence(Wait(tDodge), toonTracks)


def createCogTeaseMultiTrack(cog, delay = 0.01):
    cogTrack = Sequence(Wait(delay), ActorInterval(cog, 'victory', startTime=0.5, endTime=1.9), Func(cog.loop, 'neutral'))
    missedTrack = Sequence(Wait(delay + 0.2), Func(indicateMissed, cog, 0.9))
    return Parallel(cogTrack, missedTrack)


SPRAY_LEN = 1.5

def getSprayTrack(battle, color, origin, target, dScaleUp, dHold, dScaleDown, horizScale = 1.0, vertScale = 1.0, parent = render):
    track = Sequence()
    sprayProp = globalPropPool.getProp('spray')
    sprayScale = hidden.attachNewNode('spray-parent')
    sprayRot = hidden.attachNewNode('spray-rotate')
    spray = sprayRot
    spray.setColor(color)
    if color[3] < 1.0:
        spray.setTransparency(1)

    def showSpray(sprayScale, sprayRot, sprayProp, origin, target, parent):
        if callable(origin):
            origin = origin()
        if callable(target):
            target = target()
        sprayRot.reparentTo(parent)
        sprayRot.clearMat()
        sprayScale.reparentTo(sprayRot)
        sprayScale.clearMat()
        sprayProp.reparentTo(sprayScale)
        sprayProp.clearMat()
        sprayRot.setPos(origin)
        sprayRot.lookAt(Point3(target))

    track.append(Func(battle.movie.needRestoreRenderProp, sprayProp))
    track.append(Func(showSpray, sprayScale, sprayRot, sprayProp, origin, target, parent))

    def calcTargetScale(target = target, origin = origin, horizScale = horizScale, vertScale = vertScale):
        if callable(target):
            target = target()
        if callable(origin):
            origin = origin()
        distance = Vec3(target - origin).length()
        yScale = distance / SPRAY_LEN
        targetScale = Point3(yScale * horizScale, yScale, yScale * vertScale)
        return targetScale

    track.append(LerpScaleInterval(sprayScale, dScaleUp, calcTargetScale, startScale=PNT3_NEARZERO))
    track.append(Wait(dHold))

    def prepareToShrinkSpray(spray, sprayProp, origin, target):
        if callable(target):
            target = target()
        if callable(origin):
            origin = origin()
        sprayProp.setPos(Point3(0.0, -SPRAY_LEN, 0.0))
        spray.setPos(target)

    track.append(Func(prepareToShrinkSpray, spray, sprayProp, origin, target))
    track.append(LerpScaleInterval(sprayScale, dScaleDown, PNT3_NEARZERO))

    def hideSpray(spray, sprayScale, sprayRot, sprayProp, propPool):
        sprayProp.detachNode()
        removeProp(sprayProp)
        sprayRot.removeNode()
        sprayScale.removeNode()

    track.append(Func(hideSpray, spray, sprayScale, sprayRot, sprayProp, globalPropPool))
    track.append(Func(battle.movie.clearRenderProp, sprayProp))
    return track


T_HOLE_LEAVES_HAND = 1.708
T_TELEPORT_ANIM = 3.3
T_HOLE_CLOSES = 0.3

def getToonTeleportOutInterval(toon):
    holeActors = toon.getHoleActors()
    holes = [holeActors[0], holeActors[1]]
    hole = holes[0]
    hole2 = holes[1]
    hands = toon.getRightHands()
    delay = T_HOLE_LEAVES_HAND
    dur = T_TELEPORT_ANIM
    holeTrack = Sequence()
    holeTrack.append(Func(showProps, holes, hands))
    (holeTrack.append(Wait(0.5)),)
    holeTrack.append(Func(base.playSfx, toon.getSoundTeleport()))
    holeTrack.append(Wait(delay - 0.5))
    holeTrack.append(Func(hole.reparentTo, toon))
    holeTrack.append(Func(hole2.reparentTo, hidden))
    holeAnimTrack = Sequence()
    holeAnimTrack.append(ActorInterval(hole, 'hole', duration=dur))
    holeAnimTrack.append(Func(hideProps, holes))
    runTrack = Sequence(ActorInterval(toon, 'teleport', duration=dur), Wait(T_HOLE_CLOSES), Func(toon.detachNode))
    return Parallel(runTrack, holeAnimTrack, holeTrack)


def getToonTeleportInInterval(toon):
    hole = toon.getHoleActors()[0]
    holeAnimTrack = Sequence()
    holeAnimTrack.append(Func(toon.detachNode))
    holeAnimTrack.append(Func(hole.reparentTo, toon))
    pos = Point3(0, -2.4, 0)
    holeAnimTrack.append(Func(hole.setPos, toon, pos))
    holeAnimTrack.append(ActorInterval(hole, 'hole', startTime=T_TELEPORT_ANIM, endTime=T_HOLE_LEAVES_HAND))
    holeAnimTrack.append(ActorInterval(hole, 'hole', startTime=T_HOLE_LEAVES_HAND, endTime=T_TELEPORT_ANIM))
    holeAnimTrack.append(Func(hole.reparentTo, hidden))
    delay = T_TELEPORT_ANIM - T_HOLE_LEAVES_HAND
    jumpTrack = Sequence(Wait(delay), Func(toon.reparentTo, render), ActorInterval(toon, 'jump'))
    return Parallel(holeAnimTrack, jumpTrack)


def getCogRakeOffset(cog):
    cogName = cog.getStyleName()
    if cogName == 'glad_hander':
        return 1.4
    elif cogName == 'flunky':
        return 1.0
    elif cogName == 'cold_caller':
        return 0.7
    elif cogName == 'tightwad':
        return 1.3
    elif cogName == 'bottom_feeder':
        return 1.0
    elif cogName == 'short_change':
        return 0.8
    elif cogName == 'yesman':
        return 0.1
    elif cogName == 'micromanager':
        return 0.05
    elif cogName == 'telemarketer':
        return 0.07
    elif cogName == 'name_dropper':
        return 0.07
    elif cogName == 'penny_pincher':
        return 0.04
    elif cogName == 'bean_counter':
        return 0.36
    elif cogName == 'bloodsucker':
        return 0.41
    elif cogName == 'double_talker':
        return 0.31
    elif cogName == 'ambulance_chaser':
        return 0.39
    elif cogName == 'downsizer':
        return 0.41
    elif cogName == 'head_hunter':
        return 0.8
    elif cogName == 'corporate_raider':
        return 2.1
    elif cogName == 'the_big_cheese':
        return 1.4
    elif cogName == 'back_stabber':
        return 0.4
    elif cogName == 'spin_doctor':
        return 1.02
    elif cogName == 'legal_eagle':
        return 1.3
    elif cogName == 'big_wig':
        return 1.4
    elif cogName == 'number_cruncher':
        return 0.6
    elif cogName == 'money_bags':
        return 1.85
    elif cogName == 'loan_shark':
        return 1.4
    elif cogName == 'robber_baron':
        return 1.6
    elif cogName == 'mover_and_shaker':
        return 0.7
    elif cogName == 'two_face':
        return 0.75
    elif cogName == 'the_mingler':
        return 0.9
    elif cogName == 'mr_hollywood':
        return 1.3
    else:
        notify.warning('getCogRakeOffset(cog) - Unknown cog name: %s' % cogName)
        return 0


def startSparksIval(tntProp):
    tip = tntProp.find('**/joint_attachEmitter')
    sparks = BattleParticles.createParticleEffect(file='tnt')
    return Func(sparks.start, tip)


def indicateMissed(actor, duration = 1.1, scale = 0.7):
    actor.showHpString(TTLocalizer.AttackMissed, duration=duration, scale=scale)


def createKapowExplosionTrack(parent, explosionPoint = None, scale = 1.0):
    explosionTrack = Sequence()
    explosion = loader.loadModel('phase_3.5/models/props/explosion.bam')
    explosion.setBillboardPointEye()
    explosion.setDepthWrite(False)
    if not explosionPoint:
        explosionPoint = Point3(0, 3.6, 2.1)
    explosionTrack.append(Func(explosion.reparentTo, parent))
    explosionTrack.append(Func(explosion.setPos, explosionPoint))
    explosionTrack.append(Func(explosion.setScale, 0.4 * scale))
    explosionTrack.append(Wait(0.6))
    explosionTrack.append(Func(removeProp, explosion))
    return explosionTrack


def createCogStunInterval(cog, before, after):
    p1 = Point3(0)
    p2 = Point3(0)
    stars = globalPropPool.getProp('stun')
    stars.setColor(1, 1, 1, 1)
    stars.adjustAllPriorities(100)
    head = cog.getHeadParts()[0]
    head.calcTightBounds(p1, p2)
    return Sequence(Wait(before), Func(stars.reparentTo, head), Func(stars.setZ, max(0.0, p2[2] - 1.0)), Func(stars.loop, 'stun'), Wait(after), Func(stars.cleanup), Func(stars.removeNode))


def calcAvgCogPos(throw):
    battle = throw['battle']
    avgCogPos = Point3(0, 0, 0)
    numTargets = len(throw['target'])
    for i in range(numTargets):
        cog = throw['target'][i]['cog']
        avgCogPos += cog.getPos(battle)

    avgCogPos /= numTargets
    return avgCogPos
