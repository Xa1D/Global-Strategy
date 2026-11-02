from combat import Combat, STATS
from testing_classes import TestTerritory, DeterministicCombat, check

def test_simultaneous_damage():
    attacker, defender = TestTerritory(infantry=1), TestTerritory(infantry=1)
    battle = DeterministicCombat(attacker, defender, 2, 2) #fixed damage of 2 each
    result = battle.simulate_combat()
    check("Both armies deal 2 damage and lose units in the same round", "5.2", (1,True, 0,0),
          (len(battle.combat_log), result == "attacker", attacker.total_units(), defender.total_units()))

def test_combat_log():
    battle = DeterministicCombat(TestTerritory(infantry=1), TestTerritory(infantry=1), 2, 2)
    battle.simulate_combat()
    units_after = {"infantry": 0, "tank": 0, "artillery": 0} #specific to the battle case above (1 infantry vs 1 infantry)
    units_before = {"infantry": 1, "tank": 0, "artillery": 0}
    expected = {"attacker_unit_type": ["infantry"], "defender_unit_type": ["infantry"],
                "attacker_damage_dealt": 2, "defender_damage_dealt": 2,
                "attacker_breakdowns": {"infantry": {"infantry": 2}},
                "defender_breakdowns": {"infantry": {"infantry": 2}},
                "attacker_before": units_before, "defender_before": units_before,
                "attacker_after": units_after, "defender_after": units_after}
    check("Combat log entry", "5.7", expected, battle.combat_log[0]) #battle only lasts 1 round

def test_battle_outcome():
    battles = (DeterministicCombat(TestTerritory(infantry=2), TestTerritory(infantry=1), 2, 0),
                DeterministicCombat(TestTerritory(infantry=1), TestTerritory(infantry=2), 0, 2),
                DeterministicCombat(TestTerritory(infantry=1), TestTerritory(infantry=1), 3, 2), #attacker has greater excess damage
                DeterministicCombat(TestTerritory(infantry=1), TestTerritory(infantry=1), 2, 3))
    check("Combat outcome is handled correctly", "5.5", ("attacker", "defender", "attacker", "defender"), tuple(battle.simulate_combat() for battle in battles))

def test_partial_damage():
    defender = TestTerritory(infantry=1)
    battle = Combat(TestTerritory(infantry=1), defender)
    battle.simulate_damage(defender, 1.0, ["infantry", "tank", "artillery"], battle.defender_hp)
    check("Partial damage reduces health by 1 but keeps the unit", "5.4", True, defender.units["infantry"] == 1 and battle.defender_hp["infantry"][0] == (STATS["infantry"]["health"]-1))
    battle.simulate_damage(defender, 1.0, ["infantry", "tank", "artillery"], battle.defender_hp)
    check("A second hit of the same size kills the unit", "5.4", 0, defender.units["infantry"]) #damaged infantry at 1hp is dealt 1 damage to kill it

def test_random_damage():
    sample = Combat(TestTerritory(), TestTerritory())
    for unit_type, stats in STATS.items():
        hits = [damage for damage in (sample.get_damage(unit_type, 1) for trial in range(5000)) if damage > 0] #runs 5000 trials for each unit type, recording all the hits
        ratios = [damage / stats["attack"] for damage in hits] #obtains the original multiplier by dividing damage by original attack
        miss_probability = 1 - len(hits) / 5000 #Gets number of misses and divides by trials to obtain the probability
        miss_deviation = abs(miss_probability - stats["miss"]) #calculates the deviation from the actual miss chance 
        check(f"{unit_type} hits stay within 0.75 - 1.25 and misses match the miss chance", "5.3", (True, True),
              (0.75 <= min(ratios) and max(ratios) <= 1.25, miss_deviation < 0.025))


if __name__ == "__main__":
    test_simultaneous_damage()
    test_combat_log()
    test_battle_outcome()
    test_partial_damage()
    test_random_damage()
