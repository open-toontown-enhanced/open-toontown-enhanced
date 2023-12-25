from panda3d.core import *
from direct.gui.DirectGui import *
from . import CogDNA
from toontown.toonbase import TTLocalizer
from otp.avatar import AvatarPanel
from toontown.friends import FriendsListPanel

class CogAvatarPanel(AvatarPanel.AvatarPanel):
    currentAvatarPanel = None

    def __init__(self, avatar):
        AvatarPanel.AvatarPanel.__init__(self, avatar, FriendsListPanel=FriendsListPanel)
        self.avName = avatar.getName()
        gui = loader.loadModel('phase_3.5/models/gui/suit_detail_panel')
        self.frame = DirectFrame(
                parent = base.a2dTopRight,
                relief = None,
                pos = (-.23125, 0, -.46125),
                geom = gui.find('**/avatar_panel'),
                geom_scale = 0.21,
                geom_pos = (0, 0, 0.02)
        )
        disabledImageColor = Vec4(1, 1, 1, 0.4)
        text0Color = Vec4(1, 1, 1, 1)
        text1Color = Vec4(0.5, 1, 0.5, 1)
        text2Color = Vec4(1, 1, 0.5, 1)
        text3Color = Vec4(1, 1, 1, 0.2)
        self.head = self.frame.attachNewNode('head')
        for part in avatar.headParts:
            copyPart = part.copyTo(self.head)
            copyPart.setDepthTest(1)
            copyPart.setDepthWrite(1)

        p1 = Point3()
        p2 = Point3()
        self.head.calcTightBounds(p1, p2)
        d = p2 - p1
        biggest = max(d[0], d[1], d[2])
        s = 0.3 / biggest
        self.head.setPosHprScale(0, 0, 0, 180, 0, 0, s, s, s)
        self.nameLabel = DirectLabel(
                parent = self.frame,
                relief = None,
                pos = (0.0125, 0, 0.36),
                text = self.avName,
                text_font = avatar.getFont(),
                text_fg = Vec4(0, 0, 0, 1),
                text_pos = (0, 0),
                text_scale = 0.047,
                text_wordwrap = 7.5,
                text_shadow = (1, 1, 1, 1)
        )
        level = avatar.getActualLevel()
        dept = CogDNA.getCogDeptFullname(avatar.dna.name)
        self.levelLabel = DirectLabel(
                parent = self.frame,
                relief = None,
                pos = (0, 0, -0.1),
                text = TTLocalizer.AvatarPanelCogLevel % level,
                text_font = avatar.getFont(),
                text_align = TextNode.ACenter,
                text_fg = Vec4(0, 0, 0, 1),
                text_pos = (0, 0),
                text_scale = 0.05,
                text_wordwrap = 8.0
        )
        corpIcon = avatar.corpMedallion.copyTo(hidden)
        corpIcon.setPosHprScale(0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.corpIcon = DirectLabel(
                parent = self.frame,
                relief = None,
                geom = corpIcon,
                geom_scale = 0.13,
                pos = (0, 0, -0.175)
        )
        corpIcon.removeNode()
        self.deptLabel = DirectLabel(
                parent = self.frame,
                relief = None,
                pos = (0, 0, -0.28),
                text = dept,
                text_font = avatar.getFont(),
                text_align = TextNode.ACenter,
                text_fg = Vec4(0, 0, 0, 1),
                text_pos = (0, 0),
                text_scale = 0.05,
                text_wordwrap = 8.0
        )
        self.closeButton = DirectButton(
                parent = self.frame,
                relief = None,
                pos = (0.0, 0, -0.36),
                text = TTLocalizer.AvatarPanelCogDetailClose,
                text_font = avatar.getFont(),
                text0_fg = Vec4(0, 0, 0, 1),
                text1_fg = Vec4(0.5, 0, 0, 1),
                text2_fg = Vec4(1, 0, 0, 1),
                text_pos = (0, 0),
                text_scale = 0.05,
                command = self.__handleClose
        )
        gui.removeNode()
        base.localAvatar.obscureFriendsListButton(1)
        self.frame.show()
        messenger.send('avPanelDone')

    def cleanup(self):
        if self.frame == None:
            return
        self.frame.destroy()
        del self.frame
        self.frame = None
        self.head.removeNode()
        del self.head
        base.localAvatar.obscureFriendsListButton(-1)
        AvatarPanel.AvatarPanel.cleanup(self)

    def __handleClose(self):
        self.cleanup()
        AvatarPanel.currentAvatarPanel = None
