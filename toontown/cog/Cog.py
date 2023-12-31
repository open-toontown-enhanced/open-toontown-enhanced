from direct.actor import Actor
from otp.avatar import Avatar
from . import CogDNA
from toontown.toonbase import ToontownGlobals
from panda3d.core import *
from panda3d.otp import *
from toontown.battle import CogBattleGlobals
from direct.task.Task import Task
from toontown.battle import BattleProps
from toontown.toonbase import TTLocalizer
aSize = 6.06
bSize = 5.29
cSize = 4.14
CogDialogArray = []
SkelCogDialogArray = []
AllCogs = (('walk', 'walk'), ('run', 'walk'), ('neutral', 'neutral'))
AllCogsMinigame = (('victory', 'victory'),
 ('flail', 'flailing'),
 ('tug-o-war', 'tug-o-war'),
 ('slip-backward', 'slip-backward'),
 ('slip-forward', 'slip-forward'))
AllCogsTutorialBattle = (('lose', 'lose'), ('pie-small-react', 'pie-small'), ('squirt-small-react', 'squirt-small'))
AllCogsBattle = (('drop-react', 'anvil-drop'),
 ('flatten', 'drop'),
 ('sidestep-left', 'sidestep-left'),
 ('sidestep-right', 'sidestep-right'),
 ('squirt-large-react', 'squirt-large'),
 ('landing', 'landing'),
 ('reach', 'walknreach'),
 ('rake-react', 'rake'),
 ('hypnotized', 'hypnotize'),
 ('soak', 'soak'))
CogsCEOBattle = (('sit', 'sit'),
 ('sit-eat-in', 'sit-eat-in'),
 ('sit-eat-loop', 'sit-eat-loop'),
 ('sit-eat-out', 'sit-eat-out'),
 ('sit-angry', 'sit-angry'),
 ('sit-hungry-left', 'leftsit-hungry'),
 ('sit-hungry-right', 'rightsit-hungry'),
 ('sit-lose', 'sit-lose'),
 ('tray-walk', 'tray-walk'),
 ('tray-neutral', 'tray-neutral'),
 ('sit-lose', 'sit-lose'))
flunky = (('throw-paper', 'throw-paper', 3.5), ('phone', 'phone', 3.5), ('shredder', 'shredder', 3.5))
pencil_pusher = (('pencil-sharpener', 'pencil-sharpener', 5),
 ('pen-squirt', 'pen-squirt', 5),
 ('hold-eraser', 'hold-eraser', 5),
 ('finger-wag', 'finger-wag', 5),
 ('hold-pencil', 'hold-pencil', 5))
yesman = (('throw-paper', 'throw-paper', 5),
 ('golf-club-swing', 'golf-club-swing', 5),
 ('magic3', 'magic3', 5),
 ('rubber-stamp', 'rubber-stamp', 5),
 ('smile', 'smile', 5))
micromanager = (('speak', 'speak', 5),
 ('effort', 'effort', 5),
 ('magic1', 'magic1', 5),
 ('pen-squirt', 'fountain-pen', 5),
 ('finger-wag', 'finger-wag', 5))
downsizer = (('magic1', 'magic1', 5),
 ('magic2', 'magic2', 5),
 ('throw-paper', 'throw-paper', 5),
 ('magic3', 'magic3', 5))
head_hunter = (('pen-squirt', 'fountain-pen', 7),
 ('glower', 'glower', 5),
 ('throw-paper', 'throw-paper', 5),
 ('magic1', 'magic1', 5),
 ('roll-o-dex', 'roll-o-dex', 5))
corporate_raider = (('pickpocket', 'pickpocket', 5), ('throw-paper', 'throw-paper', 3.5), ('glower', 'glower', 5))
the_big_cheese = (('cigar-smoke', 'cigar-smoke', 8),
 ('glower', 'glower', 5),
 ('song-and-dance', 'song-and-dance', 8),
 ('golf-club-swing', 'golf-club-swing', 5))
cold_caller = (('speak', 'speak', 5),
 ('glower', 'glower', 5),
 ('phone', 'phone', 3.5),
 ('finger-wag', 'finger-wag', 5))
telemarketer = (('speak', 'speak', 5),
 ('throw-paper', 'throw-paper', 5),
 ('pickpocket', 'pickpocket', 5),
 ('roll-o-dex', 'roll-o-dex', 5),
 ('finger-wag', 'finger-wag', 5))
name_dropper = (('pickpocket', 'pickpocket', 5),
 ('roll-o-dex', 'roll-o-dex', 5),
 ('magic3', 'magic3', 5),
 ('smile', 'smile', 5))
glad_hander = (('speak', 'speak', 5), ('pen-squirt', 'fountain-pen', 5), ('rubber-stamp', 'rubber-stamp', 5))
mover_and_shaker = (('effort', 'effort', 5),
 ('throw-paper', 'throw-paper', 5),
 ('stomp', 'stomp', 5),
 ('quick-jump', 'jump', 6))
two_face = (('phone', 'phone', 5),
 ('smile', 'smile', 5),
 ('throw-object', 'throw-object', 5),
 ('glower', 'glower', 5))
