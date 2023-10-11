from toontown.building.CogPlannerInteriorAI import CogPlannerInteriorAI

class CogPlannerCogdoInteriorAI(CogPlannerInteriorAI):

    def __init__(self, cogdoLayout, bldgLevel, bldgTrack, zone):
        self._cogdoLayout = cogdoLayout
        CogPlannerInteriorAI.__init__(self, self._cogdoLayout.getNumGameFloors(), bldgLevel, bldgTrack, zone, respectInvasions = 0)

    def _genCogInfos(self, numFloors, bldgLevel, bldgTrack):
        CogPlannerInteriorAI._genCogInfos(self, self._cogdoLayout.getNumFloors(), bldgLevel, bldgTrack)
