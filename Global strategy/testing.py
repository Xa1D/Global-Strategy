"""
script_testing.py - the tests from the documentation that cannot be shown in a video.

Run from the project folder:   python script_testing.py      (add -q to only print FAIL lines)

Covers:  combat (5.2 - 5.5)  |  AI scoring (2.1, 2.3, 2.4, 2.5, 2.6, 2.7)
         AI searching (2.8, 2.9, 2.10)  |  AI opponent prediction (2.13, 2.14, 2.15)
Time-based tests use a fake clock, so they are instant and repeatable.
"""
import sys
import random

import numpy as np
import pygame

pygame.init()


class FakeClock:
    """Replaces pygame.time.get_ticks so the tests control time."""
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now


clock = FakeClock()
pygame.time.get_ticks = clock

from ai import AI
from ai_scoring import STATES, BASE_COUNT, PLAYSTYLE_TERRITORY_SCORING_WEIGHTS, PLAYSTYLE_STATE_WEIGHTS
from combat import Combat, STATS, VALUE_WEIGHTS
from player import Player
from testing_classes import TestTerritory, TestMap

DOC_AI_BATTLE_SECONDS = 5      # what the documentation says an AI battle lasts
QUIET = "-q" in sys.argv
results = []


def check(name, objective, expected, observed, tolerance=None):
    passed = abs(expected - observed) <= tolerance if tolerance is not None else expected == observed
    results.append((objective, name, passed))
    if not QUIET or not passed:
        print(f"\n{name} [{objective}]")
        print(f"Expected: {expected}; Observed: {observed}")
        print("PASS" if passed else "FAIL")


def run(test_function):
    if not QUIET:
        print(f"\n{'=' * 8} {test_function.__name__} {'=' * 8}")
    try:
        test_function()
    except Exception:
        import traceback
        results.append(("-", f"{test_function.__name__} crashed", False))
        print(f"\nERROR in {test_function.__name__}:")
        traceback.print_exc()


def terr(name, infantry=0, tank=0, artillery=0):
    return TestTerritory(name, infantry, tank, artillery)


def connect(a, b):
    a.adjacent.append(b.name)
    b.adjacent.append(a.name)


def claim(player, territory):
    if territory not in player.territories:
        player.territories.append(territory)
    territory.owner = player


def world_of(*territories):
    return TestMap(list(territories))


def unit_totals(*territories):
    return {unit: sum(t.units[unit] for t in territories) for unit in ("infantry", "tank", "artillery")}


# ----------------------------------------------------------------------------------------------
# Combat: simultaneous damage, random damage, partial damage, winner selection
# ----------------------------------------------------------------------------------------------
class ForcedDamageCombat(Combat):
    """Combat where the damage dealt by each unit type is fixed instead of random."""
    DAMAGE = {}

    def get_damage(self, unit_type, count):
        return self.DAMAGE.get(unit_type, 0) if count else 0


