class TestTerritory:
    def __init__(self, name="T", infantry=0, tank=0, artillery=0):
        self.name = name
        self.units = {"infantry": infantry, "tank": tank, "artillery": artillery}
        self.adjacent = []
        self.owner = None
        self.combat = False
        self.attack_cooldown = 0

    def total_units(self):
        return sum(self.units.values())

    def unit_value(self, weights):
        return sum(self.units[unit] * weights[unit] for unit in self.units)

class TestMap:
    def __init__(self, territories):
        self.territories = {territory.name: territory for territory in territories}

