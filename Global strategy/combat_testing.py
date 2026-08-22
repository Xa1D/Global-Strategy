from combat import Combat

class FakeCountry:
    def __init__(self, infantry=0, tank=0, artillery=0):
        self.units = {"infantry": infantry, "tank": tank, "artillery": artillery}

    def total_units(self):
        return sum(self.units.values())


def run_trial(attacker_units, defender_units):
    attacker = FakeCountry(**attacker_units)
    defender = FakeCountry(**defender_units)
    attacker_before = attacker.total_units()
    defender_before = defender.total_units()

    battle = Combat(attacker, defender)
    result = battle.simulate_combat()

    attacker_after = attacker.total_units()
    defender_after = defender.total_units()
    rounds_taken = len(battle.combat_log)
    return result, attacker_before - attacker_after, defender_before - defender_after, rounds_taken


def run_matchup(name, attacker_units, defender_units, trials=200):
    attacker_wins = 0
    defender_wins = 0
    total_attacker_lost = 0
    total_defender_lost = 0
    total_rounds = 0

    for _ in range(trials):
        result, atk_lost, def_lost, rounds = run_trial(attacker_units, defender_units)
        if result == "attacker":
            attacker_wins += 1
        else:
            defender_wins += 1
        total_attacker_lost += atk_lost
        total_defender_lost += def_lost
        total_rounds += rounds

    print(f"\n=== {name} ===")
    print(f"Attacker: {attacker_units}  Defender: {defender_units}")
    print(f"Trials: {trials}")
    print(f"Attacker win rate: {attacker_wins/trials*100:.1f}%")
    print(f"Defender win rate: {defender_wins/trials*100:.1f}%")
    print(f"Avg units lost - attacker: {total_attacker_lost/trials:.1f}, defender: {total_defender_lost/trials:.1f}")
    print(f"Avg rounds to resolve: {total_rounds/trials:.1f}")


TRIALS = 150

run_matchup("50 Tank vs 100 Infantry", {"tank": 50}, {"infantry": 100}, trials=TRIALS)
run_matchup("30 Artillery vs 100 Infantry", {"artillery": 30}, {"infantry": 100}, trials=TRIALS)
run_matchup("Equal cost: 100 Infantry vs 50 Tank", {"infantry": 100}, {"tank": 50}, trials=TRIALS)
run_matchup("Equal cost: 100 Infantry vs 33 Artillery", {"infantry": 100}, {"artillery": 33}, trials=TRIALS)
run_matchup("Artillery vs Tank (equal cost, 10 vs 15)", {"artillery": 10}, {"tank": 15}, trials=TRIALS)

# Demonstrates whether attack order actually affects outcomes right now -
# same composition, two different orders, should show IDENTICAL results
# until the order-wiring bug above is fixed

run_matchup(
    "Mixed army, order = artillery/infantry/tank",
    {"infantry": 40, "tank": 20, "artillery": 20},
    {"infantry": 31, "tank": 21, "artillery": 22},
    trials=TRIALS,
)
run_matchup(
    "Same mixed army, order = tank/artillery/infantry",
    {"infantry": 40, "tank": 20, "artillery": 20},
    {"infantry": 40, "tank": 20, "artillery": 20},
    trials=TRIALS,
)