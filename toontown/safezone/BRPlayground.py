from . import Playground

class BRPlayground(Playground.Playground):

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Pluto))

    def enter(self, requestStatus: dict):
        self.loader.hood.startSnowAndWind()
        Playground.Playground.enter(self, requestStatus)

    def exit(self):
        Playground.Playground.exit(self)
        self.loader.hood.stopSnowAndWind()