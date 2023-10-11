from direct.directnotify import DirectNotifyGlobal


class CogPageManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('CogPageManagerAI')

    def __init__(self, air):
        self.air = air

    def toonKilledCogs(self, toon, cogsKilled, zoneId):
        pass  # TODO

    def toonEncounteredCogs(self, toon, cogsEncountered, zoneId):
        pass  # TODO
