from combat import Combat
from testing_classes import TestTerritory

def simulate_battle(attacker_units, defender_units):
    attacker = TestTerritory(infantry=attacker_units.get("infantry", 0), tank=attacker_units.get("tank", 0),artillery=attacker_units.get("artillery", 0))
    defender = TestTerritory(infantry=defender_units.get("infantry", 0),tank=defender_units.get("tank", 0), artillery=defender_units.get("artillery", 0))
    attacker_before = attacker.total_units()
    defender_before = defender.total_units()
    battle = Combat(attacker, defender)
    result = battle.simulate_combat()
    attacker_after = attacker.total_units()
    defender_after = defender.total_units()
    rounds = len(battle.combat_log)
    return result, attacker_before - attacker_after, defender_before - defender_after, rounds

def simulate_test(name, attacker_units, defender_units, trials=200):
    attacker_wins = 0
    defender_wins = 0
    total_attacker_lost = 0
    total_defender_lost = 0
    total_rounds = 0
    for trial in range(trials):
        result, attacker_lost, defender_lost, rounds = simulate_battle(attacker_units, defender_units)
        if result == "attacker":
            attacker_wins += 1
        else:
            defender_wins += 1
        total_attacker_lost += attacker_lost
        total_defender_lost += defender_lost
        total_rounds += rounds
    print(f"{name}")
    print(f"Attacker: {attacker_units}  Defender: {defender_units}")
    print(f"Trials: {trials}")
    print(f"Attacker win rate: {attacker_wins/trials*100:.1f}%")
    print(f"Defender win rate: {defender_wins/trials*100:.1f}%")
    print(f"Average units lost - attacker: {total_attacker_lost/trials:.1f}, defender: {total_defender_lost/trials:.1f}")
    print(f"Average rounds: {total_rounds/trials:.1f}")

simulate_test("50 Tank vs 100 Infantry", {"tank": 50}, {"infantry": 100})
simulate_test("33 Artillery vs 100 Infantry", {"artillery": 33}, {"infantry": 100})
simulate_test("10 Artillery vs 15 Tank", {"artillery": 10}, {"tank": 15})
simulate_test("Mixed army vs single army",{"infantry": 20, "tank": 20, "artillery": 20},{"infantry": 120})
simulate_test("Mixed army vs mixed army", {"infantry": 20, "tank": 20, "artillery": 20},{"infantry": 10, "tank": 10, "artillery": 30})
simulate_test("Same mixed army", {"infantry": 20, "tank": 20, "artillery": 20}, {"infantry": 20, "tank": 20, "artillery": 20})  