mingler = (('speak', 'speak', 5),
 ('magic2', 'magic2', 5),
 ('magic1', 'magic1', 5),
 ('golf-club-swing', 'golf-club-swing', 5))
mr_hollywood = (('magic1', 'magic1', 5),
 ('smile', 'smile', 5),
 ('golf-club-swing', 'golf-club-swing', 5),
 ('song-and-dance', 'song-and-dance', 5))
short_change = (('throw-paper', 'throw-paper', 3.5), ('watercooler', 'watercooler', 5), ('pickpocket', 'pickpocket', 5))
penny_pincher = (('throw-paper', 'throw-paper', 5), ('glower', 'glower', 5), ('finger-wag', 'fingerwag', 5))
tightwad = (('throw-paper', 'throw-paper', 3.5),
 ('glower', 'glower', 5),
 ('magic2', 'magic2', 5),
 ('finger-wag', 'finger-wag', 5))
bean_counter = (('phone', 'phone', 5), ('hold-pencil', 'hold-pencil', 5))
number_cruncher = (('phone', 'phone', 5), ('throw-object', 'throw-object', 5))
money_bags = (('magic1', 'magic1', 5), ('throw-paper', 'throw-paper', 3.5))
loan_shark = (('throw-paper', 'throw-paper', 5), ('throw-object', 'throw-object', 5), ('hold-pencil', 'hold-pencil', 5))
robber_baron = (('glower', 'glower', 5), ('magic1', 'magic1', 5), ('golf-club-swing', 'golf-club-swing', 5))
bottom_feeder = (('pickpocket', 'pickpocket', 5),
 ('rubber-stamp', 'rubber-stamp', 5),
 ('shredder', 'shredder', 3.5),
 ('watercooler', 'watercooler', 5))
bloodsucker = (('effort', 'effort', 5),
 ('throw-paper', 'throw-paper', 5),
 ('throw-object', 'throw-object', 5),
 ('magic1', 'magic1', 5))
double_talker = (('rubber-stamp', 'rubber-stamp', 5),
 ('throw-paper', 'throw-paper', 5),
 ('speak', 'speak', 5),
 ('finger-wag', 'fingerwag', 5),
 ('throw-paper', 'throw-paper', 5))
ambulance_chaser = (('throw-object', 'throw-object', 5),
 ('roll-o-dex', 'roll-o-dex', 5),
 ('stomp', 'stomp', 5),
 ('phone', 'phone', 5),
 ('throw-paper', 'throw-paper', 5))
back_stabber = (('magic1', 'magic1', 5), ('throw-paper', 'throw-paper', 5), ('finger-wag', 'fingerwag', 5))
spin_doctor = (('magic2', 'magic2', 5),
 ('quick-jump', 'jump', 6),
 ('stomp', 'stomp', 5),
 ('magic3', 'magic3', 5),
 ('hold-pencil', 'hold-pencil', 5),
 ('throw-paper', 'throw-paper', 5))
legal_eagle = (('speak', 'speak', 5),
 ('throw-object', 'throw-object', 5),
 ('glower', 'glower', 5),
 ('throw-paper', 'throw-paper', 5))
big_wig = (('finger-wag', 'fingerwag', 5),
 ('cigar-smoke', 'cigar-smoke', 8),
 ('gavel', 'gavel', 8),
 ('magic1', 'magic1', 5),
 ('throw-object', 'throw-object', 5),
 ('throw-paper', 'throw-paper', 5))
if not ConfigVariableBool('want-new-cogs', 0).value:
    ModelDict = {'a': ('/models/char/suitA-', 4),
     'b': ('/models/char/suitB-', 4),
     'c': ('/models/char/suitC-', 3.5)}
    TutorialModelDict = {'a': ('/models/char/suitA-', 4),
     'b': ('/models/char/suitB-', 4),
     'c': ('/models/char/suitC-', 3.5)}
else:
    ModelDict = {'a': ('/models/char/tt_a_ene_cga_', 4),
     'b': ('/models/char/tt_a_ene_cgb_', 4),
     'c': ('/models/char/tt_a_ene_cgc_', 3.5)}
    TutorialModelDict = {'a': ('/models/char/tt_a_ene_cga_', 4),
     'b': ('/models/char/tt_a_ene_cgb_', 4),
     'c': ('/models/char/tt_a_ene_cgc_', 3.5)}
HeadModelDict = {'a': ('/models/char/suitA-', 4),
 'b': ('/models/char/suitB-', 4),
 'c': ('/models/char/suitC-', 3.5)}

def loadTutorialCog():
    loader.loadModel('phase_3.5/models/char/suitC-mod').node()
    loadDialog(1)


def loadCogs(level):
    loadCogModelsAndAnims(level, flag=1)
    loadDialog(level)


def unloadCogs(level):
    loadCogModelsAndAnims(level, flag=0)
    unloadDialog(level)


