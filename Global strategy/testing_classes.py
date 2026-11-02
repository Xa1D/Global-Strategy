from combat import Combat
from pprint import pformat

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

class DeterministicCombat(Combat):
    def __init__(self, attacker, defender, attacker_damage, defender_damage):
        super().__init__(attacker, defender)
        self.damages = [attacker_damage, defender_damage]
        self.count = 0

    def get_damage(self, unit_type, count):   
        damage = self.damages[self.count % 2] #simulate_round asks for the attacker's damage first, then the defender's
        self.count += 1
        return damage

def check(name, objective, expected, observed):
    print(f"\n{name} [{objective}]")
    print(f"Expected: {pformat(expected, width=70, sort_dicts=False)}")
    print(f"Observed: {pformat(observed, width=70, sort_dicts=False)}")
    print("PASS" if expected == observed else "FAIL")