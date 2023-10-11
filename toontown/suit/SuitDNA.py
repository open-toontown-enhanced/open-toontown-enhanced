import random
from panda3d.core import *
from direct.directnotify.DirectNotifyGlobal import *
from toontown.toonbase import TTLocalizer
import random
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from otp.avatar import AvatarDNA
notify = directNotify.newCategory('SuitDNA')
suitHeadTypes = ['flunky',
 'pencil_pusher',
 'yesman',
 'micromanager',
 'downsizer',
 'head_hunter',
 'corporate_raider',
 'the_big_cheese',
 'bottom_feeder',
 'bloodsucker',
 'double_talker',
 'ambulance_chaser',
 'back_stabber',
 'spin_doctor',
 'legal_eagle',
 'big_wig',
 'short_change',
 'penny_pincher',
 'tightwad',
 'bean_counter',
 'number_cruncher',
 'money_bags',
 'loan_shark',
 'robber_baron',
 'cold_caller',
 'telemarketer',
 'name_dropper',
 'glad_hander',
 'mover_and_shaker',
 'two_face',
 'the_mingler',
 'mr_hollywood']
suitATypes = ['yesman',
 'head_hunter',
 'the_big_cheese',
 'double_talker',
 'back_stabber',
 'legal_eagle',
 'big_wig',
 'penny_pincher',
 'number_cruncher',
 'robber_baron',
 'name_dropper',
 'two_face',
 'the_mingler',
 'mr_hollywood']
suitBTypes = ['pencil_pusher',
 'downsizer',
 'bloodsucker',
 'ambulance_chaser',
 'spin_doctor',
 'bean_counter',
 'loan_shark',
 'telemarketer',
 'mover_and_shaker']
suitCTypes = ['flunky',
 'micromanager',
 'corporate_raider',
 'bottom_feeder',
 'short_change',
 'tightwad',
 'money_bags',
 'cold_caller',
 'glad_hander']
suitDepts = ['c',
 'l',
 'm',
 's']
suitDeptFullnames = {'c': TTLocalizer.Bossbot,
 'l': TTLocalizer.Lawbot,
 'm': TTLocalizer.Cashbot,
 's': TTLocalizer.Sellbot}
suitDeptFullnamesP = {'c': TTLocalizer.BossbotP,
 'l': TTLocalizer.LawbotP,
 'm': TTLocalizer.CashbotP,
 's': TTLocalizer.SellbotP}
corpPolyColor = VBase4(0.95, 0.75, 0.75, 1.0)
legalPolyColor = VBase4(0.75, 0.75, 0.95, 1.0)
moneyPolyColor = VBase4(0.65, 0.95, 0.85, 1.0)
salesPolyColor = VBase4(0.95, 0.75, 0.95, 1.0)
suitsPerLevel = [1,
 1,
 1,
 1,
 1,
 1,
 1,
 1]
suitsPerDept = 8
goonTypes = ['pg', 'sg']

def getSuitBodyType(name):
    if name in suitATypes:
        return 'a'
    elif name in suitBTypes:
        return 'b'
    elif name in suitCTypes:
        return 'c'
    else:
        print('Unknown body type for suit name: ', name)


def getSuitDept(name):
    index = suitHeadTypes.index(name)
    if index < suitsPerDept:
        return suitDepts[0]
    elif index < suitsPerDept * 2:
        return suitDepts[1]
    elif index < suitsPerDept * 3:
        return suitDepts[2]
    elif index < suitsPerDept * 4:
        return suitDepts[3]
    else:
        print('Unknown dept for suit name: ', name)
        return None
    return None


def getDeptFullname(dept):
    return suitDeptFullnames[dept]


def getDeptFullnameP(dept):
    return suitDeptFullnamesP[dept]


def getSuitDeptFullname(name):
    return suitDeptFullnames[getSuitDept(name)]


def getSuitType(name):
    index = suitHeadTypes.index(name)
    return index % suitsPerDept + 1


def getRandomSuitType(level, rng = random):
    return random.randint(max(level - 4, 1), min(level, 8))


def getRandomSuitByDept(dept):
    deptNumber = suitDepts.index(dept)
    return suitHeadTypes[suitsPerDept * deptNumber + random.randint(0, 7)]


class SuitDNA(AvatarDNA.AvatarDNA):

    def __init__(self, str = None, type = None, dna = None, r = None, b = None, g = None):
        if str != None:
            self.makeFromNetString(str)
        elif type != None:
            if type == 's':
                self.newSuit()
        else:
            self.type = 'u'
        return

    def __str__(self):
        if self.type == 's':
            return 'type = %s\nbody = %s, dept = %s, name = %s' % ('suit',
             self.body,
             self.dept,
             self.name)
        elif self.type == 'b':
            return 'type = boss cog\ndept = %s' % self.dept
        else:
            return 'type undefined'

    def makeNetString(self):
        dg = PyDatagram()
        dg.addFixedString(self.type, 1)
        if self.type == 's':
            dg.addString(self.name)
            dg.addFixedString(self.dept, 1)
        elif self.type == 'b':
            dg.addFixedString(self.dept, 1)
        elif self.type == 'u':
            notify.error('undefined avatar')
        else:
            notify.error('unknown avatar type: ', self.type)
        return dg.getMessage()

    def makeFromNetString(self, string):
        dg = PyDatagram(string)
        dgi = PyDatagramIterator(dg)
        self.type = dgi.getFixedString(1)
        if self.type == 's':
            self.name = dgi.getString()
            self.dept = dgi.getFixedString(1)
            self.body = getSuitBodyType(self.name)
        elif self.type == 'b':
            self.dept = dgi.getFixedString(1)
        else:
            notify.error('unknown avatar type: ', self.type)
        return None

    def __defaultGoon(self):
        self.type = 'g'
        self.name = goonTypes[0]

    def __defaultSuit(self):
        self.type = 's'
        self.name = 'downsizer'
        self.dept = getSuitDept(self.name)
        self.body = getSuitBodyType(self.name)

    def newSuit(self, name = None):
        if name == None:
            self.__defaultSuit()
        else:
            self.type = 's'
            self.name = name
            self.dept = getSuitDept(self.name)
            self.body = getSuitBodyType(self.name)
        return

    def newBossCog(self, dept):
        self.type = 'b'
        self.dept = dept

    def newSuitRandom(self, level = None, dept = None):
        self.type = 's'
        if level == None:
            level = random.choice(list(range(1, len(suitsPerLevel))))
        elif level < 0 or level > len(suitsPerLevel):
            notify.error('Invalid suit level: %d' % level)
        if dept == None:
            dept = random.choice(suitDepts)
        self.dept = dept
        index = suitDepts.index(dept)
        base = index * suitsPerDept
        offset = 0
        if level > 1:
            for i in range(1, level):
                offset = offset + suitsPerLevel[i - 1]

        bottom = base + offset
        top = bottom + suitsPerLevel[level - 1]
        self.name = suitHeadTypes[random.choice(list(range(bottom, top)))]
        self.body = getSuitBodyType(self.name)
        return

    def newGoon(self, name = None):
        if type == None:
            self.__defaultGoon()
        else:
            self.type = 'g'
            if name in goonTypes:
                self.name = name
            else:
                notify.error('unknown goon type: ', name)
        return

    def getType(self):
        if self.type == 's':
            type = 'suit'
        elif self.type == 'b':
            type = 'boss'
        else:
            notify.error('Invalid DNA type: ', self.type)
        return type