def loadCogModelsAndAnims(level, flag = 0):
    for key in list(ModelDict.keys()):
        model, phase = ModelDict[key]
        if ConfigVariableBool('want-new-cogs', 0).value:
            headModel, headPhase = HeadModelDict[key]
        else:
            headModel, headPhase = ModelDict[key]
        if flag:
            if ConfigVariableBool('want-new-cogs', 0).value:
                filepath = 'phase_3.5' + model + 'zero'
                if cogExists(model + 'zero.bam'):
                    loader.loadModel(filepath).node()
            else:
                loader.loadModel('phase_3.5' + model + 'mod').node()
            loader.loadModel('phase_' + str(headPhase) + headModel + 'heads').node()
        else:
            if ConfigVariableBool('want-new-cogs', 0).value:
                filepath = 'phase_3.5' + model + 'zero'
                if cogExists(model + 'zero.bam'):
                    loader.unloadModel(filepath)
            else:
                loader.unloadModel('phase_3.5' + model + 'mod')
            loader.unloadModel('phase_' + str(headPhase) + headModel + 'heads')


def cogExists(filePrefix):
    searchPath = DSearchPath()
    if __debug__:
        searchPath.appendDirectory(Filename('resources/phase_3.5'))
    filePrefix = filePrefix.strip('/')
    pfile = Filename(filePrefix)
    found = vfs.resolveFilename(pfile, searchPath)
    if not found:
        return False
    return True


def loadCogAnims(cog, flag = 1):
    if cog in CogDNA.cogHeadTypes:
        try:
            animList = eval(cog)
        except NameError:
            animList = ()

    else:
        print('Invalid cog name: ', cog)
        return -1
    for anim in animList:
        phase = 'phase_' + str(anim[2])
        filePrefix = ModelDict[bodyType][0]
        animName = filePrefix + anim[1]
        if flag:
            loader.loadModel(animName).node()
        else:
            loader.unloadModel(animName)


def loadDialog(level):
    global CogDialogArray
    if len(CogDialogArray) > 0:
        return
    else:
        loadPath = 'phase_3.5/audio/dial/'
        CogDialogFiles = ['COG_VO_grunt',
         'COG_VO_murmur',
         'COG_VO_statement',
         'COG_VO_question']
        for file in CogDialogFiles:
            CogDialogArray.append(base.loader.loadSfx(loadPath + file + '.ogg'))

        CogDialogArray.append(CogDialogArray[2])
        CogDialogArray.append(CogDialogArray[2])


def loadSkelDialog():
    global SkelCogDialogArray
    if len(SkelCogDialogArray) > 0:
        return
    else:
        grunt = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_grunt.ogg')
        murmur = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_murmur.ogg')
        statement = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_statement.ogg')
        question = loader.loadSfx('phase_5/audio/sfx/Skel_COG_VO_question.ogg')
        SkelCogDialogArray = [grunt,
         murmur,
         statement,
         question,
         statement,
         statement]


def unloadDialog(level):
    global CogDialogArray
    CogDialogArray = []


def unloadSkelDialog():
    global SkelCogDialogArray
    SkelCogDialogArray = []


def attachCogHead(node, cogName):
    cogIndex = CogDNA.cogHeadTypes.index(cogName)
    CogDNA = CogDNA.CogDNA()
    CogDNA.newCog(cogName)
    cog = Cog()
    cog.setDNA(CogDNA)
    headParts = cog.getHeadParts()
    head = node.attachNewNode('head')
    for part in headParts:
        copyPart = part.copyTo(head)
        copyPart.setDepthTest(1)
        copyPart.setDepthWrite(1)

    cog.delete()
    cog = None
    p1 = Point3()
    p2 = Point3()
    head.calcTightBounds(p1, p2)
    d = p2 - p1
    biggest = max(d[0], d[2])
    column = cogIndex % CogDNA.cogsPerDept
    s = (0.2 + column / 100.0) / biggest
    pos = -0.14 + (CogDNA.cogsPerDept - column - 1) / 135.0
    head.setPosHprScale(0, 0, pos, 180, 0, 0, s, s, s)
    return head


