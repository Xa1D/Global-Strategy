#import json
#data = json.load(open("africa_coords.json"))
#print([n for n in data.keys() if "nea" in n or "adagascar" in n])
import pygame
pygame.init()
import ai_scoring
from ai import AI
from player import Player
from combat import VALUE_WEIGHTS

class FakeClock:
    def __init__(self):
        self.t = 0

    def advance(self, ms):
        self.t += ms

    def get_ticks(self):
        return self.t

class MockCountry:
    def __init__(self, name, infantry=0, tank=0, artillery=0, adjacent=None):
        self.name = name
        self.units = {"infantry": infantry, "tank": tank, "artillery": artillery}
        self.adjacent = adjacent or []
        self.combat = False
        self.attack_cooldown = 0
        self.owner = None
        self.highlighted = False

    def total_units(self):
        return sum(self.units.values())

    def unit_value(self, weights):
        return sum(self.units.get(t, 0) * w for t, w in weights.items())

    def __repr__(self):
        return f"<{self.name}>"

class MockWorld:
    def __init__(self, countries):
        self.countries = {c.name: c for c in countries}

class MockOwner:
    def __init__(self, territories=None):
        self.territories = territories or []


fake_clock = FakeClock()
pygame.time.get_ticks = fake_clock.get_ticks

def build_line_map(length=8):
    """A -> B -> C -> ... in a straight line, for BFS testing."""
    names = [chr(ord("A") + i) for i in range(length)]
    countries = [MockCountry(n, infantry=10) for n in names]
    for i, c in enumerate(countries):
        adj = []
        if i > 0:
            adj.append(names[i - 1])
        if i < length - 1:
            adj.append(names[i + 1])
        c.adjacent = adj
    return MockWorld(countries), countries


def build_grid_map(w=4, h=4):
    """A small grid, for the full AI simulation - more realistic branching."""
    countries = []
    grid = {}
    for y in range(h):
        for x in range(w):
            name = f"{x}_{y}"
            c = MockCountry(name, infantry=10, tank=2, artillery=1)
            grid[(x, y)] = c
            countries.append(c)
    for (x, y), c in grid.items():
        adj = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) in grid:
                adj.append(f"{nx}_{ny}")
        c.adjacent = adj
    return MockWorld(countries), grid



def test_scoring_functions():
    print("\n" + "=" * 60)
    print("1. SCORING FUNCTION CORRECTNESS")
    print("=" * 60)

    world, countries = build_line_map(4)
    attacker = countries[0]
    defender = countries[1]

    # equal strength -> count_ratio_score should be 0
    attacker.units = {"infantry": 100, "tank": 0, "artillery": 0}
    defender.units = {"infantry": 100, "tank": 0, "artillery": 0}
    score = ai_scoring.count_ratio_score(attacker, defender)
    print(f"count_ratio_score, equal strength: {score:.3f} (expect 0.0)")
    assert abs(score - 0.0) < 0.01, "FAILED: equal strength should score 0"

    # double strength -> should be 1.0 (capped)
    attacker.units = {"infantry": 200, "tank": 0, "artillery": 0}
    score = ai_scoring.count_ratio_score(attacker, defender)
    print(f"count_ratio_score, double strength: {score:.3f} (expect 1.0)")
    assert abs(score - 1.0) < 0.01, "FAILED: double strength should score 1.0"

    # 1.5x strength -> should be 0.5
    attacker.units = {"infantry": 150, "tank": 0, "artillery": 0}
    score = ai_scoring.count_ratio_score(attacker, defender)
    print(f"count_ratio_score, 1.5x strength: {score:.3f} (expect 0.5)")
    assert abs(score - 0.5) < 0.01, "FAILED: 1.5x strength should score 0.5"

    # weaker attacker -> should clamp to 0, not go negative
    attacker.units = {"infantry": 50, "tank": 0, "artillery": 0}
    score = ai_scoring.count_ratio_score(attacker, defender)
    print(f"count_ratio_score, weaker attacker: {score:.3f} (expect 0.0, not negative)")
    assert score == 0.0, "FAILED: weaker attacker should clamp to 0, not go negative"

    # value_ratio_score should weight artillery higher than infantry
    attacker.units = {"infantry": 0, "tank": 0, "artillery": 100}
    defender.units = {"infantry": 100, "tank": 0, "artillery": 0}
    score = ai_scoring.value_ratio_score(attacker, defender)
    print(f"value_ratio_score, 100 artillery vs 100 infantry: {score:.3f} (expect 1.0, artillery worth 2x)")
    assert abs(score - 1.0) < 0.01, "FAILED: artillery should be worth double infantry in value terms"

    # threat_score: a country with no adjacent enemy-owned territory should score 1.0 (safe)
    empty_enemy = MockOwner(territories=[])
    threat = ai_scoring.threat_score(countries[0], world, empty_enemy, n=10)
    print(f"threat_score, no adjacent enemy: {threat:.3f} (expect 1.0)")
    assert threat == 1.0, "FAILED: no adjacent enemy should be maximally safe"

    # threat_score: an enemy owning the adjacent country should reduce it
    countries[1].units = {"infantry": 20, "tank": 0, "artillery": 0}
    real_enemy = MockOwner(territories=[countries[1]])
    threat_with_enemy = ai_scoring.threat_score(countries[0], world, real_enemy, n=10)
    print(f"threat_score, enemy owns adjacent country with 20 units, n=10: {threat_with_enemy:.3f} (expect 0.0, clamped)")
    assert threat_with_enemy == 0.0, "FAILED: enemy strength >= n should clamp threat to 0"

    print("All scoring function checks PASSED.")


