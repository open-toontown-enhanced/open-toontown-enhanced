from . import Street

class BRStreet(Street.Street):

    def enter(self, requestStatus: dict):
        self.loader.hood.startSnowAndWind()
        Street.Street.enter(self, requestStatus)

    def exit(self):
        Street.Street.exit(self)
        self.loader.hood.stopSnowAndWind()