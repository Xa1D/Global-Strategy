import json
data = json.load(open("africa_coords.json"))
print([n for n in data.keys() if "nea" in n or "adagascar" in n])

import ai_scoring

matrix = ai_scoring.new_transition_matrix()
print("Initial row for 'attacking':", matrix["attacking"])
# should show all 5s: {'attacking': 5, 'expanding': 5, 'defending': 5, 'reinforcing': 5, 'idle': 5}

ai_scoring.record_transition(matrix, "attacking", "defending")
ai_scoring.record_transition(matrix, "attacking", "defending")
ai_scoring.record_transition(matrix, "attacking", "attacking")

print("After 3 transitions:", matrix["attacking"])
# should show: {'attacking': 6, 'expanding': 5, 'defending': 7, 'reinforcing': 5, 'idle': 5}

prediction = ai_scoring.predict_next_state(matrix, "attacking")
print("Predicted next state from 'attacking':", prediction)
# defending should now have noticeably higher probability than the others


"""
Combat balance test script.
 
Runs many independent trials of fixed unit-count matchups through the
real Combat class (same code the game uses) and reports win rates and
average units lost. No pygame needed - drop this file in the same
folder as combat.py and run it directly.
 
Usage:
    python combat_balance_test.py
"""
 
from combat import Combat
 
 
class FakeCountry:
    """Minimal stand-in for Country - Combat only ever touches .units."""
    def __init__(self, infantry=0, tank=0, artillery=0):
        self.units = {"infantry": infantry, "tank": tank, "artillery": artillery}
 
    def total_units(self):
        return sum(self.units.values())
 
 
def run_trial(attacker_units, defender_units):
    """
    attacker_units / defender_units: dicts like {"infantry": 100}
    Returns (winner, attacker_units_lost, defender_units_lost)
    """
    attacker = FakeCountry(**attacker_units)
    defender = FakeCountry(**defender_units)
    attacker_before = attacker.total_units()
    defender_before = defender.total_units()
 
    battle = Combat(attacker, defender)
    result = battle.simulate_combat()
 
    attacker_after = attacker.total_units()
    defender_after = defender.total_units()
    return result, attacker_before - attacker_after, defender_before - defender_after
 
 
def run_matchup(name, attacker_units, defender_units, trials=500):
    attacker_wins = 0
    defender_wins = 0
    total_attacker_lost = 0
    total_defender_lost = 0
 
    for _ in range(trials):
        result, atk_lost, def_lost = run_trial(attacker_units, defender_units)
        if result == "attacker":
            attacker_wins += 1
        else:
            defender_wins += 1
        total_attacker_lost += atk_lost
        total_defender_lost += def_lost
 
    attacker_win_rate = attacker_wins / trials * 100
    defender_win_rate = defender_wins / trials * 100
    avg_attacker_lost = total_attacker_lost / trials
    avg_defender_lost = total_defender_lost / trials
 
    print(f"\n=== {name} ===")
    print(f"Attacker: {attacker_units}")
    print(f"Defender: {defender_units}")
    print(f"Trials: {trials}")
    print(f"Attacker win rate: {attacker_win_rate:.1f}%")
    print(f"Defender win rate: {defender_win_rate:.1f}%")
    print(f"Avg units lost - attacker: {avg_attacker_lost:.1f}, defender: {avg_defender_lost:.1f}")
 
 

TRIALS = 1

run_matchup(
    "100 Infantry vs 100 Infantry",
    {"infantry": 100},
    {"infantry": 100},
    trials=TRIALS,
)

run_matchup(
    "50 Tanks vs 100 Infantry",
    {"tank": 50},
    {"infantry": 100},
    trials=TRIALS,
)

run_matchup(
    "25 Artillery vs 100 Infantry",
    {"artillery": 25},
    {"infantry": 100},
    trials=TRIALS,
)

# A few extra matchups worth checking while you're at it -
# remove any of these if you only want the three specified above
run_matchup(
    "Mixed 40 Infantry / 20 Tank / 10 Artillery vs 100 Infantry",
    {"infantry": 40, "tank": 20, "artillery": 10},
    {"infantry": 100},
    trials=TRIALS,
)

run_matchup(
    "Equal cost: 100 Infantry (500g) vs ~33 Tank (495g)",
    {"infantry": 100},
    {"tank": 33},
    trials=TRIALS,
)

run_matchup(
    "Equal cost: 100 Infantry (500g) vs 25 Artillery (500g)",
    {"infantry": 100},
    {"artillery": 25},
    trials=TRIALS,
)