def test_markov_accuracy():
    print("\n" + "=" * 60)
    print("2. MARKOV PREDICTION ACCURACY")
    print("=" * 60)
    matrix = ai_scoring.new_transition_matrix()
    # simulate an opponent that, from "attacking", goes to "defending"
    # 70% of the time and "idle" 30% of the time - see if enough
    # observations make predict_next_state converge close to that
    import random
    random.seed(42)
    n_observations = 2000
    for _ in range(n_observations):
        roll = random.random()
        to_state = "defending" if roll < 0.7 else "idle"
        ai_scoring.record_transition(matrix, "attacking", to_state)
    prediction = ai_scoring.predict_next_state(matrix, "attacking")
    print(f"After {n_observations} observations (true: 70% defending, 30% idle):")
    for state, prob in prediction.items():
        print(f"  {state}: {prob:.3f}")
    defending_prob = prediction["defending"]
    print(f"\nPredicted P(defending): {defending_prob:.3f} (true: 0.70)")
    error = abs(defending_prob - 0.70)
    print(f"Error: {error:.3f}")
    if error < 0.03:
        print("PASSED: prediction converged closely to the true distribution.")
    else:
        print("WARNING: prediction did not converge as closely as expected - "
              "check record_transition/predict_next_state for a bug.")

    # sanity check: an unobserved row should stay at the uniform prior
    fresh_matrix = ai_scoring.new_transition_matrix()
    fresh_prediction = ai_scoring.predict_next_state(fresh_matrix, "expanding")
    uniform = 1 / len(ai_scoring.STATES)
    print(f"\nUnobserved row should be uniform ({uniform:.3f} each):")
    for state, prob in fresh_prediction.items():
        print(f"  {state}: {prob:.3f}")
    assert all(abs(p - uniform) < 0.001 for p in fresh_prediction.values()), \
        "FAILED: unobserved row should be exactly uniform"
    print("PASSED: unobserved row is uniform as expected.")


def test_pathfinding():
    print("\n" + "=" * 60)
    print("3. BFS PATHFINDING CORRECTNESS")
    print("=" * 60)

    world, countries = build_line_map(6)  # A-B-C-D-E-F
    ai_country = countries[0]
    ai = AI(ai_country, playstyle="aggressive", offset=0)

    target = world.countries["E"]
    path = ai.search(ai_country, target, world)
    path_names = [c.name for c in path] if path else None
    print(f"Path from A to E on line A-B-C-D-E-F: {path_names}")
    expected = ["A", "B", "C", "D", "E"]
    assert path_names == expected, f"FAILED: expected {expected}, got {path_names}"
    print("PASSED: shortest path found correctly.")

    # unreachable target should return empty, not crash
    isolated = MockCountry("ISOLATED", infantry=5, adjacent=[])
    world.countries["ISOLATED"] = isolated
    path = ai.search(ai_country, isolated, world)
    print(f"Path to an unreachable/isolated country: {path}")
    assert not path, "FAILED: unreachable target should return an empty/falsy path, not crash"
    print("PASSED: unreachable target handled without crashing.")



def test_choose_state_distribution():
    print("\n" + "=" * 60)
    print("4. CHOOSE_STATE SAMPLING DISTRIBUTION")
    print("=" * 60)
    state_scores = {"attacking": 0.6,"expanding": 0.3,"defending": 0.1,"reinforcing": 0.0,"idle": 0.2,}
    total = sum(state_scores.values())
    expected_probs = {s: v / total for s, v in state_scores.items()}
    trials = 5000
    counts = {s: 0 for s in state_scores}
    for _ in range(trials):
        chosen = ai_scoring.choose_state(state_scores)
        counts[chosen] += 1
    print(f"Over {trials} draws:")
    print(f"{'state':<12}{'expected':>10}{'observed':>10}")
    for s in state_scores:
        expected = expected_probs[s]
        observed = counts[s] / trials
        print(f"{s:<12}{expected:>10.3f}{observed:>10.3f}")
        assert abs(expected - observed) < 0.03, \
            f"FAILED: {s} distribution off by more than expected sampling noise"
    print("PASSED: empirical distribution matches intended probabilities.")


def run_ai_simulation(cycles=40, verbose=True):
    print("\n" + "=" * 60)
    print("5. FULL AI SIMULATION (grid map, two AI, fast-forwarded clock)")
    print("=" * 60)
    world, grid = build_grid_map(4, 4)
    # give one AI a starting country and a human "player" stand-in
    player_country = grid[(0, 0)]
    ai_1_country = grid[(3, 3)]
    ai_2_country = grid[(0, 3)]
    player = Player(player_country)
    ai_1 = AI(ai_1_country, playstyle="aggressive", offset=0)
    ai_2 = AI(ai_2_country, playstyle="defensive", offset=1500)
    ai_players = [ai_1, ai_2]
    state_log = {ai_1.country.name: [], ai_2.country.name: []}
    for cycle in range(cycles):
        fake_clock.advance(1000)  # advance 1 simulated second per loop tick
        for ai in ai_players:
            before_state = ai.last_action
            ai.update_ai(world, player, ai_players)
            ai.update()
            if ai.last_action != before_state:
                state_log[ai.country.name].append(ai.last_action)
    print(f"Ran {cycles} simulated seconds.\n")
    for name, log in state_log.items():
        print(f"{name} state history: {log}")
    print("\nFinal summary:")
    for ai in ai_players:
        print(f"  {ai.country.name} ({ai.playstyle}): "
              f"{len(ai.territories)} territories, {ai.currency} currency, "
              f"{ai.attacks_made} attacks ({ai.attacks_won}W/{ai.attacks_lost}L), "
              f"currency_spent={ai.currency_spent}")
    return ai_players, state_log


test_scoring_functions()
test_markov_accuracy()
test_pathfinding()
test_choose_state_distribution()
run_ai_simulation(cycles=40)
