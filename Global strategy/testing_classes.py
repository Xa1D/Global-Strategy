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

class ScoreRecorder: #bypasses AIScoring.choose_state and returns the state scores from evaluate_state
    def __init__(self):
        self.scores = {}

    def choose_state(self, state_scores):
        self.scores = dict(state_scores)
        return "idle"

def test(file, name, objective, expected, observed):  
    file.write(f"\n{name} [{objective}]\n")
    file.write(f"Expected: {pformat(expected, width=80, sort_dicts=False)}\n")
    file.write(f"Observed: {pformat(observed, width=80, sort_dicts=False)}\n")
    file.write("PASS\n" if expected == observed else "FAIL\n")