def test_combat():
    random.seed(3)
    infantry_health = STATS["infantry"]["health"]

    # 5.2 both sides deal damage before casualties are applied
    ForcedDamageCombat.DAMAGE = {"infantry": infantry_health}
    attacker, defender = terr("A", 1), terr("D", 1)
    battle = ForcedDamageCombat(attacker, defender)
    battle.simulate_combat()
    first = battle.combat_log[0]
    check("Simultaneous damage: both sides hit and lose their unit in the same round", "5.2", (0, 0, infantry_health, infantry_health, 1),
          (attacker.total_units(), defender.total_units(), first["attacker_damage_dealt"], first["defender_damage_dealt"], len(battle.combat_log)))

    # 5.3 miss threshold and 0.75 - 1.25 multiplier limits
    original_random, original_uniform = random.random, random.uniform
    try:
        for unit, stats in STATS.items():
            c = Combat(terr("A"), terr("D"))
            random.random = lambda m=stats["miss"]: m                 # not greater than miss -> miss
            missed = c.get_damage(unit, 5)
            random.random = lambda m=stats["miss"]: m + 1e-6          # just above miss -> hit
            seen = []
            random.uniform = lambda low, high: (seen.append((low, high)), low)[1]
            low_hit = c.get_damage(unit, 5)
            random.uniform = lambda low, high: high
            high_hit = c.get_damage(unit, 5)
            check(f"{unit}: misses at the threshold, hits just above it", "5.3", (0, True), (missed, low_hit > 0))
            check(f"{unit}: multiplier limits are 0.75 and 1.25", "5.3", ((0.75, 1.25), True),
                  (seen[0], abs(low_hit - 0.75 * stats["attack"] * 5) < 1e-9 and abs(high_hit - 1.25 * stats["attack"] * 5) < 1e-9))
    finally:
        random.random, random.uniform = original_random, original_uniform

    # 5.4 partial damage
    target = terr("D", 1)
    c = Combat(terr("A", 1), target)
    half = infantry_health / 2
    c.simulate_damage(target, half, c.get_priority("tank"), c.defender_hp)
    check("Partial damage: the unit survives with reduced health", "5.4", (1, True), (target.units["infantry"], abs(c.defender_hp["infantry"][0] - half) < 1e-9))
    c.simulate_damage(target, half, c.get_priority("tank"), c.defender_hp)
    check("Partial damage: the second hit kills it", "5.4", 0, target.units["infantry"])

    # 5.5 winner selection
    ForcedDamageCombat.DAMAGE = {"artillery": 100, "infantry": 0}
    attacker, defender = terr("A", 0, 0, 1), terr("D", 1)
    result = ForcedDamageCombat(attacker, defender).simulate_combat()
    check("Attacker wins with units left", "5.5", ("attacker", 1, 0), (result, attacker.total_units(), defender.total_units()))
    attacker, defender = terr("A", 1), terr("D", 0, 0, 1)
    result = ForcedDamageCombat(attacker, defender).simulate_combat()
    check("Defender wins with units left", "5.5", ("defender", 0, 1), (result, attacker.total_units(), defender.total_units()))
    artillery_hp, tank_hp = STATS["artillery"]["health"], STATS["tank"]["health"]
    ForcedDamageCombat.DAMAGE = {"artillery": tank_hp + 4, "tank": artillery_hp + 1}      # attacker overkills by 4, defender by 1
    attacker, defender = terr("A", 0, 0, 1), terr("D", 0, 1, 0)
    result = ForcedDamageCombat(attacker, defender).simulate_combat()
    check("Both armies die: attacker did more excess damage -> attacker wins", "5.5", ("attacker", 0, 0), (result, attacker.total_units(), defender.total_units()))
    ForcedDamageCombat.DAMAGE = {"tank": artillery_hp + 1, "artillery": tank_hp + 4}      # attacker overkills by 1, defender by 4
    attacker, defender = terr("A", 0, 1, 0), terr("D", 0, 0, 1)
    result = ForcedDamageCombat(attacker, defender).simulate_combat()
    check("Both armies die: defender did more excess damage -> defender wins", "5.5", ("defender", 0, 0), (result, attacker.total_units(), defender.total_units()))


# ----------------------------------------------------------------------------------------------
# AI scoring: playstyles, territory scoring, state probabilities, empty territory weighting, battle timing
# ----------------------------------------------------------------------------------------------
def known_scoring_setup(style):
    a, b, c, d = terr("A", 15), terr("B", 10), terr("C", 15), terr("D", 5)
    ai, enemy = AI(a, style), Player(b)
    claim(ai, c)
    claim(enemy, d)
    connect(a, b)
    connect(a, c)
    connect(a, d)
    return ai, enemy, a, b, world_of(a, b, c, d)


def test_ai_territory_scoring():
    ai, enemy, a, b, world = known_scoring_setup("balanced")
    scorer = ai.scorer
    n = scorer.get_average_count()
    sub_scores = [scorer.count_ratio_score(a, b), scorer.value_ratio_score(a, b), scorer.connectivity_score(a, world, ai, n), scorer.threat_score(a, world, enemy, n)]
    check("Count, value, connectivity and threat scores for a known position", "2.4", [0.5, 0.5, 1.0, 0.0], sub_scores)
    scores = {}
    for style in ("aggressive", "defensive", "balanced"):
        ai_s, enemy_s, a_s, b_s, world_s = known_scoring_setup(style)
        scores[style] = ai_s.scorer.score_territory(a_s, b_s, world_s, enemy_s)
        expected = float(np.dot(PLAYSTYLE_TERRITORY_SCORING_WEIGHTS[style], sub_scores))
        check(f"{style}: territory score applies its own weights", "2.1 / 2.4", True, abs(scores[style] - expected) < 1e-9)
    check("Aggressive and defensive territory scores differ", "2.1", True, scores["aggressive"] != scores["defensive"])

    a.units["infantry"], b.units["infantry"] = 1, 100
    weak = ai.scorer.score_territory(a, b, world, enemy)
    a.units["infantry"], b.units["infantry"] = 500, 1
    strong = ai.scorer.score_territory(a, b, world, enemy)
    check("Weak attacker scores lower than strong attacker", "2.4", True, weak < strong)
    random.seed(8)
    inside = True
    for _ in range(300):
        for t in world.territories.values():
            t.units = {"infantry": random.randint(0, 200), "tank": random.randint(0, 50), "artillery": random.randint(0, 50)}
        for style in ("aggressive", "defensive", "balanced"):
            probe = AI(a, style)
            probe.territories = [a, world.territories["C"]]
            inside = inside and 0.0 <= probe.scorer.score_territory(a, b, world, enemy) <= 1.0
    check("Territory scores stay between 0 and 1 over 900 random positions", "2.4", True, inside)


