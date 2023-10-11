import random
from panda3d.core import *
from direct.directnotify.DirectNotifyGlobal import *
from toontown.toonbase import TTLocalizer
import random
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from otp.avatar import AvatarDNA
notify = directNotify.newCategory('CogDNA')
cogHeadTypes = ['flunky',
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
cogATypes = ['yesman',
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
cogBTypes = ['pencil_pusher',
 'downsizer',
 'bloodsucker',
 'ambulance_chaser',
 'spin_doctor',
 'bean_counter',
 'loan_shark',
 'telemarketer',
 'mover_and_shaker']
cogCTypes = ['flunky',
 'micromanager',
 'corporate_raider',
 'bottom_feeder',
 'short_change',
 'tightwad',
 'money_bags',
 'cold_caller',
 'glad_hander']
cogDepts = ['c',
 'l',
 'm',
 's']
cogDeptFullnames = {'c': TTLocalizer.Bossbot,
 'l': TTLocalizer.Lawbot,
 'm': TTLocalizer.Cashbot,
 's': TTLocalizer.Sellbot}
cogDeptFullnamesP = {'c': TTLocalizer.BossbotP,
 'l': TTLocalizer.LawbotP,
 'm': TTLocalizer.CashbotP,
 's': TTLocalizer.SellbotP}
corpPolyColor = VBase4(0.95, 0.75, 0.75, 1.0)
legalPolyColor = VBase4(0.75, 0.75, 0.95, 1.0)
moneyPolyColor = VBase4(0.65, 0.95, 0.85, 1.0)
salesPolyColor = VBase4(0.95, 0.75, 0.95, 1.0)
cogsPerLevel = [1,
 1,
 1,
 1,
 1,
 1,
 1,
 1]
cogsPerDept = 8
goonTypes = ['pg', 'sg']

def getCogBodyType(name):
    if name in cogATypes:
        return 'a'
    elif name in cogBTypes:
        return 'b'
    elif name in cogCTypes:
        return 'c'
    else:
        print('Unknown body type for cog name: ', name)


def getCogDept(name):
    index = cogHeadTypes.index(name)
    if index < cogsPerDept:
        return cogDepts[0]
    elif index < cogsPerDept * 2:
        return cogDepts[1]
    elif index < cogsPerDept * 3:
        return cogDepts[2]
    elif index < cogsPerDept * 4:
        return cogDepts[3]
    else:
        print('Unknown dept for cog name: ', name)
        return None
    return None


def getDeptFullname(dept):
    return cogDeptFullnames[dept]


def getDeptFullnameP(dept):
    return cogDeptFullnamesP[dept]


def getCogDeptFullname(name):
    return cogDeptFullnames[getCogDept(name)]


def getCogType(name):
    index = cogHeadTypes.index(name)
    return index % cogsPerDept + 1


def getRandomCogType(level, rng = random):
    return random.randint(max(level - 4, 1), min(level, 8))


def getRandomCogByDept(dept):
    deptNumber = cogDepts.index(dept)
    return cogHeadTypes[cogsPerDept * deptNumber + random.randint(0, 7)]


class CogDNA(AvatarDNA.AvatarDNA):

    def __init__(self, str = None, type = None, dna = None, r = None, b = None, g = None):
        if str != None:
            self.makeFromNetString(str)
        elif type != None:
            if type == 's':
                self.newCog()
        else:
            self.type = 'u'
        return

    def __str__(self):
        if self.type == 's':
            return 'type = %s\nbody = %s, dept = %s, name = %s' % ('cog',
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
            self.body = getCogBodyType(self.name)
        elif self.type == 'b':
            self.dept = dgi.getFixedString(1)
        else:
            notify.error('unknown avatar type: ', self.type)
        return None

    def __defaultGoon(self):
        self.type = 'g'
        self.name = goonTypes[0]

    def __defaultCog(self):
        self.type = 's'
        self.name = 'downsizer'
        self.dept = getCogDept(self.name)
        self.body = getCogBodyType(self.name)

    def newCog(self, name = None):
        if name == None:
            self.__defaultCog()
        else:
            self.type = 's'
            self.name = name
            self.dept = getCogDept(self.name)
            self.body = getCogBodyType(self.name)
        return

    def newBossCog(self, dept):
        self.type = 'b'
        self.dept = dept

    def newCogRandom(self, level = None, dept = None):
        self.type = 's'
        if level == None:
            level = random.choice(list(range(1, len(cogsPerLevel))))
        elif level < 0 or level > len(cogsPerLevel):
            notify.error('Invalid cog level: %d' % level)
        if dept == None:
            dept = random.choice(cogDepts)
        self.dept = dept
        index = cogDepts.index(dept)
        base = index * cogsPerDept
        offset = 0
        if level > 1:
            for i in range(1, level):
                offset = offset + cogsPerLevel[i - 1]

        bottom = base + offset
        top = bottom + cogsPerLevel[level - 1]
        self.name = cogHeadTypes[random.choice(list(range(bottom, top)))]
        self.body = getCogBodyType(self.name)
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
            type = 'cog'
        elif self.type == 'b':
            type = 'boss'
        else:
            notify.error('Invalid DNA type: ', self.type)
        return type