class Cog(Avatar.Avatar):
    healthColors = (Vec4(0, 1, 0, 1),
     Vec4(1, 1, 0, 1),
     Vec4(1, 0.5, 0, 1),
     Vec4(1, 0, 0, 1),
     Vec4(0.3, 0.3, 0.3, 1))
    healthGlowColors = (Vec4(0.25, 1, 0.25, 0.5),
     Vec4(1, 1, 0.25, 0.5),
     Vec4(1, 0.5, 0.25, 0.5),
     Vec4(1, 0.25, 0.25, 0.5),
     Vec4(0.3, 0.3, 0.3, 0))
    medallionColors = {'c': Vec4(0.863, 0.776, 0.769, 1.0),
     's': Vec4(0.843, 0.745, 0.745, 1.0),
     'l': Vec4(0.749, 0.776, 0.824, 1.0),
     'm': Vec4(0.749, 0.769, 0.749, 1.0)}

    def __init__(self):
        try:
            self.Cog_initialized
            return
        except:
            self.Cog_initialized = 1

        Avatar.Avatar.__init__(self)
        self.setFont(ToontownGlobals.getCogFont())
        self.setPlayerType(NametagGroup.CCSuit)
        self.setPickable(1)
        self.leftHand = None
        self.rightHand = None
        self.shadowJoint = None
        self.nametagJoint = None
        self.headParts = []
        self.healthBar = None
        self.healthCondition = 0
        self.isDisguised = 0
        self.isWaiter = 0
        self.isRental = 0
        return

    def delete(self):
        try:
            self.Cog_deleted
        except:
            self.Cog_deleted = 1
            if self.leftHand:
                self.leftHand.removeNode()
                self.leftHand = None
            if self.rightHand:
                self.rightHand.removeNode()
                self.rightHand = None
            if self.shadowJoint:
                self.shadowJoint.removeNode()
                self.shadowJoint = None
            if self.nametagJoint:
                self.nametagJoint.removeNode()
                self.nametagJoint = None
            for part in self.headParts:
                part.removeNode()

            self.headParts = []
            self.removeHealthBar()
            Avatar.Avatar.delete(self)

        return

    def setHeight(self, height):
        Avatar.Avatar.setHeight(self, height)
        self.nametag3d.setPos(0, 0, height + 1.0)

    def getRadius(self):
        return 2

    def setDNAString(self, dnaString):
        self.dna = CogDNA.CogDNA()
        self.dna.makeFromNetString(dnaString)
        self.setDNA(self.dna)

    def setDNA(self, dna):
        if self.style:
            pass
        else:
            self.style = dna
            self.generateCog()
            self.initializeDropShadow()
            self.initializeNametag3d()

    def generateCog(self):
        dna = self.style
        self.headParts = []
        self.headColor = None
        self.headTexture = None
        self.loseActor = None
        self.isSkeleton = 0
        if dna.name == 'flunky':
            self.scale = 4.0 / cSize
            self.handColor = CogDNA.corpPolyColor
            self.generateBody()
            self.generateHead('flunky')
            self.generateHead('glasses')
            self.setHeight(4.88)
        elif dna.name == 'pencil_pusher':
            self.scale = 3.35 / bSize
            self.handColor = CogDNA.corpPolyColor
            self.generateBody()
            self.generateHead('pencilpusher')
            self.setHeight(5.0)
        elif dna.name == 'yesman':
            self.scale = 4.125 / aSize
            self.handColor = CogDNA.corpPolyColor
            self.generateBody()
            self.generateHead('yesman')
            self.setHeight(5.28)
        elif dna.name == 'micromanager':
            self.scale = 2.5 / cSize
            self.handColor = CogDNA.corpPolyColor
            self.generateBody()
            self.generateHead('micromanager')
            self.setHeight(3.25)
        elif dna.name == 'downsizer':
            self.scale = 4.5 / bSize
            self.handColor = CogDNA.corpPolyColor
            self.generateBody()
            self.generateHead('beancounter')
            self.setHeight(6.08)
        elif dna.name == 'head_hunter':
            self.scale = 6.5 / aSize
            self.handColor = CogDNA.corpPolyColor
            self.generateBody()
            self.generateHead('headhunter')
            self.setHeight(7.45)
        elif dna.name == 'corporate_raider':
            self.scale = 6.75 / cSize
            self.handColor = VBase4(0.85, 0.55, 0.55, 1.0)
            self.generateBody()
            self.headTexture = 'corporate-raider.png'
            self.generateHead('flunky')
            self.setHeight(8.23)
        elif dna.name == 'the_big_cheese':
            self.scale = 7.0 / aSize
            self.handColor = VBase4(0.75, 0.95, 0.75, 1.0)
            self.generateBody()
            self.generateHead('bigcheese')
            self.setHeight(9.34)
        elif dna.name == 'bottom_feeder':
            self.scale = 4.0 / cSize
            self.handColor = CogDNA.legalPolyColor
            self.generateBody()
            self.headTexture = 'bottom-feeder.png'
            self.generateHead('tightwad')
            self.setHeight(4.81)
        elif dna.name == 'bloodsucker':
            self.scale = 4.375 / bSize
            self.handColor = VBase4(0.95, 0.95, 1.0, 1.0)
            self.generateBody()
            self.headTexture = 'blood-sucker.png'
            self.generateHead('movershaker')
            self.setHeight(6.17)
        elif dna.name == 'double_talker':
            self.scale = 4.25 / aSize
            self.handColor = CogDNA.legalPolyColor
            self.generateBody()
            self.headTexture = 'double-talker.png'
            self.generateHead('twoface')
            self.setHeight(5.63)
        elif dna.name == 'ambulance_chaser':
            self.scale = 4.35 / bSize
            self.handColor = CogDNA.legalPolyColor
            self.generateBody()
            self.generateHead('ambulancechaser')
            self.setHeight(6.39)
        elif dna.name == 'back_stabber':
            self.scale = 4.5 / aSize
            self.handColor = CogDNA.legalPolyColor
            self.generateBody()
            self.generateHead('backstabber')
            self.setHeight(6.71)
        elif dna.name == 'spin_doctor':
            self.scale = 5.65 / bSize
            self.handColor = VBase4(0.5, 0.8, 0.75, 1.0)
            self.generateBody()
            self.headTexture = 'spin-doctor.png'
            self.generateHead('telemarketer')
            self.setHeight(7.9)
        elif dna.name == 'legal_eagle':
            self.scale = 7.125 / aSize
            self.handColor = VBase4(0.25, 0.25, 0.5, 1.0)
            self.generateBody()
            self.generateHead('legaleagle')
            self.setHeight(8.27)
        elif dna.name == 'big_wig':
            self.scale = 7.0 / aSize
            self.handColor = CogDNA.legalPolyColor
            self.generateBody()
            self.generateHead('bigwig')
            self.setHeight(8.69)
        elif dna.name == 'short_change':
            self.scale = 3.6 / cSize
            self.handColor = CogDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('coldcaller')
            self.setHeight(4.77)
        elif dna.name == 'penny_pincher':
            self.scale = 3.55 / aSize
            self.handColor = VBase4(1.0, 0.5, 0.6, 1.0)
            self.generateBody()
            self.generateHead('pennypincher')
            self.setHeight(5.26)
        elif dna.name == 'tightwad':
            self.scale = 4.5 / cSize
            self.handColor = CogDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('tightwad')
            self.setHeight(5.41)
        elif dna.name == 'bean_counter':
            self.scale = 4.4 / bSize
            self.handColor = CogDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('beancounter')
            self.setHeight(5.95)
        elif dna.name == 'number_cruncher':
            self.scale = 5.25 / aSize
            self.handColor = CogDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('numbercruncher')
            self.setHeight(7.22)
        elif dna.name == 'money_bags':
            self.scale = 5.3 / cSize
            self.handColor = CogDNA.moneyPolyColor
            self.generateBody()
            self.generateHead('moneybags')
            self.setHeight(6.97)
        elif dna.name == 'loan_shark':
            self.scale = 6.5 / bSize
            self.handColor = VBase4(0.5, 0.85, 0.75, 1.0)
            self.generateBody()
            self.generateHead('loanshark')
            self.setHeight(8.58)
        elif dna.name == 'robber_baron':
            self.scale = 7.0 / aSize
            self.handColor = CogDNA.moneyPolyColor
            self.generateBody()
            self.headTexture = 'robber-baron.png'
            self.generateHead('yesman')
            self.setHeight(8.95)
        elif dna.name == 'cold_caller':
            self.scale = 3.5 / cSize
            self.handColor = VBase4(0.55, 0.65, 1.0, 1.0)
            self.headColor = VBase4(0.25, 0.35, 1.0, 1.0)
            self.generateBody()
            self.generateHead('coldcaller')
            self.setHeight(4.63)
        elif dna.name == 'telemarketer':
            self.scale = 3.75 / bSize
            self.handColor = CogDNA.salesPolyColor
            self.generateBody()
            self.generateHead('telemarketer')
            self.setHeight(5.24)
        elif dna.name == 'name_dropper':
            self.scale = 4.35 / aSize
            self.handColor = CogDNA.salesPolyColor
            self.generateBody()
            self.headTexture = 'name-dropper.png'
            self.generateHead('numbercruncher')
            self.setHeight(5.98)
        elif dna.name == 'glad_hander':
            self.scale = 4.75 / cSize
            self.handColor = CogDNA.salesPolyColor
            self.generateBody()
            self.generateHead('gladhander')
            self.setHeight(6.4)
        elif dna.name == 'mover_and_shaker':
            self.scale = 4.75 / bSize
            self.handColor = CogDNA.salesPolyColor
            self.generateBody()
            self.generateHead('movershaker')
            self.setHeight(6.7)
        elif dna.name == 'two_face':
            self.scale = 5.25 / aSize
            self.handColor = CogDNA.salesPolyColor
            self.generateBody()
            self.generateHead('twoface')
            self.setHeight(6.95)
        elif dna.name == 'the_mingler':
            self.scale = 5.75 / aSize
            self.handColor = CogDNA.salesPolyColor
            self.generateBody()
            self.headTexture = 'mingler.png'
            self.generateHead('twoface')
            self.setHeight(7.61)
        elif dna.name == 'mr_hollywood':
            self.scale = 7.0 / aSize
            self.handColor = CogDNA.salesPolyColor
            self.generateBody()
            self.generateHead('yesman')
            self.setHeight(8.95)
        self.setName(CogBattleGlobals.CogAttributes[dna.name]['name'])
        self.getGeomNode().setScale(self.scale)
        self.generateHealthBar()
        self.generateCorporateMedallion()
        return

    def generateBody(self):
        animDict = self.generateAnimDict()
        filePrefix, bodyPhase = ModelDict[self.style.body]
        if ConfigVariableBool('want-new-cogs', 0).value:
            if cogExists(filePrefix + 'zero.bam'):
                self.loadModel('phase_3.5' + filePrefix + 'zero')
            else:
                self.loadModel('phase_3.5' + filePrefix + 'mod')
        else:
            self.loadModel('phase_3.5' + filePrefix + 'mod')
        self.loadAnims(animDict)
        self.setCogClothes()

    def generateAnimDict(self):
        animDict = {}
        filePrefix, bodyPhase = ModelDict[self.style.body]
        for anim in AllCogs:
            animDict[anim[0]] = 'phase_' + str(bodyPhase) + filePrefix + anim[1]

        for anim in AllCogsMinigame:
            animDict[anim[0]] = 'phase_4' + filePrefix + anim[1]

        for anim in AllCogsTutorialBattle:
            filePrefix, bodyPhase = TutorialModelDict[self.style.body]
            animDict[anim[0]] = 'phase_' + str(bodyPhase) + filePrefix + anim[1]

        for anim in AllCogsBattle:
            animDict[anim[0]] = 'phase_5' + filePrefix + anim[1]

        if not ConfigVariableBool('want-new-cogs', 0).value:
            if self.style.body == 'a':
                animDict['neutral'] = 'phase_4/models/char/suitA-neutral'
                for anim in CogsCEOBattle:
                    animDict[anim[0]] = 'phase_12/models/char/suitA-' + anim[1]

            elif self.style.body == 'b':
                animDict['neutral'] = 'phase_4/models/char/suitB-neutral'
                for anim in CogsCEOBattle:
                    animDict[anim[0]] = 'phase_12/models/char/suitB-' + anim[1]

            elif self.style.body == 'c':
                animDict['neutral'] = 'phase_3.5/models/char/suitC-neutral'
                for anim in CogsCEOBattle:
                    animDict[anim[0]] = 'phase_12/models/char/suitC-' + anim[1]

        try:
            animList = eval(self.style.name)
        except NameError:
            animList = ()

        for anim in animList:
            phase = 'phase_' + str(anim[2])
            animDict[anim[0]] = phase + filePrefix + anim[1]

        return animDict

    def initializeBodyCollisions(self, collIdStr):
        Avatar.Avatar.initializeBodyCollisions(self, collIdStr)
        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | ToontownGlobals.PieBitmask)

    def setCogClothes(self, modelRoot = None):
        if not modelRoot:
            modelRoot = self
        dept = self.style.dept
        phase = 3.5

        def __doItTheOldWay__():
            torsoTex = loader.loadTexture('phase_%s/maps/%s_blazer.png' % (phase, dept))
            torsoTex.setMinfilter(Texture.FTLinearMipmapLinear)
            torsoTex.setMagfilter(Texture.FTLinear)
            legTex = loader.loadTexture('phase_%s/maps/%s_leg.png' % (phase, dept))
            legTex.setMinfilter(Texture.FTLinearMipmapLinear)
            legTex.setMagfilter(Texture.FTLinear)
            armTex = loader.loadTexture('phase_%s/maps/%s_sleeve.png' % (phase, dept))
            armTex.setMinfilter(Texture.FTLinearMipmapLinear)
            armTex.setMagfilter(Texture.FTLinear)
            modelRoot.find('**/torso').setTexture(torsoTex, 1)
            modelRoot.find('**/arms').setTexture(armTex, 1)
            modelRoot.find('**/legs').setTexture(legTex, 1)
            modelRoot.find('**/hands').setColor(self.handColor)
            self.leftHand = self.find('**/joint_Lhold')
            self.rightHand = self.find('**/joint_Rhold')
            self.shadowJoint = self.find('**/joint_shadow')
            self.nametagJoint = self.find('**/joint_nameTag')

        if ConfigVariableBool('want-new-cogs', 0).value:
            if dept == 'c':
                texType = 'bossbot'
            elif dept == 'm':
                texType = 'cashbot'
            elif dept == 'l':
                texType = 'lawbot'
            elif dept == 's':
                texType = 'sellbot'
            if self.find('**/body').isEmpty():
                __doItTheOldWay__()
            else:
                filepath = 'phase_3.5/maps/tt_t_ene_' + texType + '.png'
                if cogExists('/maps/tt_t_ene_' + texType + '.png'):
                    bodyTex = loader.loadTexture(filepath)
                    self.find('**/body').setTexture(bodyTex, 1)
                self.leftHand = self.find('**/def_joint_left_hold')
                self.rightHand = self.find('**/def_joint_right_hold')
                self.shadowJoint = self.find('**/def_shadow')
                self.nametagJoint = self.find('**/def_nameTag')
        else:
            __doItTheOldWay__()

    def makeWaiter(self, modelRoot = None):
        if not modelRoot:
            modelRoot = self
        self.isWaiter = 1
        torsoTex = loader.loadTexture('phase_3.5/maps/waiter_m_blazer.png')
        torsoTex.setMinfilter(Texture.FTLinearMipmapLinear)
        torsoTex.setMagfilter(Texture.FTLinear)
        legTex = loader.loadTexture('phase_3.5/maps/waiter_m_leg.png')
        legTex.setMinfilter(Texture.FTLinearMipmapLinear)
        legTex.setMagfilter(Texture.FTLinear)
        armTex = loader.loadTexture('phase_3.5/maps/waiter_m_sleeve.png')
        armTex.setMinfilter(Texture.FTLinearMipmapLinear)
        armTex.setMagfilter(Texture.FTLinear)
        modelRoot.find('**/torso').setTexture(torsoTex, 1)
        modelRoot.find('**/arms').setTexture(armTex, 1)
        modelRoot.find('**/legs').setTexture(legTex, 1)

    def makeRentalCog(self, cogType, modelRoot = None):
        if not modelRoot:
            modelRoot = self.getGeomNode()
        if cogType == 's':
            torsoTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_blazer.png')
            legTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_leg.png')
            armTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_sleeve.png')
            handTex = loader.loadTexture('phase_3.5/maps/tt_t_ene_sellbotRental_hand.png')
        else:
            self.notify.warning('No rental cog for cog type %s' % cogType)
            return
        self.isRental = 1
        modelRoot.find('**/torso').setTexture(torsoTex, 1)
        modelRoot.find('**/arms').setTexture(armTex, 1)
        modelRoot.find('**/legs').setTexture(legTex, 1)
        modelRoot.find('**/hands').setTexture(handTex, 1)

    def generateHead(self, headType):
        if ConfigVariableBool('want-new-cogs', 0).value:
            filePrefix, phase = HeadModelDict[self.style.body]
        else:
            filePrefix, phase = ModelDict[self.style.body]
        headModel = loader.loadModel('phase_' + str(phase) + filePrefix + 'heads')
        headReferences = headModel.findAllMatches('**/' + headType)
        for i in range(0, headReferences.getNumPaths()):
            if ConfigVariableBool('want-new-cogs', 0).value:
                headPart = self.instance(headReferences.getPath(i), 'modelRoot', 'to_head')
                if not headPart:
                    headPart = self.instance(headReferences.getPath(i), 'modelRoot', 'joint_head')
            else:
                headPart = self.instance(headReferences.getPath(i), 'modelRoot', 'joint_head')
            if self.headTexture:
                headTex = loader.loadTexture('phase_' + str(phase) + '/maps/' + self.headTexture)
                headTex.setMinfilter(Texture.FTLinearMipmapLinear)
                headTex.setMagfilter(Texture.FTLinear)
                headPart.setTexture(headTex, 1)
            if self.headColor:
                headPart.setColor(self.headColor)
            self.headParts.append(headPart)

        headModel.removeNode()

    def generateCorporateTie(self, modelPath = None):
        if not modelPath:
            modelPath = self
        dept = self.style.dept
        tie = modelPath.find('**/tie')
        if tie.isEmpty():
            self.notify.warning('skelecog has no tie model!!!')
            return
        if dept == 'c':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_boss.png')
        elif dept == 's':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_sales.png')
        elif dept == 'l':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_legal.png')
        elif dept == 'm':
            tieTex = loader.loadTexture('phase_5/maps/cog_robot_tie_money.png')
        tieTex.setMinfilter(Texture.FTLinearMipmapLinear)
        tieTex.setMagfilter(Texture.FTLinear)
        tie.setTexture(tieTex, 1)

    def generateCorporateMedallion(self):
        icons = loader.loadModel('phase_3/models/gui/cog_icons')
        dept = self.style.dept
        if ConfigVariableBool('want-new-cogs', 0).value:
            chestNull = self.find('**/def_joint_attachMeter')
            if chestNull.isEmpty():
                chestNull = self.find('**/joint_attachMeter')
        else:
            chestNull = self.find('**/joint_attachMeter')
        if dept == 'c':
            self.corpMedallion = icons.find('**/CorpIcon').copyTo(chestNull)
        elif dept == 's':
            self.corpMedallion = icons.find('**/SalesIcon').copyTo(chestNull)
        elif dept == 'l':
            self.corpMedallion = icons.find('**/LegalIcon').copyTo(chestNull)
        elif dept == 'm':
            self.corpMedallion = icons.find('**/MoneyIcon').copyTo(chestNull)
        self.corpMedallion.setPosHprScale(0.02, 0.05, 0.04, 180.0, 0.0, 0.0, 0.51, 0.51, 0.51)
        self.corpMedallion.setColor(self.medallionColors[dept])
        icons.removeNode()

    def generateHealthBar(self):
        self.removeHealthBar()
        model = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        button = model.find('**/minnieCircle')
        button.setScale(3.0)
        button.setH(180.0)
        button.setColor(self.healthColors[0])
        if ConfigVariableBool('want-new-cogs', 0).value:
            chestNull = self.find('**/def_joint_attachMeter')
            if chestNull.isEmpty():
                chestNull = self.find('**/joint_attachMeter')
        else:
            chestNull = self.find('**/joint_attachMeter')
        button.reparentTo(chestNull)
        self.healthBar = button
        glow = BattleProps.globalPropPool.getProp('glow')
        glow.reparentTo(self.healthBar)
        glow.setScale(0.28)
        glow.setPos(-0.005, 0.01, 0.015)
        glow.setColor(self.healthGlowColors[0])
        button.flattenLight()
        self.healthBarGlow = glow
        self.healthBar.hide()
        self.healthCondition = 0

    def reseatHealthBarForSkele(self):
        self.healthBar.setPos(0.0, 0.1, 0.0)

    def updateHealthBar(self, hp, forceUpdate = 0):
        if hp > self.currHP:
            hp = self.currHP
        self.currHP -= hp
        health = float(self.currHP) / float(self.maxHP)
        if health > 0.95:
            condition = 0
        elif health > 0.7:
            condition = 1
        elif health > 0.3:
            condition = 2
        elif health > 0.05:
            condition = 3
        elif health > 0.0:
            condition = 4
        else:
            condition = 5
        if self.healthCondition != condition or forceUpdate:
            if condition == 4:
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.75), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.uniqueName('blink-task'))
            elif condition == 5:
                if self.healthCondition == 4:
                    taskMgr.remove(self.uniqueName('blink-task'))
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.25), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.uniqueName('blink-task'))
            else:
                self.healthBar.setColor(self.healthColors[condition], 1)
                self.healthBarGlow.setColor(self.healthGlowColors[condition], 1)
            self.healthCondition = condition

    def __blinkRed(self, task):
        self.healthBar.setColor(self.healthColors[3], 1)
        self.healthBarGlow.setColor(self.healthGlowColors[3], 1)
        if self.healthCondition == 5:
            self.healthBar.setScale(1.17)
        return Task.done

    def __blinkGray(self, task):
        if not self.healthBar:
            return
        self.healthBar.setColor(self.healthColors[4], 1)
        self.healthBarGlow.setColor(self.healthGlowColors[4], 1)
        if self.healthCondition == 5:
            self.healthBar.setScale(1.0)
        return Task.done

    def removeHealthBar(self):
        if self.healthBar:
            self.healthBar.removeNode()
            self.healthBar = None
        if self.healthCondition == 4 or self.healthCondition == 5:
            taskMgr.remove(self.uniqueName('blink-task'))
        self.healthCondition = 0
        return

    def getLoseActor(self):
        if ConfigVariableBool('want-new-cogs', 0).value:
            if self.find('**/body'):
                return self
        if self.loseActor == None:
            if not self.isSkeleton:
                filePrefix, phase = TutorialModelDict[self.style.body]
                loseModel = 'phase_' + str(phase) + filePrefix + 'lose-mod'
                loseAnim = 'phase_' + str(phase) + filePrefix + 'lose'
                self.loseActor = Actor.Actor(loseModel, {'lose': loseAnim})
                loseNeck = self.loseActor.find('**/joint_head')
                for part in self.headParts:
                    part.instanceTo(loseNeck)

                if self.isWaiter:
                    self.makeWaiter(self.loseActor)
                else:
                    self.setCogClothes(self.loseActor)
            else:
                loseModel = 'phase_5/models/char/cog' + self.style.body.upper() + '_robot-lose-mod'
                filePrefix, phase = TutorialModelDict[self.style.body]
                loseAnim = 'phase_' + str(phase) + filePrefix + 'lose'
                self.loseActor = Actor.Actor(loseModel, {'lose': loseAnim})
                self.generateCorporateTie(self.loseActor)
        self.loseActor.setScale(self.scale)
        self.loseActor.setPos(self.getPos())
        self.loseActor.setHpr(self.getHpr())
        shadowJoint = self.loseActor.find('**/joint_shadow')
        dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
        dropShadow.setScale(0.45)
        dropShadow.setColor(0.0, 0.0, 0.0, 0.5)
        dropShadow.reparentTo(shadowJoint)
        return self.loseActor

    def cleanupLoseActor(self):
        self.notify.debug('cleanupLoseActor()')
        if self.loseActor != None:
            self.notify.debug('cleanupLoseActor() - got one')
            self.loseActor.cleanup()
        self.loseActor = None
        return

    def makeSkeleton(self):
        model = 'phase_5/models/char/cog' + self.style.body.upper() + '_robot-zero'
        anims = self.generateAnimDict()
        anim = self.getCurrentAnim()
        dropShadow = self.dropShadow
        if not dropShadow.isEmpty():
            dropShadow.reparentTo(hidden)
        self.removePart('modelRoot')
        self.loadModel(model)
        self.loadAnims(anims)
        self.getGeomNode().setScale(self.scale * 1.0173)
        self.generateHealthBar()
        self.generateCorporateMedallion()
        self.generateCorporateTie()
        self.setHeight(self.height)
        parts = self.findAllMatches('**/pPlane*')
        for partNum in range(0, parts.getNumPaths()):
            bb = parts.getPath(partNum)
            bb.setTwoSided(1)

        self.setName(TTLocalizer.Skeleton)
        nameInfo = TTLocalizer.CogBaseNameWithLevel % {'name': self._name,
         'dept': self.getStyleDept(),
         'level': self.getActualLevel()}
        self.setDisplayName(nameInfo)
        self.leftHand = self.find('**/joint_Lhold')
        self.rightHand = self.find('**/joint_Rhold')
        self.shadowJoint = self.find('**/joint_shadow')
        self.nametagNull = self.find('**/joint_nameTag')
        if not dropShadow.isEmpty():
            dropShadow.setScale(0.75)
            if not self.shadowJoint.isEmpty():
                dropShadow.reparentTo(self.shadowJoint)
        self.loop(anim)
        self.isSkeleton = 1

    def getHeadParts(self):
        return self.headParts

    def getRightHand(self):
        return self.rightHand

    def getLeftHand(self):
        return self.leftHand

    def getShadowJoint(self):
        return self.shadowJoint

    def getNametagJoints(self):
        return []

    def getDialogueArray(self):
        if self.isSkeleton:
            loadSkelDialog()
            return SkelCogDialogArray
        else:
            return CogDialogArray