def test_ai_states():
    random.seed(2)
    np.random.seed(2)
    scorer = AI(terr("A", 5), "balanced").scorer
    scores = {"attacking": 1.0, "expanding": 1.0, "defending": 0.0, "reinforcing": 2.0, "idle": 0.0}
    samples = 20000
    counts = {s: 0 for s in STATES}
    for _ in range(samples):
        counts[scorer.choose_state(scores)] += 1
    expected = {"attacking": 0.25, "expanding": 0.25, "defending": 0.0, "reinforcing": 0.5, "idle": 0.0}
    check("Selection frequencies match score / total score", "2.5", True, all(abs(counts[s] / samples - expected[s]) < 0.02 for s in STATES))
    check("States with a score of zero are never selected", "2.5", (0, 0), (counts["defending"], counts["idle"]))
    check("If every score is 0 the idle state is chosen", "2.5", ["idle"] * 50, [scorer.choose_state({s: 0 for s in STATES}) for _ in range(50)])

    equal = {s: 1.0 for s in STATES}

    def share(style, states):
        weighted = AI(terr("A", 5), style).scorer.apply_playstyle_weights(equal)
        return sum(weighted[s] for s in states) / sum(weighted.values())

    check("Aggressive favours attacking + expanding more than defensive", "2.1 / 2.6", True, share("aggressive", ["attacking", "expanding"]) > share("defensive", ["attacking", "expanding"]))
    check("Defensive favours defending + reinforcing more than aggressive", "2.1 / 2.6", True, share("defensive", ["defending", "reinforcing"]) > share("aggressive", ["defending", "reinforcing"]))
    check("Playstyle weights come from PLAYSTYLE_STATE_WEIGHTS", "2.1", {s: PLAYSTYLE_STATE_WEIGHTS["aggressive"][s] for s in STATES}, AI(terr("A", 5), "aggressive").scorer.apply_playstyle_weights(equal))

    def shares(weighted):
        total = sum(weighted.values())
        return {s: weighted[s] / total for s in weighted}

    base = shares(equal)
    low = shares(scorer.apply_empty_territory_weights(0.2, equal))
    high = shares(scorer.apply_empty_territory_weights(0.4, equal))
    check("20% empty: attack/expand less likely, defend/reinforce more likely", "2.7", (True, True),
          (low["attacking"] < base["attacking"] and low["expanding"] < base["expanding"], low["defending"] > base["defending"] and low["reinforcing"] > base["reinforcing"]))
    check("Over 20% empty: the effect is stronger", "2.7", (True, True), (high["attacking"] < low["attacking"], high["defending"] > low["defending"]))
    check("Zero scores stay zero after empty territory weighting", "2.7", True, all(v == 0 for v in scorer.apply_empty_territory_weights(0.5, {s: 0 for s in STATES}).values()))


def test_ai_timing():
    clock.now = 0
    a, b = terr("A", 5), terr("B", 5)
    ai, enemy = AI(a, "balanced"), Player(b)
    connect(a, b)
    world = world_of(a, b)
    clock.now = 30000
    ai.start_attack(a, b)
    clock.now = 30000 + ai.attack_duration - 1
    ai.update(world, enemy, [])
    check("AI battle has not resolved just before attack_duration", "2.3", (True, "attacking"), (a.combat, ai.state))
    clock.now = 30000 + ai.attack_duration
    ai.update(world, enemy, [])
    check("AI battle resolves at attack_duration", "2.3", (False, False, "idle"), (a.combat, b.combat, ai.state))
    check("AI battle length matches the documentation", "2.3", DOC_AI_BATTLE_SECONDS * 1000, ai.attack_duration)


def search_world():
    a, b, c, d, e, f = [terr(n) for n in "ABCDEF"]
    for x, y in [(a, b), (b, d), (a, c), (c, e), (e, d)]:
        connect(x, y)
    return a, b, c, d, e, f, world_of(a, b, c, d, e, f)


