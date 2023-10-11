

class BattleExperienceAggregatorAI:

    def __init__(self):
        self.cogsKilled = []
        self.cogsKilledPerFloor = []
        self.toonSkillPtsGained = {}
        self.toonExp = {}
        self.toonOrigQuests = {}
        self.toonItems = {}
        self.toonOrigMerits = {}
        self.toonMerits = {}
        self.toonParts = {}
        self.helpfulToons = []

    def attachToBattle(self, battle):
        battle.cogsKilled = self.cogsKilled
        battle.cogsKilledPerFloor = self.cogsKilledPerFloor
        battle.battleCalc.toonSkillPtsGained = self.toonSkillPtsGained
        battle.toonExp = self.toonExp
        battle.toonOrigQuests = self.toonOrigQuests
        battle.toonItems = self.toonItems
        battle.toonOrigMerits = self.toonOrigMerits
        battle.toonMerits = self.toonMerits
        battle.toonParts = self.toonParts
        battle.helpfulToons = self.helpfulToons
