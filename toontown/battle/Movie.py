from toontown.toonbase.ToontownBattleGlobals import *
from .BattleBase import *
from direct.interval.IntervalGlobal import *
from direct.showbase import DirectObject
from . import MovieFire
from . import MovieSOS
from . import MovieNPCSOS
from . import MoviePetSOS
from . import MovieHeal
from . import MovieTrap
from . import MovieLure
from . import MovieSound
from . import MovieThrow
from . import MovieSquirt
from . import MovieDrop
from . import MovieCogAttacks
from . import MovieToonVictory
from . import PlayByPlayText
from . import BattleParticles
from toontown.distributed import DelayDelete
from . import BattleExperience
from .CogBattleGlobals import *
from direct.directnotify import DirectNotifyGlobal
from . import RewardPanel
import random
from . import MovieUtil
from toontown.toon import Toon
from toontown.toonbase import ToontownGlobals
from toontown.toontowngui import TTDialog
import copy
import functools
from toontown.toonbase import TTLocalizer
from toontown.toon import NPCToons
camPos = Point3(14, 0, 10)
camHpr = Vec3(89, -30, 0)
randomBattleTimestamp = base.config.GetBool('random-battle-timestamp', 0)

class Movie(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('Movie')

    def __init__(self, battle):
        self.battle = battle
        self.track = None
        self.rewardPanel = None
        self.rewardCallback = None
        self.playByPlayText = PlayByPlayText.PlayByPlayText()
        self.playByPlayText.hide()
        self.renderProps = []
        self.hasBeenReset = 0
        self.reset()
        self.rewardHasBeenReset = 0
        self.resetReward()
        return

    def cleanup(self):
        self.reset()
        self.resetReward()
        self.battle = None
        if self.playByPlayText != None:
            self.playByPlayText.cleanup()
        self.playByPlayText = None
        if self.rewardPanel != None:
            self.rewardPanel.cleanup()
        self.rewardPanel = None
        self.rewardCallback = None
        return

    def needRestoreColor(self):
        self.restoreColor = 1

    def clearRestoreColor(self):
        self.restoreColor = 0

    def needRestoreHips(self):
        self.restoreHips = 1

    def clearRestoreHips(self):
        self.restoreHips = 0

    def needRestoreHeadScale(self):
        self.restoreHeadScale = 1

    def clearRestoreHeadScale(self):
        self.restoreHeadScale = 0

    def needRestoreToonScale(self):
        self.restoreToonScale = 1

    def clearRestoreToonScale(self):
        self.restoreToonScale = 0

    def needRestoreParticleEffect(self, effect):
        self.specialParticleEffects.append(effect)

    def clearRestoreParticleEffect(self, effect):
        if self.specialParticleEffects.count(effect) > 0:
            self.specialParticleEffects.remove(effect)

    def needRestoreRenderProp(self, prop):
        self.renderProps.append(prop)

    def clearRenderProp(self, prop):
        if self.renderProps.count(prop) > 0:
            self.renderProps.remove(prop)

    def restore(self):
        return
        for toon in self.battle.activeToons:
            toon.loop('neutral')
            origPos, origHpr = self.battle.getActorPosHpr(toon)
            toon.setPosHpr(self.battle, origPos, origHpr)
            hands = toon.getRightHands()[:]
            hands += toon.getLeftHands()
            for hand in hands:
                props = hand.getChildren()
                for prop in props:
                    if prop.getName() != 'book':
                        MovieUtil.removeProp(prop)

            if self.restoreColor == 1:
                headParts = toon.getHeadParts()
                torsoParts = toon.getTorsoParts()
                legsParts = toon.getLegsParts()
                partsList = [headParts, torsoParts, legsParts]
                for parts in partsList:
                    for partNum in range(0, parts.getNumPaths()):
                        nextPart = parts.getPath(partNum)
                        nextPart.clearColorScale()
                        nextPart.clearTransparency()

            if self.restoreHips == 1:
                parts = toon.getHipsParts()
                for partNum in range(0, parts.getNumPaths()):
                    nextPart = parts.getPath(partNum)
                    props = nextPart.getChildren()
                    for prop in props:
                        if prop.getName() == 'redtape-tube.egg':
                            MovieUtil.removeProp(prop)

            if self.restoreHeadScale == 1:
                headScale = ToontownGlobals.toonHeadScales[toon.style.getAnimal()]
                for lod in toon.getLODNames():
                    toon.getPart('head', lod).setScale(headScale)

            if self.restoreToonScale == 1:
                toon.setScale(1)
            headParts = toon.getHeadParts()
            for partNum in range(0, headParts.getNumPaths()):
                part = headParts.getPath(partNum)
                part.setHpr(0, 0, 0)
                part.setPos(0, 0, 0)

            arms = toon.findAllMatches('**/arms')
            sleeves = toon.findAllMatches('**/sleeves')
            hands = toon.findAllMatches('**/hands')
            for partNum in range(0, arms.getNumPaths()):
                armPart = arms.getPath(partNum)
                sleevePart = sleeves.getPath(partNum)
                handsPart = hands.getPath(partNum)
                armPart.setHpr(0, 0, 0)
                sleevePart.setHpr(0, 0, 0)
                handsPart.setHpr(0, 0, 0)

        for cog in self.battle.activeCogs:
            if cog._Actor__animControlDict != None:
                cog.loop('neutral')
                cog.battleTrapIsFresh = 0
                origPos, origHpr = self.battle.getActorPosHpr(cog)
                cog.setPosHpr(self.battle, origPos, origHpr)
                hands = [cog.getRightHand(), cog.getLeftHand()]
                for hand in hands:
                    props = hand.getChildren()
                    for prop in props:
                        MovieUtil.removeProp(prop)

        for effect in self.specialParticleEffects:
            if effect != None:
                effect.cleanup()

        self.specialParticleEffects = []
        for prop in self.renderProps:
            MovieUtil.removeProp(prop)

        self.renderProps = []
        return

    def _deleteTrack(self):
        if self.track:
            DelayDelete.cleanupDelayDeletes(self.track)
            self.track = None
        return

    def reset(self, finish = 0):
        if self.hasBeenReset == 1:
            return
        self.hasBeenReset = 1
        self.stop()
        self._deleteTrack()
        if finish == 1:
            self.restore()
        self.toonAttackDicts = []
        self.cogAttackDicts = []
        self.restoreColor = 0
        self.restoreHips = 0
        self.restoreHeadScale = 0
        self.restoreToonScale = 0
        self.specialParticleEffects = []
        for prop in self.renderProps:
            MovieUtil.removeProp(prop)

        self.renderProps = []

    def resetReward(self, finish = 0):
        if self.rewardHasBeenReset == 1:
            return
        self.rewardHasBeenReset = 1
        self.stop()
        self._deleteTrack()
        if finish == 1:
            self.restore()
        self.toonRewardDicts = []
        if self.rewardPanel != None:
            self.rewardPanel.destroy()
        self.rewardPanel = None
        return

    def play(self, ts, callback):
        self.hasBeenReset = 0
        ptrack = Sequence()
        camtrack = Sequence()
        if random.random() > 0.5:
            MovieUtil.shotDirection = 'left'
        else:
            MovieUtil.shotDirection = 'right'
        for s in self.battle.activeCogs:
            s.battleTrapIsFresh = 0

        tattacks, tcam = self.__doToonAttacks()
        if tattacks:
            ptrack.append(tattacks)
            camtrack.append(tcam)
        sattacks, scam = self.__doCogAttacks()
        if sattacks:
            ptrack.append(sattacks)
            camtrack.append(scam)
        ptrack.append(Func(callback))
        self._deleteTrack()
        self.track = Sequence(ptrack, name='movie-track-%d' % self.battle.doId)
        if self.battle.localToonPendingOrActive():
            self.track = Parallel(self.track, Sequence(camtrack), name='movie-track-with-cam-%d' % self.battle.doId)
        if randomBattleTimestamp == 1:
            randNum = random.randint(0, 99)
            dur = self.track.getDuration()
            ts = float(randNum) / 100.0 * dur
        self.track.delayDeletes = []
        for cog in self.battle.cogs:
            self.track.delayDeletes.append(DelayDelete.DelayDelete(cog, 'Movie.play'))

        for toon in self.battle.toons:
            self.track.delayDeletes.append(DelayDelete.DelayDelete(toon, 'Movie.play'))

        self.track.start(ts)
        return None

    def finish(self):
        self.track.finish()
        return None

    def playReward(self, ts, name, callback, noSkip = False):
        self.rewardHasBeenReset = 0
        ptrack = Sequence()
        camtrack = Sequence()
        self.rewardPanel = RewardPanel.RewardPanel(name)
        self.rewardPanel.hide()
        victory, camVictory, skipper = MovieToonVictory.doToonVictory(self.battle.localToonActive(), self.battle.activeToons, self.toonRewardIds, self.toonRewardDicts, self.deathList, self.rewardPanel, 1, self.uberList, self.helpfulToonsList, noSkip=noSkip)
        if victory:
            skipper.setIvals((ptrack, camtrack), ptrack.getDuration())
            ptrack.append(victory)
            camtrack.append(camVictory)
        ptrack.append(Func(callback))
        self._deleteTrack()
        self.track = Sequence(ptrack, name='movie-reward-track-%d' % self.battle.doId)
        if self.battle.localToonActive():
            self.track = Parallel(self.track, camtrack, name='movie-reward-track-with-cam-%d' % self.battle.doId)
        self.track.delayDeletes = []
        for t in self.battle.activeToons:
            self.track.delayDeletes.append(DelayDelete.DelayDelete(t, 'Movie.playReward'))

        skipper.setIvals((self.track,), 0.0)
        skipper.setBattle(self.battle)
        self.track.start(ts)
        return None

    def playTutorialReward(self, ts, name, callback):
        self.rewardHasBeenReset = 0
        self.rewardPanel = RewardPanel.RewardPanel(name)
        self.rewardCallback = callback
        self.questList = self.rewardPanel.getQuestIntervalList(base.localAvatar, [0,
         1,
         1,
         0], [base.localAvatar], base.localAvatar.quests[0], [], [base.localAvatar.getDoId()])
        camera.setPosHpr(0, 8, base.localAvatar.getHeight() * 0.66, 179, 15, 0)
        self.playTutorialReward_1()

    def playTutorialReward_1(self):
        self.tutRewardDialog_1 = TTDialog.TTDialog(text=TTLocalizer.MovieTutorialReward1, command=self.playTutorialReward_2, style=TTDialog.Acknowledge, fadeScreen=None, pos=(0.65, 0, 0.5), scale=0.8)
        self.tutRewardDialog_1.hide()
        self._deleteTrack()
        self.track = Sequence(name='tutorial-reward-1')
        self.track.append(Func(self.rewardPanel.initGagFrame, base.localAvatar, [0,
         0,
         0,
         0,
         0,
         0,
         0], [0,
         0,
         0,
         0], noSkip=True))
        self.track += self.rewardPanel.getTrackIntervalList(base.localAvatar, THROW_TRACK, 0, 1, 0)
        self.track.append(Func(self.tutRewardDialog_1.show))
        self.track.start()
        return

    def playTutorialReward_2(self, value):
        self.tutRewardDialog_1.cleanup()
        self.tutRewardDialog_2 = TTDialog.TTDialog(text=TTLocalizer.MovieTutorialReward2, command=self.playTutorialReward_3, style=TTDialog.Acknowledge, fadeScreen=None, pos=(0.65, 0, 0.5), scale=0.8)
        self.tutRewardDialog_2.hide()
        self._deleteTrack()
        self.track = Sequence(name='tutorial-reward-2')
        self.track.append(Wait(1.0))
        self.track += self.rewardPanel.getTrackIntervalList(base.localAvatar, SQUIRT_TRACK, 0, 1, 0)
        self.track.append(Func(self.tutRewardDialog_2.show))
        self.track.start()
        return

    def playTutorialReward_3(self, value):
        self.tutRewardDialog_2.cleanup()
        from toontown.toon import Toon
        from toontown.toon import ToonDNA

        def doneChat1(page, elapsed = 0):
            self.track2.start()

        def doneChat2(elapsed):
            self.track2.pause()
            self.track3.start()

        def uniqueName(hook):
            return 'TutorialTom-' + hook

        self.tutorialTom = Toon.Toon()
        dna = ToonDNA.ToonDNA()
        dnaList = ('dll', 'ms', 'm', 'm', 7, 0, 7, 7, 2, 6, 2, 6, 2, 16)
        dna.newToonFromProperties(*dnaList)
        self.tutorialTom.setDNA(dna)
        self.tutorialTom.setName(TTLocalizer.NPCToonNames[20000])
        self.tutorialTom.uniqueName = uniqueName
        if base.config.GetString('language', 'english') == 'japanese':
            self.tomDialogue03 = base.loader.loadSfx('phase_3.5/audio/dial/CC_tom_movie_tutorial_reward01.ogg')
            self.tomDialogue04 = base.loader.loadSfx('phase_3.5/audio/dial/CC_tom_movie_tutorial_reward02.ogg')
            self.tomDialogue05 = base.loader.loadSfx('phase_3.5/audio/dial/CC_tom_movie_tutorial_reward03.ogg')
            self.musicVolume = base.config.GetFloat('tutorial-music-volume', 0.5)
        else:
            self.tomDialogue03 = None
            self.tomDialogue04 = None
            self.tomDialogue05 = None
            self.musicVolume = 0.9
        music = base.cr.playGame.place.loader.battleMusic
        if self.questList:
            self.track1 = Sequence(Wait(1.0), Func(self.rewardPanel.initQuestFrame, base.localAvatar, copy.deepcopy(base.localAvatar.quests)), Wait(1.0), Sequence(*self.questList), Wait(1.0), Func(self.rewardPanel.hide), Func(camera.setPosHpr, render, 34, 19.88, 3.48, -90, -2.36, 0), Func(base.localAvatar.animFSM.request, 'neutral'), Func(base.localAvatar.setPosHpr, 40.31, 22.0, -0.47, 150.0, 360.0, 0.0), Wait(0.5), Func(self.tutorialTom.reparentTo, render), Func(self.tutorialTom.show), Func(self.tutorialTom.setPosHpr, 40.29, 17.9, -0.47, 11.31, 0.0, 0.07), Func(self.tutorialTom.animFSM.request, 'TeleportIn'), Wait(1.517), Func(self.tutorialTom.animFSM.request, 'neutral'), Func(self.acceptOnce, self.tutorialTom.uniqueName('doneChatPage'), doneChat1), Func(self.tutorialTom.addActive), Func(music.setVolume, self.musicVolume), Func(self.tutorialTom.setLocalPageChat, TTLocalizer.MovieTutorialReward3, 0, None, [self.tomDialogue03]), name='tutorial-reward-3a')
            self.track2 = Sequence(Func(self.acceptOnce, self.tutorialTom.uniqueName('doneChatPage'), doneChat2), Func(self.tutorialTom.setLocalPageChat, TTLocalizer.MovieTutorialReward4, 1, None, [self.tomDialogue04]), Func(self.tutorialTom.setPlayRate, 1.5, 'right-hand-start'), Func(self.tutorialTom.play, 'right-hand-start'), Wait(self.tutorialTom.getDuration('right-hand-start') / 1.5), Func(self.tutorialTom.loop, 'right-hand'), name='tutorial-reward-3b')
            self.track3 = Parallel(Sequence(Func(self.tutorialTom.setPlayRate, -1.8, 'right-hand-start'), Func(self.tutorialTom.play, 'right-hand-start'), Wait(self.tutorialTom.getDuration('right-hand-start') / 1.8), Func(self.tutorialTom.animFSM.request, 'neutral'), name='tutorial-reward-3ca'), Sequence(Wait(0.5), Func(self.tutorialTom.setChatAbsolute, TTLocalizer.MovieTutorialReward5, CFSpeech | CFTimeout, self.tomDialogue05), Wait(1.0), Func(self.tutorialTom.animFSM.request, 'TeleportOut'), Wait(self.tutorialTom.getDuration('teleport')), Wait(1.0), Func(self.playTutorialReward_4, 0), name='tutorial-reward-3cb'), name='tutorial-reward-3c')
            self.track1.start()
        else:
            self.playTutorialReward_4(0)
        return

    def playTutorialReward_4(self, value):
        base.localAvatar.setH(270)
        self.tutorialTom.removeActive()
        self.tutorialTom.delete()
        self.questList = None
        self.rewardCallback()
        return

    def stop(self):
        if self.track:
            self.track.finish()
            self._deleteTrack()
        if hasattr(self, 'track1'):
            self.track1.finish()
            self.track1 = None
        if hasattr(self, 'track2'):
            self.track2.finish()
            self.track2 = None
        if hasattr(self, 'track3'):
            self.track3.finish()
            self.track3 = None
        if self.rewardPanel:
            self.rewardPanel.hide()
        if self.playByPlayText:
            self.playByPlayText.hide()
        return

    def __doToonAttacks(self):
        if base.config.GetBool('want-toon-attack-anims', 1):
            track = Sequence(name='toon-attacks')
            camTrack = Sequence(name='toon-attacks-cam')
            ival, camIval = MovieFire.doFires(self.__findToonAttack(FIRE))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieSOS.doSOSs(self.__findToonAttack(SOS))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieNPCSOS.doNPCSOSs(self.__findToonAttack(NPCSOS))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MoviePetSOS.doPetSOSs(self.__findToonAttack(PETSOS))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            hasHealBonus = self.battle.getInteractivePropTrackBonus() == HEAL
            ival, camIval = MovieHeal.doHeals(self.__findToonAttack(HEAL), hasHealBonus)
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieTrap.doTraps(self.__findToonAttack(TRAP))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieLure.doLures(self.__findToonAttack(LURE))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieSound.doSounds(self.__findToonAttack(SOUND))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieThrow.doThrows(self.__findToonAttack(THROW))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieSquirt.doSquirts(self.__findToonAttack(SQUIRT))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            ival, camIval = MovieDrop.doDrops(self.__findToonAttack(DROP))
            if ival:
                track.append(ival)
                camTrack.append(camIval)
            if len(track) == 0:
                return (None, None)
            else:
                return (track, camTrack)
        else:
            return (None, None)
        return None

    def genRewardDicts(self, id0, origExp0, earnedExp0, origQuests0, items0, missedItems0, origMerits0, merits0, parts0, id1, origExp1, earnedExp1, origQuests1, items1, missedItems1, origMerits1, merits1, parts1, id2, origExp2, earnedExp2, origQuests2, items2, missedItems2, origMerits2, merits2, parts2, id3, origExp3, earnedExp3, origQuests3, items3, missedItems3, origMerits3, merits3, parts3, deathList, uberList, helpfulToonsList):
        self.deathList = deathList
        self.helpfulToonsList = helpfulToonsList
        entries = ((id0,
          origExp0,
          earnedExp0,
          origQuests0,
          items0,
          missedItems0,
          origMerits0,
          merits0,
          parts0),
         (id1,
          origExp1,
          earnedExp1,
          origQuests1,
          items1,
          missedItems1,
          origMerits1,
          merits1,
          parts1),
         (id2,
          origExp2,
          earnedExp2,
          origQuests2,
          items2,
          missedItems2,
          origMerits2,
          merits2,
          parts2),
         (id3,
          origExp3,
          earnedExp3,
          origQuests3,
          items3,
          missedItems3,
          origMerits3,
          merits3,
          parts3))
        self.toonRewardDicts = BattleExperience.genRewardDicts(entries)
        self.toonRewardIds = [id0,
         id1,
         id2,
         id3]
        self.uberList = uberList

    def genAttackDicts(self, toons, cogs, id0, tr0, le0, tg0, hp0, ac0, hpb0, kbb0, died0, revive0, id1, tr1, le1, tg1, hp1, ac1, hpb1, kbb1, died1, revive1, id2, tr2, le2, tg2, hp2, ac2, hpb2, kbb2, died2, revive2, id3, tr3, le3, tg3, hp3, ac3, hpb3, kbb3, died3, revive3, sid0, at0, stg0, dm0, sd0, sb0, st0, sid1, at1, stg1, dm1, sd1, sb1, st1, sid2, at2, stg2, dm2, sd2, sb2, st2, sid3, at3, stg3, dm3, sd3, sb3, st3):
        if self.track and self.track.isPlaying():
            self.notify.warning('genAttackDicts() - track is playing!')
        toonAttacks = ((id0,
          tr0,
          le0,
          tg0,
          hp0,
          ac0,
          hpb0,
          kbb0,
          died0,
          revive0),
         (id1,
          tr1,
          le1,
          tg1,
          hp1,
          ac1,
          hpb1,
          kbb1,
          died1,
          revive1),
         (id2,
          tr2,
          le2,
          tg2,
          hp2,
          ac2,
          hpb2,
          kbb2,
          died2,
          revive2),
         (id3,
          tr3,
          le3,
          tg3,
          hp3,
          ac3,
          hpb3,
          kbb3,
          died3,
          revive3))
        self.__genToonAttackDicts(toons, cogs, toonAttacks)
        cogAttacks = ((sid0,
          at0,
          stg0,
          dm0,
          sd0,
          sb0,
          st0),
         (sid1,
          at1,
          stg1,
          dm1,
          sd1,
          sb1,
          st1),
         (sid2,
          at2,
          stg2,
          dm2,
          sd2,
          sb2,
          st2),
         (sid3,
          at3,
          stg3,
          dm3,
          sd3,
          sb3,
          st3))
        self.__genCogAttackDicts(toons, cogs, cogAttacks)

    def __genToonAttackDicts(self, toons, cogs, toonAttacks):
        for ta in toonAttacks:
            targetGone = 0
            track = ta[TOON_TRACK_COL]
            if track != NO_ATTACK:
                adict = {}
                toonIndex = ta[TOON_ID_COL]
                toonId = toons[toonIndex]
                toon = self.battle.findToon(toonId)
                if toon == None:
                    continue
                level = ta[TOON_LVL_COL]
                adict['toon'] = toon
                adict['track'] = track
                adict['level'] = level
                hps = ta[TOON_HP_COL]
                kbbonuses = ta[TOON_KBBONUS_COL]
                if track == NPCSOS:
                    adict['npcId'] = ta[TOON_TGT_COL]
                    toonId = ta[TOON_TGT_COL]
                    track, npc_level, npc_hp = NPCToons.getNPCTrackLevelHp(adict['npcId'])
                    if track == None:
                        track = NPCSOS
                    adict['track'] = track
                    adict['level'] = npc_level
                elif track == PETSOS:
                    petId = ta[TOON_TGT_COL]
                    adict['toonId'] = toonId
                    adict['petId'] = petId
                if track == SOS:
                    targetId = ta[TOON_TGT_COL]
                    if targetId == base.localAvatar.doId:
                        target = base.localAvatar
                        adict['targetType'] = 'callee'
                    elif toon == base.localAvatar:
                        target = base.cr.identifyAvatar(targetId)
                        adict['targetType'] = 'caller'
                    else:
                        target = None
                        adict['targetType'] = 'observer'
                    adict['target'] = target
                elif track == NPCSOS or track == NPC_COGS_MISS or track == NPC_TOONS_HIT or track == NPC_RESTOCK_GAGS or track == PETSOS:
                    adict['special'] = 1
                    toonHandles = []
                    for t in toons:
                        if t != -1:
                            target = self.battle.findToon(t)
                            if target == None:
                                continue
                            if track == NPC_TOONS_HIT and t == toonId:
                                continue
                            toonHandles.append(target)

                    adict['toons'] = toonHandles
                    cogHandles = []
                    for s in cogs:
                        if s != -1:
                            target = self.battle.findCog(s)
                            if target == None:
                                continue
                            cogHandles.append(target)

                    adict['cogs'] = cogHandles
                    if track == PETSOS:
                        del adict['special']
                        targets = []
                        for t in toons:
                            if t != -1:
                                target = self.battle.findToon(t)
                                if target == None:
                                    continue
                                tdict = {}
                                tdict['toon'] = target
                                tdict['hp'] = hps[toons.index(t)]
                                self.notify.debug('PETSOS: toon: %d healed for hp: %d' % (target.doId, hps[toons.index(t)]))
                                targets.append(tdict)

                        if len(targets) > 0:
                            adict['target'] = targets
                elif track == HEAL:
                    if levelAffectsGroup(HEAL, level):
                        targets = []
                        for t in toons:
                            if t != toonId and t != -1:
                                target = self.battle.findToon(t)
                                if target == None:
                                    continue
                                tdict = {}
                                tdict['toon'] = target
                                tdict['hp'] = hps[toons.index(t)]
                                self.notify.debug('HEAL: toon: %d healed for hp: %d' % (target.doId, hps[toons.index(t)]))
                                targets.append(tdict)

                        if len(targets) > 0:
                            adict['target'] = targets
                        else:
                            targetGone = 1
                    else:
                        targetIndex = ta[TOON_TGT_COL]
                        if targetIndex < 0:
                            targetGone = 1
                        else:
                            targetId = toons[targetIndex]
                            target = self.battle.findToon(targetId)
                            if target != None:
                                tdict = {}
                                tdict['toon'] = target
                                tdict['hp'] = hps[targetIndex]
                                adict['target'] = tdict
                            else:
                                targetGone = 1
                elif attackAffectsGroup(track, level, ta[TOON_TRACK_COL]):
                    targets = []
                    for s in cogs:
                        if s != -1:
                            target = self.battle.findCog(s)
                            if ta[TOON_TRACK_COL] == NPCSOS:
                                if track == LURE and self.battle.isCogLured(target) == 1:
                                    continue
                                elif track == TRAP and (self.battle.isCogLured(target) == 1 or target.battleTrap != NO_TRAP):
                                    continue
                            targetIndex = cogs.index(s)
                            sdict = {}
                            sdict['cog'] = target
                            sdict['hp'] = hps[targetIndex]
                            if ta[TOON_TRACK_COL] == NPCSOS and track == DROP and hps[targetIndex] == 0:
                                continue
                            sdict['kbbonus'] = kbbonuses[targetIndex]
                            sdict['died'] = ta[COG_DIED_COL] & 1 << targetIndex
                            sdict['revived'] = ta[COG_REVIVE_COL] & 1 << targetIndex
                            if sdict['died'] != 0:
                                pass
                            sdict['leftCogs'] = []
                            sdict['rightCogs'] = []
                            targets.append(sdict)

                    adict['target'] = targets
                else:
                    targetIndex = ta[TOON_TGT_COL]
                    if targetIndex < 0:
                        targetGone = 1
                    else:
                        targetId = cogs[targetIndex]
                        target = self.battle.findCog(targetId)
                        sdict = {}
                        sdict['cog'] = target
                        if self.battle.activeCogs.count(target) == 0:
                            targetGone = 1
                            cogIndex = 0
                        else:
                            cogIndex = self.battle.activeCogs.index(target)
                        leftCogs = []
                        for si in range(0, cogIndex):
                            acog = self.battle.activeCogs[si]
                            if self.battle.isCogLured(acog) == 0:
                                leftCogs.append(acog)

                        lenCogs = len(self.battle.activeCogs)
                        rightCogs = []
                        if lenCogs > cogIndex + 1:
                            for si in range(cogIndex + 1, lenCogs):
                                acog = self.battle.activeCogs[si]
                                if self.battle.isCogLured(acog) == 0:
                                    rightCogs.append(acog)

                        sdict['leftCogs'] = leftCogs
                        sdict['rightCogs'] = rightCogs
                        sdict['hp'] = hps[targetIndex]
                        sdict['kbbonus'] = kbbonuses[targetIndex]
                        sdict['died'] = ta[COG_DIED_COL] & 1 << targetIndex
                        sdict['revived'] = ta[COG_REVIVE_COL] & 1 << targetIndex
                        if sdict['revived'] != 0:
                            pass
                        if sdict['died'] != 0:
                            pass
                        if track == DROP or track == TRAP:
                            adict['target'] = [sdict]
                        else:
                            adict['target'] = sdict
                adict['hpbonus'] = ta[TOON_HPBONUS_COL]
                adict['sidestep'] = ta[TOON_ACCBONUS_COL]
                if 'npcId' in adict:
                    adict['sidestep'] = 0
                adict['battle'] = self.battle
                adict['playByPlayText'] = self.playByPlayText
                if targetGone == 0:
                    self.toonAttackDicts.append(adict)
                else:
                    self.notify.warning('genToonAttackDicts() - target gone!')

        def compFunc(a, b):
            alevel = a['level']
            blevel = b['level']
            if alevel > blevel:
                return 1
            elif alevel < blevel:
                return -1
            return 0

        self.toonAttackDicts.sort(key=functools.cmp_to_key(compFunc))
        return

    def __findToonAttack(self, track):
        setCapture = 0
        tp = []
        for ta in self.toonAttackDicts:
            if ta['track'] == track or track == NPCSOS and 'special' in ta:
                tp.append(ta)
                if track == SQUIRT:
                    setCapture = 1

        if track == TRAP:
            sortedTraps = []
            for attack in tp:
                if 'npcId' not in attack:
                    sortedTraps.append(attack)

            for attack in tp:
                if 'npcId' in attack:
                    sortedTraps.append(attack)

            tp = sortedTraps
        if setCapture:
            pass
        return tp

    def __genCogAttackDicts(self, toons, cogs, cogAttacks):
        for sa in cogAttacks:
            targetGone = 0
            attack = sa[COG_ATK_COL]
            if attack != NO_ATTACK:
                cogIndex = sa[COG_ID_COL]
                cogId = cogs[cogIndex]
                cog = self.battle.findCog(cogId)
                if cog == None:
                    self.notify.error('cog: %d not in battle!' % cogId)
                adict = getCogAttack(cog.getStyleName(), cog.getLevel(), attack)
                adict['cog'] = cog
                adict['battle'] = self.battle
                adict['playByPlayText'] = self.playByPlayText
                adict['taunt'] = sa[COG_TAUNT_COL]
                hps = sa[COG_HP_COL]
                if adict['group'] == ATK_TGT_GROUP:
                    targets = []
                    for t in toons:
                        if t != -1:
                            target = self.battle.findToon(t)
                            if target == None:
                                continue
                            targetIndex = toons.index(t)
                            tdict = {}
                            tdict['toon'] = target
                            tdict['hp'] = hps[targetIndex]
                            self.notify.debug('DAMAGE: toon: %d hit for hp: %d' % (target.doId, hps[targetIndex]))
                            toonDied = sa[TOON_DIED_COL] & 1 << targetIndex
                            tdict['died'] = toonDied
                            targets.append(tdict)

                    if len(targets) > 0:
                        adict['target'] = targets
                    else:
                        targetGone = 1
                elif adict['group'] == ATK_TGT_SINGLE:
                    targetIndex = sa[COG_TGT_COL]
                    targetId = toons[targetIndex]
                    target = self.battle.findToon(targetId)
                    if target == None:
                        targetGone = 1
                        break
                    tdict = {}
                    tdict['toon'] = target
                    tdict['hp'] = hps[targetIndex]
                    self.notify.debug('DAMAGE: toon: %d hit for hp: %d' % (target.doId, hps[targetIndex]))
                    toonDied = sa[TOON_DIED_COL] & 1 << targetIndex
                    tdict['died'] = toonDied
                    toonIndex = self.battle.activeToons.index(target)
                    rightToons = []
                    for ti in range(0, toonIndex):
                        rightToons.append(self.battle.activeToons[ti])

                    lenToons = len(self.battle.activeToons)
                    leftToons = []
                    if lenToons > toonIndex + 1:
                        for ti in range(toonIndex + 1, lenToons):
                            leftToons.append(self.battle.activeToons[ti])

                    tdict['leftToons'] = leftToons
                    tdict['rightToons'] = rightToons
                    adict['target'] = tdict
                else:
                    self.notify.warning('got cog attack not group or single!')
                if targetGone == 0:
                    self.cogAttackDicts.append(adict)
                else:
                    self.notify.warning('genCogAttackDicts() - target gone!')

        return

    def __doCogAttacks(self):
        if base.config.GetBool('want-cog-anims', 1):
            track = Sequence(name='cog-attacks')
            camTrack = Sequence(name='cog-attacks-cam')
            isLocalToonSad = False
            for a in self.cogAttackDicts:
                ival, camIval = MovieCogAttacks.doCogAttack(a)
                if ival:
                    track.append(ival)
                    camTrack.append(camIval)
                targetField = a.get('target')
                if targetField is None:
                    continue
                if a['group'] == ATK_TGT_GROUP:
                    for target in targetField:
                        if target['died'] and target['toon'].doId == base.localAvatar.doId:
                            isLocalToonSad = True

                elif a['group'] == ATK_TGT_SINGLE:
                    if targetField['died'] and targetField['toon'].doId == base.localAvatar.doId:
                        isLocalToonSad = True
                if isLocalToonSad:
                    break

            if len(track) == 0:
                return (None, None)
            return (track, camTrack)
        else:
            return (None, None)
        return