def test_ai_search():
    a, b, c, d, e, f, world = search_world()
    ai = AI(a, "balanced")
    path = ai.search(a, d, world)
    check("BFS returns the shortest of two routes", "2.8", ["A", "B", "D"], [t.name for t in path])
    check("Path only contains adjacent consecutive territories", "2.8", True, all(path[i + 1].name in path[i].adjacent for i in range(len(path) - 1)))
    check("BFS to a disconnected territory returns no path", "2.8", None, ai.search(a, f, world))

    b.units["artillery"] = 100
    a.units["infantry"] = 100
    check("Target selection prefers the most valuable territory", "2.8", ["B"], [t.name for t in ai.choose_targets(world, 1)])
    claim(ai, b)
    check("After the preferred target is captured the targets are recalculated", "2.8 / 2.9", True, "B" not in [t.name for t in ai.choose_targets(world, 1)])

    outcomes = {}
    for label, mine, theirs in (("0.50", 15, 10), ("0.95", 39, 20)):
        x, y = terr("X", mine), terr("Y", theirs)
        owner = AI(x, "balanced")
        connect(x, y)
        w = world_of(x, y)
        on_path = owner.best_expansion_target(w, [], {"Y"})[1]
        off_path = owner.best_expansion_target(w, [], set())[1]
        outcomes[label] = (round(on_path, 6), round(off_path, 6))
    check("Base 0.50 -> 0.65 on the path, base 0.95 -> 1.00 (capped); off-path unchanged", "2.8 / 2.9", {"0.50": (0.65, 0.5), "0.95": (1.0, 0.95)}, outcomes)


def test_ai_attack_validity():
    clock.now = 10000

    def setup():
        a, b, n, far = terr("A", 10), terr("B", 5), terr("N", 3), terr("Far", 5)
        ai, enemy = AI(a, "balanced"), Player(b)
        claim(enemy, far)
        connect(a, b)
        connect(a, n)
        return ai, enemy, a, b, n, world_of(a, b, n, far)

    ai, enemy, a, b, n, world = setup()
    check("Valid adjacent enemy and neutral are accepted", "2.10", (True, True), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))
    ai, enemy, a, b, n, world = setup()
    a.units = {"infantry": 0, "tank": 0, "artillery": 0}
    check("Empty source cannot attack or expand", "2.10", (False, False, None), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy]), ai.best_attack_target(world, [enemy], set())[0]))
    ai, enemy, a, b, n, world = setup()
    a.adjacent.remove("B")
    check("Non-adjacent enemy cannot be attacked", "2.10", (False, None), (ai.can_attack(world, [enemy]), ai.best_attack_target(world, [enemy], set())[0]))
    ai, enemy, a, b, n, world = setup()
    b.combat, n.combat = True, True
    check("Targets in combat are not chosen", "2.10", (False, False), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))
    ai, enemy, a, b, n, world = setup()
    a.combat = True
    check("A source in combat is not used", "2.10", (False, False), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))
    ai, enemy, a, b, n, world = setup()
    b.attack_cooldown = n.attack_cooldown = clock.now + 4000
    check("Targets with an active cooldown are not chosen", "2.10", (False, False), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))
    clock.now += 4000
    check("Targets are valid again once the cooldown ends", "2.10", (True, True), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))



