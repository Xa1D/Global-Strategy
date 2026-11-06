import pygame
from ai import AI
from ai_config import STATES
from player import Player
from testing_classes import TestMap, TestTerritory, ScoreRecorder, test

def connect(a, b): #makes two territories neighbours
    a.adjacent.append(b.name)
    b.adjacent.append(a.name)

def conquer(player, territory): #gives a territory to a player, like a capture in the game
    player.territories.append(territory)
    territory.owner = player

def rounded(values): #scores are floats so round to 2 d.p. before comparing
    return tuple(round(value, 2) for value in values)

def target_stats(ai, world, enemies): 
    return (ai.can_attack(world, enemies), ai.can_expand(world, enemies),
            ai.best_attack_target(world, enemies, set())[0] is not None, ai.best_expansion_target(world, enemies, set())[0] is not None)

def composition(territory):
    return (territory.units["infantry"], territory.units["tank"], territory.units["artillery"])

def observed_matrix(): #opponent attacks twice then defends, observed after each action
    observer, opponent = AI(TestTerritory("Observer"), "balanced"), Player(TestTerritory("opponent"))
    observer.observe_opponents([opponent])
    for action in ("attacking", "attacking", "defending"):
        opponent.record_action(action)
        observer.observe_opponents([opponent])
    return observer, observer.opponent_matrices[opponent]

def state_scores(predicted_state):
    # returns the AI's final state scores when the enemy (who just attacked) is certain to do predicted_state next
    # ScoreRecorder captures the scores instead of letting choose_state pick a state at random
    source, friend = TestTerritory("source", infantry=10), TestTerritory("friend", infantry=10)
    enemy_territory, neutral = TestTerritory("enemy", infantry=5), TestTerritory("neutral", infantry=100) #neutral keeps scores below the 1.0 cap
    ai, enemy = AI(source, "balanced"), Player(enemy_territory)
    conquer(ai, friend)
    for territory in (friend, enemy_territory, neutral):
        connect(source, territory)
    world = TestMap([source, friend, enemy_territory, neutral])
    enemy.record_action("attacking")
    matrix = ai.scorer.new_transition_matrix()
    matrix["attacking"] = {state: 0 for state in STATES}
    matrix["attacking"][predicted_state] = 100
    ai.opponent_matrices[enemy] = matrix
    recorder = ScoreRecorder()
    ai.scorer.choose_state = recorder.choose_state #evaluate state uses recorder's choose_state method instead
    ai.evaluate_state(world, [enemy])
    return recorder.scores

def purchased_units(aggressive_enemy):
    # buys with 100 currency while the enemy is certain to follow attacking with attacking (aggressive) or defending (passive)
    danger, enemy_territory = TestTerritory("danger", infantry=10), TestTerritory("enemy", infantry=5)
    buyer, enemy = AI(danger, "balanced"), Player(enemy_territory)
    connect(danger, enemy_territory)
    enemy.record_action("attacking")
    matrix = buyer.scorer.new_transition_matrix()
    follow_up = "attacking" if aggressive_enemy else "defending"
    for state in STATES:
        matrix[state] = {next_state: 0 for next_state in STATES}
        matrix[state][follow_up] = 100
    buyer.opponent_matrices[enemy] = matrix
    buyer.currency = 100
    buyer.purchase_units(TestMap([danger, enemy_territory]), [enemy])
    return danger.units["tank"] + danger.units["artillery"] #the stronger unit types