def test_ai_prediction():
    opponent = Player(terr("Opponent"))
    ai = AI(terr("A", 5), "balanced")
    scorer = ai.scorer
    ai.observe_opponents([opponent])
    matrix = ai.opponent_matrices[opponent]
    check("New opponents start with the base count in every cell", "2.13", True, all(matrix[a][b] == BASE_COUNT for a in STATES for b in STATES))
    opponent.record_action("attacking")
    ai.observe_opponents([opponent])
    check("A single observed action creates no transition", "2.13", True, all(matrix[a][b] == BASE_COUNT for a in STATES for b in STATES))
    opponent.record_action("attacking")
    ai.observe_opponents([opponent])
    opponent.record_action("defending")
    ai.observe_opponents([opponent])
    check("attacking -> attacking and attacking -> defending each rise once", "2.13", (BASE_COUNT + 1, BASE_COUNT + 1), (matrix["attacking"]["attacking"], matrix["attacking"]["defending"]))
    check("No other counts change", "2.13", True, sum(matrix[a][b] for a in STATES for b in STATES) == BASE_COUNT * 25 + 2)
    ai.observe_opponents([opponent])
    check("Observing again without new actions does not double count", "2.13", BASE_COUNT + 1, matrix["attacking"]["attacking"])

    row = scorer.predict_next_state(matrix, "attacking")
    total = sum(matrix["attacking"].values())
    check("Prediction is the normalised row of counts", "2.14", True, abs(row["attacking"] - matrix["attacking"]["attacking"] / total) < 1e-9)
    check("Predicted probabilities sum to one", "2.14", 1.0, sum(row.values()), tolerance=1e-9)
    scorer.record_transition(matrix, "attacking", "attacking")
    updated = scorer.predict_next_state(matrix, "attacking")
    check("Increasing a count raises that prediction and still sums to one", "2.14", (True, True), (updated["attacking"] > row["attacking"], abs(sum(updated.values()) - 1) < 1e-9))
    check("Unknown latest action gives uniform predictions", "2.14", {s: 1 / len(STATES) for s in STATES}, scorer.predict_next_state(matrix, "unknown"))

    # local vs global predictions
    near, far = Player(terr("Near", 5)), Player(terr("Far", 5))
    me = terr("Me", 5)
    ai = AI(me, "balanced")
    connect(me, near.territory)
    world = world_of(me, near.territory, far.territory)
    for enemy, favoured in ((near, "defending"), (far, "attacking")):
        ai.opponent_matrices[enemy] = ai.scorer.new_transition_matrix()
        ai.opponent_matrices[enemy][enemy.last_action][favoured] = 1000
    local = ai.predicted_local_states(world, [near, far])
    glob = ai.predicted_global_states([near, far])
    check("Local prediction only uses neighbouring opponents", "2.15", True, local[0] > 0.9 and local[1] < 0.1)
    check("Global prediction averages every opponent", "2.15", True, abs(glob[0] - 0.5) < 0.05 and abs(glob[1] - 0.5) < 0.05)
    check("With no neighbouring enemies local prediction is neutral", "2.15", (0.5, 0.5), AI(terr("Alone", 1), "balanced").predicted_local_states(world_of(terr("Alone", 1)), [far]))


def captured_scores(ai, world, enemies, local, global_):
    """Runs evaluate_state with fixed predictions and returns the state scores it produced."""
    captured = {}
    ai.predicted_local_states = lambda m, e: local
    ai.predicted_global_states = lambda e: global_
    ai.scorer.choose_state = lambda scores: (captured.update(scores), "idle")[1]
    ai.evaluate_state(world, enemies)
    return dict(captured)


def test_ai_prediction_influence():
    clock.now = 10000
    for style in ("balanced", "aggressive"):
        me1, me2, enemy_territory, far_enemy, neutral = terr("Me1", 8), terr("Me2", 4), terr("En", 4), terr("EnFar", 25), terr("Neutral", 10)
        ai, enemy = AI(me1, style), Player(enemy_territory)
        claim(ai, me2)
        claim(enemy, far_enemy)
        connect(me1, me2)
        connect(me1, enemy_territory)
        connect(me2, neutral)
        connect(enemy_territory, far_enemy)
        world = world_of(me1, me2, enemy_territory, far_enemy, neutral)
        ai.currency = 0
        base = captured_scores(ai, world, [enemy], (0.0, 0.0), (0.0, 0.0))
        weights = PLAYSTYLE_STATE_WEIGHTS[style]
        headroom = all(base[s] / weights[s] < 0.75 for s in ("attacking", "expanding", "defending", "reinforcing"))
        check(f"{style}: test position leaves room below the cap of 1", "2.15", True, headroom)
        cases = {"attacking": ((1.0, 0.0), (0.0, 0.0)), "defending": ((0.0, 1.0), (0.0, 0.0)),
                 "expanding": ((0.0, 0.0), (1.0, 0.0)), "reinforcing": ((0.0, 0.0), (0.0, 1.0))}
        for state, (local, global_) in cases.items():
            changed = captured_scores(ai, world, [enemy], local, global_)
            difference = changed[state] - base[state]
            others_unchanged = all(abs(changed[s] - base[s]) < 1e-9 for s in STATES if s != state)
            check(f"{style}: a predicted change of 1 moves the {state} score by 0.25 x playstyle weight", "2.15", (True, True), (abs(difference - 0.25 * weights[state]) < 1e-9, others_unchanged))


def main():
    random.seed(1)
    np.random.seed(1)
    for test in (test_combat, test_ai_territory_scoring, test_ai_states, test_ai_timing, test_ai_search,
                 test_ai_attack_validity, test_ai_prediction, test_ai_prediction_influence):
        run(test)
    failed = [(objective, name) for objective, name, ok in results if not ok]
    print("\n" + "=" * 60)
    print(f"{len(results) - len(failed)} / {len(results)} checks passed")
    for objective, name in failed:
        print(f"  FAILED [{objective}] {name}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()