class AITests:
    def __init__(self, file):
        self.file = file  #open results file used by every test

    def test_playstyle_weights(self):
        # identical scores for every state, so any difference comes from the playstyle alone
        base = {state: 1.0 for state in STATES}
        aggressive, balanced, defensive = (AI(TestTerritory(), style).scorer.apply_playstyle_weights(base) for style in ("aggressive", "balanced", "defensive"))
        # aggressive favours attack/expand, defensive favours defend/reinforce, balanced changes nothing
        test(self.file, "Playstyles favour intended state groups", "2.1 / 2.6", (True, True, True),
              (aggressive["attacking"] + aggressive["expanding"] > defensive["attacking"] + defensive["expanding"],
               defensive["defending"] + defensive["reinforcing"] > aggressive["defending"] + aggressive["reinforcing"], balanced == base))

    def test_empty_territory_weights(self):
        # more empty territories shifts scores towards defending/reinforcing
        scorer = AI(TestTerritory(), "balanced").scorer
        scores = {state: 1.0 for state in STATES}
        low, high = scorer.apply_empty_territory_weights(0.2, scores), scorer.apply_empty_territory_weights(0.4, scores) #20% and 40% empty
        test(self.file, "Empty-territory weights change above 20 percent", "2.7", ((0.7, 0.7, 1.3, 1.3, 1.0), (0.5, 0.5, 2.0, 2.0, 1.0)),
              (tuple(low[state] for state in STATES), tuple(high[state] for state in STATES)))

    def test_territory_score(self):
        # score of attacking the defender, built from count, value, friendly support and enemy threat
        attacker, defender, a, b = (TestTerritory("Attacker", infantry=15), TestTerritory("Defender", infantry=10),
                                    TestTerritory("a", infantry=15), TestTerritory("Support", infantry=5))
        ai, enemy = AI(attacker, "balanced"), Player(defender)
        conquer(ai, a)
        conquer(enemy, b)
        for territory in (defender, a, b):
            connect(attacker, territory)
        world = TestMap([attacker, defender, a, b])
        # 15 = average units per territory the AI owns, used to scale support and threat
        scores = (ai.scorer.count_ratio_score(attacker, defender), ai.scorer.value_ratio_score(attacker, defender),
                  ai.scorer.connectivity_score(attacker, world, ai, 15), ai.scorer.threat_score(attacker, world, enemy, 15),
                  ai.scorer.score_territory(attacker, defender, world, enemy))
        # expected: count 0.5, value 0.5, support 1.0, threat 0.0, then the final weighted score
        test(self.file, "Territory score combines count, value, support and threat", "2.4", (0.5, 0.5, 1.0, 0.0, 0.5), rounded(scores))
        # same position, only the attacker's strength changes
        attackers = []
        for units in (2, 30):
            attacker.units["infantry"] = units
            attackers.append(ai.scorer.score_territory(attacker, defender, world, enemy))
        test(self.file, "Weaker attackers score lower and stronger attackers score higher, within 0 to 1", "2.4", (0.25, 0.75), rounded(attackers))

    def test_bfs_path(self):
        # short route A-B-D, longer route A-C-E-D, and F is not connected to anything
        a, b, c, d, e, f = [TestTerritory(name) for name in "ABCDEF"]
        for first, second in ((a, b), (b, d), (a, c), (c, e), (e, d)):
            connect(first, second)
        ai, world = AI(a, "balanced"), TestMap([a, b, c, d, e, f])
        test(self.file, "BFS finds the shortest path", "2.8", ["A", "B", "D"], [territory.name for territory in ai.search(a, d, world)])
        test(self.file, "BFS returns no route to an isolated territory", "2.8", None, ai.search(a, f, world))

    def test_attack_target_selection(self):
        # picks the best enemy neighbour to attack, territories on the AI's path get +0.15
        source = TestTerritory("source", infantry=10)
        weak, medium, strong = TestTerritory("weak", infantry=3), TestTerritory("medium", infantry=5), TestTerritory("strong", infantry=8)
        ai, enemy = AI(source, "balanced"), Player(weak)
        for territory in (medium, strong):
            conquer(enemy, territory)
        for territory in (weak, medium, strong):
            connect(source, territory)
        world = TestMap([source, weak, medium, strong])
        results = []
        for path in (set(), {"weak"}, {"medium"}, {"strong"}): #no path, then a path through each candidate
            pair, score = ai.best_attack_target(world, [enemy], path)
            results.append((pair[0].name, pair[1].name, round(score, 2)))
        #expected - weak wins, weak gets the bonus (0.5 to 0.65) and wins, medium gets bonus and wins, strong gets bonus but score is still too low so weak wins
        test(self.file, "The best target is chosen and path territories gain 0.15", "2.9 / 2.10",
              [("source", "weak", 0.5), ("source", "weak", 0.65), ("source", "medium", 0.65), ("source", "weak", 0.5)], results)

    def test_expansion_target_selection(self):
        # same idea for neutral territories, the path bonus is capped at 1
        source = TestTerritory("source", infantry=10)
        weak, strong = TestTerritory("weak"), TestTerritory("strong", infantry=12) #weak has no defenders
        ai, enemy = AI(source, "balanced"), Player(TestTerritory())
        connect(source, weak)
        connect(source, strong)
        world = TestMap([source, weak, strong])
        results = []
        for path in (set(), {"weak"}, {"strong"}):
            pair, score = ai.best_expansion_target(world, [enemy], path)
            results.append((pair[0].name, pair[1].name, round(score, 2)))
        # weak always wins, and stays at 1.0 even when the bonus is added
        test(self.file, "The best target is chosen and the path bonus is capped at 1", "2.9 / 2.10",
              [("source", "weak", 1.0), ("source", "weak", 1.0), ("source", "weak", 1.0)], results)

    def test_target_calculation(self):
        # the AI plans a path to its most valuable (usually the strongest) unowned territory B, then changes to C once B is captured
        start, strong, weak = TestTerritory("A", infantry=5), TestTerritory("B", infantry=10), TestTerritory("C", infantry=1)
        ai = AI(start, "balanced")
        connect(start, strong)
        connect(start, weak)
        world = TestMap([start, strong, weak])
        first_target = ai.get_target_path(world)[-1].name #last territory in the path is the target
        conquer(ai, strong)
        test(self.file, "Target path is recalculated after the preferred target is captured", "2.8", ("B", "C"), (first_target, ai.get_target_path(world)[-1].name))

    def test_valid_targets(self):
        # each test breaks one rule on the same small map and expects the AI to reject the target
        source, enemy_territory, neutral = TestTerritory("source", infantry=10), TestTerritory("enemy", infantry=5), TestTerritory("neutral")
        ai, enemy = AI(source, "balanced"), Player(enemy_territory)
        connect(source, enemy_territory)
        connect(source, neutral)
        world = TestMap([source, enemy_territory, neutral])
        test(self.file, "AI finds valid adjacent attack and expansion targets", "2.10", (True, True, True, True), target_stats(ai, world, [enemy]))
        # enemy that is not adjacent to any of owned territories
        territory = TestTerritory("territory", infantry=5)
        isolated = TestTerritory("isolated", infantry=10)
        isolated_ai = AI(isolated, "balanced")
        test(self.file, "AI ignores a non-adjacent enemy", "2.10", (False, False, False, False), target_stats(isolated_ai, TestMap([isolated, territory]), [Player(territory)]))
        # source with no units
        source.units["infantry"] = 0
        test(self.file, "AI rejects an empty source", "2.10", (False, False, False, False), target_stats(ai, world, [enemy]))
        source.units["infantry"] = 10
        # source already in combat
        source.combat = True
        test(self.file, "AI rejects a source in combat", "2.10", (False, False, False, False), target_stats(ai, world, [enemy]))
        # enemy in combat, but the neutral territory can still be expanded into
        source.combat, enemy_territory.combat = False, True
        test(self.file, "AI rejects a target in combat", "2.10", (False, True, False, True), target_stats(ai, world, [enemy]))
        enemy_territory.combat = False 
        # targets still in their attack cooldown
        enemy_territory.attack_cooldown = neutral.attack_cooldown = pygame.time.get_ticks() + 100000
        test(self.file, "AI rejects targets in cooldown", "2.10", (False, False, False, False), target_stats(ai, world, [enemy]))

    def test_purchases(self):
        # Danger borders an enemy and Safe doesn't, so Danger should get more of the new units
        danger, safe, enemy_territory = TestTerritory("danger", infantry=10), TestTerritory("safe", infantry=10), TestTerritory("enemy", infantry=5)
        player, enemy = AI(danger, "balanced"), Player(enemy_territory)
        conquer(player, safe)
        connect(danger, enemy_territory)
        player.currency = 100
        player.purchase_units(TestMap([danger, safe, enemy_territory]), [enemy])
        # passes if the AI never overspent and danger gained more units than safe (both started with 10)
        test(self.file, "AI purchases remain within currency and prioritise danger", "2.11", True, 0 <= player.currency < 100 and danger.total_units() - 10 > safe.total_units() - 10)

    def test_reinforcement(self):
        # strong (6 infantry, 4 tank, 2 artillery) sends (12 - 1) // 2 = 5 units to weak (1 infantry)
        # units move in proportion to the mix, with leftovers going to the largest remainders: 2 infantry, 2 tank, 1 artillery
        strong = TestTerritory("strong", infantry=6, tank=4, artillery=2)
        weak = TestTerritory("weak", infantry=1)
        ai = AI(strong, "balanced")
        conquer(ai, weak)
        connect(strong, weak)
        ai.reinforce(TestMap([strong, weak]))
        test(self.file, "AI reinforcement moves the correct number of each unit type", "2.12", ((4, 2, 1), (3, 2, 1)), (composition(strong), composition(weak)))
        test(self.file, "AI reinforcement conserves total units", "2.12", 13, strong.total_units() + weak.total_units())

    def test_transition_counts(self):
        # two transitions were seen ,attacking to attacking and attacking to defending - each count goes from 5 to 6
        observer, matrix = observed_matrix()
        test(self.file, "Repeated and changed actions update transition counts", "2.13", (6, 6), (matrix["attacking"]["attacking"], matrix["attacking"]["defending"]))

    def test_prediction(self):
        # increases count of attacking to expanding, predict again - the outcome (expanding) increases in probability, others decrease
        observer, matrix = observed_matrix()
        before = observer.scorer.predict_next_state(matrix, "attacking")
        matrix["attacking"]["expanding"] += 5
        after = observer.scorer.predict_next_state(matrix, "attacking")
        # attacking row starts as 6, 6, 5, 5, 5 (total 27), then expanding goes 5 to 10 (total 32)
        # attacking 6/27 = 0.22 -> 6/32 = 0.19, expanding 5/27 = 0.19 -> 10/32 = 0.31
        test(self.file, "Prediction values increase as count increases", "2.14", (0.22, 0.19, 0.19, 0.31),
              rounded((before["attacking"], after["attacking"], before["expanding"], after["expanding"])))
        total = sum(after.values()) # adds probabilities
        test(self.file, "Prediction values sum to one", "2.14", (True), abs(total - 1) < 1e-9)

    def test_prediction_influence(self):
        # same position, once expecting a passive enemy and once an aggressive one
        # the relevant scores should differ by exactly the prediction weight, 0.25
        passive, aggressive = state_scores("defending"), state_scores("attacking") #
        differences = (passive["attacking"] - aggressive["attacking"], aggressive["defending"] - passive["defending"], passive["expanding"] - aggressive["expanding"], aggressive["reinforcing"] - passive["reinforcing"])
        test(self.file, "Local and global predictions change relevant scores by 0.25", "2.15", (0.25, 0.25, 0.25, 0.25), rounded(differences))

    def test_two_step_prediction(self):
        # attacking is always followed by defending and defending by expanding, so two moves after attacking should be expanding
        observer = AI(TestTerritory("observer"), "balanced")
        matrix = {state: {next_state: 0 for next_state in STATES} for state in STATES}
        matrix["attacking"]["defending"] = 10
        matrix["defending"]["expanding"] = 10
        two_steps = observer.scorer.predict_future_state(matrix, "attacking")
        # tuple order follows STATES: attacking, expanding, defending, reinforcing, idle
        test(self.file, "Two move prediction multiplies the transition matrix by itself", "2.14", (0.0, 1.0, 0.0, 0.0, 0.0), rounded(two_steps[state] for state in STATES))

    def test_purchase_response(self):
        # an enemy expected to be aggressive should make the AI buy more of the stronger units (tanks and artillery)
        test(self.file, "AI buys stronger units when aggression is predicted", "2.14", True, purchased_units(True) > purchased_units(False))

    def run(self):
        tests = [self.test_playstyle_weights, self.test_empty_territory_weights, self.test_territory_score, self.test_bfs_path, self.test_attack_target_selection, 
                 self.test_expansion_target_selection, self.test_target_calculation, self.test_valid_targets, self.test_purchases, self.test_reinforcement, 
                 self.test_transition_counts, self.test_prediction, self.test_prediction_influence, self.test_two_step_prediction, self.test_purchase_response]
        for test in tests:
            try:
                test()
            except Exception as error:  #a crash is recorded and the associated test along with the error is written to the file
                self.file.write(f"\n{test.__name__} - {type(error).__name__}: {error}\n")

if __name__ == "__main__":
    with open("ai_tests_results.txt", "w") as file:
        AITests(file).run()