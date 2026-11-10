import pygame
from ai import AI
from ai_config import STATES
from player import Player
from testing_classes import TestMap, TestTerritory, ScoreRecorder, test

def connect(a, b): #makes two territories neighbours
    a.adjacent.append(b.name)
    b.adjacent.append(a.name)

def conquer(player, territory): #gives a territory to a player
    player.territories.append(territory)
    territory.owner = player

def rounded(values): #scores are floats so rounded to 2 d.p. before comparing
    return tuple(round(value, 2) for value in values)

def get_target_stats(ai, map, enemies): 
    return (ai.can_attack(map, enemies), ai.can_expand(map, enemies),
            ai.best_attack_target(map, enemies, set())[0] is not None, ai.best_expansion_target(map, enemies, set())[0] is not None)

def get_unit_counts(territory):
    return (territory.units["infantry"], territory.units["tank"], territory.units["artillery"])

def get_observed_matrix(): #opponent attacks twice then defends, actions observed
    observer, opponent = AI(TestTerritory("observer"), "balanced"), Player(TestTerritory("opponent"))
    for action in ("attacking", "attacking", "defending"):
        opponent.record_action(action)
    observer.observe_opponents([opponent])
    return observer, observer.opponent_matrices[opponent]

def get_state_scores(predicted_state):
    # returns the AI's final state scores when the enemy who just attacked is certain to do the specified state next
    source, support = TestTerritory("source", infantry=10), TestTerritory("support", infantry=10)
    enemy_territory, neutral = TestTerritory("enemy", infantry=5), TestTerritory("neutral", infantry=100) #neutral keeps scores below the 1.0 cap
    ai, enemy = AI(source, "balanced"), Player(enemy_territory)
    conquer(ai, support)
    for territory in (support, enemy_territory, neutral):
        connect(source, territory)
    map = TestMap([source, support, enemy_territory, neutral])
    enemy.record_action("attacking")
    matrix = ai.scorer.new_transition_matrix()
    matrix["attacking"] = {state: 0 for state in STATES}
    matrix["attacking"][predicted_state] = 100
    ai.opponent_matrices[enemy] = matrix
    recorder = ScoreRecorder()
    ai.scorer.choose_state = recorder.choose_state #evaluate state uses recorder's choose_state method instead
    ai.evaluate_state(map, [enemy])
    return recorder.scores

def get_purchased_units(aggressive_enemy):
    # AI purchases units using 100 currency while the enemy is predicted to be attacking (aggressive) or defending (passive)
    danger, enemy_territory = TestTerritory("danger", infantry=10), TestTerritory("enemy", infantry=5)
    buyer, enemy = AI(danger, "balanced"), Player(enemy_territory)
    connect(danger, enemy_territory)
    enemy.record_action("attacking")
    matrix = buyer.scorer.new_transition_matrix()
    expected_state = "attacking" if aggressive_enemy else "defending"
    for state in STATES:
        matrix[state] = {next_state: 0 for next_state in STATES}
        matrix[state][expected_state] = 100
    buyer.opponent_matrices[enemy] = matrix
    buyer.currency = 100
    buyer.purchase_units(TestMap([danger, enemy_territory]), [enemy])
    return danger.units["tank"] 

class AITests:
    def __init__(self, file):
        self.file = file  

    def test_playstyle_weights(self):
        # identical scores for every state
        base = {state: 1.0 for state in STATES}
        aggressive, balanced, defensive = (AI(TestTerritory(), style).scorer.apply_playstyle_weights(base) for style in ("aggressive", "balanced", "defensive"))
        # aggressive favours attack/expand, defensive favours defend/reinforce, balanced changes nothing
        test(self.file, "Playstyles favour intended state groups", "2.1", (True, True, True),
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
                                    TestTerritory("a", infantry=15), TestTerritory("b", infantry=5))
        ai, enemy = AI(attacker, "balanced"), Player(defender)
        conquer(ai, a)
        conquer(enemy, b)
        for territory in (defender, a, b):
            connect(attacker, territory)
        map = TestMap([attacker, defender, a, b])
        scores = (ai.scorer.count_ratio_score(attacker, defender), ai.scorer.value_ratio_score(attacker, defender),
                  ai.scorer.connectivity_score(attacker, map, ai, 15), ai.scorer.threat_score(attacker, map, enemy, 15), #15 is the AI's average unit count
                  ai.scorer.score_territory(attacker, defender, map, enemy))
        # expected - count 0.5, value 0.5, support 1.0, threat 0.0
        test(self.file, "Territory score combines count, value, support and threat", "2.4", (0.5, 0.5, 1.0, 0.0, 0.5), rounded(scores))
        # same position but the attacker's strength changes
        attackers = []
        for units in (5, 25):
            attacker.units["infantry"] = units
            attackers.append(ai.scorer.score_territory(attacker, defender, map, enemy))
        test(self.file, "Weaker attackers score lower and stronger attackers score higher, within 0 to 1", "2.4", (0.25, 0.75), rounded(attackers))
        # the attacker now has 25 units, so the scores are count 1.0, value 1.0, support 0.75, threat 0.25 - each playstyle weights them differently
        playstyles = []
        for playstyle in ("aggressive", "balanced", "defensive"):
            ai.scorer.playstyle = playstyle
            playstyles.append(ai.scorer.score_territory(attacker, defender, map, enemy))
        test(self.file, "Territory scores use each playstyle's weights", "2.1", (0.85, 0.75, 0.68), rounded(playstyles))

    def test_defence(self):
        # weak is threatened - strong (10 units) is the strongest eligible neighbour so sends half (5), medium (5) is not used 
        weak, strong, medium = TestTerritory("weak", infantry=1), TestTerritory("strong", infantry=10), TestTerritory("medium", infantry=5)
        ai = AI(weak, "balanced")
        for territory in (strong, medium):
            conquer(ai, territory)
            connect(weak, territory)
        ai.defend(weak, TestMap([weak, strong, medium]))
        test(self.file, "AI defence sends half the strongest eligible neighbour's units", "2.11", (6, 5, 4), (weak.total_units(), strong.total_units(), medium.total_units()))

    def test_purchasing(self):
        # border has an enemy next to it with a danger of 0.5, expandable has 2 neutral neighbours, passive has neither
        border, expandable, passive = TestTerritory("border", infantry=10), TestTerritory("expandable", infantry=10), TestTerritory("passive", infantry=10)
        enemy_territory, neutral_1, neutral_2 = TestTerritory("enemy", infantry=5), TestTerritory("neutral_1"), TestTerritory("neutral_2")
        ai, enemy = AI(border, "balanced"), Player(enemy_territory)
        conquer(ai, passive) 
        conquer(ai, expandable)
        connect(border, enemy_territory)
        connect(expandable, neutral_1)
        connect(expandable, neutral_2)
        map = TestMap([border, expandable, passive, enemy_territory, neutral_1, neutral_2])
        scored = ai.scorer.purchase_priority(map, [enemy])
        test(self.file, "Purchase priority ranks danger first, then neutral neighbours", "2.10",
            [("border", 0.5), ("expandable", 0.0), ("passive", 0.0)], [(territory.name, round(danger, 2)) for territory, danger in scored])
        ai.currency = 100
        ai.purchase_units(map, [enemy])
        test(self.file, "AI purchases remain within currency and prioritise danger", "2.10", True,
            0 <= ai.currency < 100 and border.total_units() > expandable.total_units() and border.total_units() > passive.total_units())

    def test_connected_regions(self):
        # a, b and c are connected and d is owned but not adjacent to any of them
        a, b, c, d = [TestTerritory(name, infantry=5) for name in "abcd"]
        ai = AI(a, "balanced")
        for territory in (b, c, d):
            conquer(ai, territory)
        connect(a, b)
        connect(b, c)
        map = TestMap([a, b, c, d])
        connected_regions = ai.scorer.connected_regions(map)
        test(self.file, "Flood fill splits owned territories into connected regions", "2.11", [3, 1], sorted((len(region) for region in connected_regions), reverse=True))

    def test_reinforcement(self):
        # strong (6 infantry, 4 tank, 2 artillery) sends (12 - 1) // 2 = 5 units to weak (1 infantry)
        # units move in proportion to the mix, with leftovers going to the largest remainders: 2 infantry, 2 tank, 1 artillery
        strong = TestTerritory("strong", infantry=6, tank=4, artillery=2)
        weak = TestTerritory("weak", infantry=1)
        ai = AI(strong, "balanced")
        conquer(ai, weak)
        connect(strong, weak)
        ai.reinforce(TestMap([strong, weak]))
        test(self.file, "AI reinforcement moves the correct number of each unit type", "2.11", ((4, 2, 1), (3, 2, 1)), (get_unit_counts(strong), get_unit_counts(weak)))

    def test_bfs_path(self):
        # short route A-B-D, longer route A-C-E-D, and F is not connected to anything
        a, b, c, d, e, f = [TestTerritory(name) for name in "ABCDEF"]
        for first, second in ((a, b), (b, d), (a, c), (c, e), (e, d)):
            connect(first, second)
        ai, map = AI(a, "balanced"), TestMap([a, b, c, d, e, f])
        test(self.file, "BFS finds the shortest path", "2.8", ["A", "B", "D"], [territory.name for territory in ai.search(a, d, map)])
        test(self.file, "BFS returns no route to an isolated territory", "2.8", None, ai.search(a, f, map))

    def test_attack_target_selection(self):
        # picks the best enemy neighbour to attack, territories on the AI's path get +0.15
        source = TestTerritory("source", infantry=10)
        weak, strong = TestTerritory("weak", infantry=3), TestTerritory("strong", infantry=5)
        ai, enemy = AI(source, "balanced"), Player(weak)
        conquer(enemy, strong)
        for territory in (weak, strong):
            connect(source, territory)
        map = TestMap([source, weak, strong])
        results = []
        for path in (set(), {"strong"}): #no path, then a path through strong territory
            pair, score = ai.best_attack_target(map, [enemy], path)
            results.append((pair[0].name, pair[1].name, round(score, 2)))
        #expected - weak wins, strong gets the bonus (0.5 to 0.65) and wins
        test(self.file, "The best target is chosen and path territories gain 0.15", "2.8 / 2.9", [("source", "weak", 0.55), ("source", "strong", 0.7)], results)

    def test_expansion_target_selection(self):
        # same idea for neutral territories, the path bonus is capped at 1
        source = TestTerritory("source", infantry=10)
        weak, strong = TestTerritory("weak"), TestTerritory("strong", infantry=12) #weak has no defenders
        ai, enemy = AI(source, "balanced"), Player(TestTerritory())
        connect(source, weak)
        connect(source, strong)
        map = TestMap([source, weak, strong])
        results = []
        for path in (set(), {"weak"}, {"strong"}):
            pair, score = ai.best_expansion_target(map, [enemy], path)
            results.append((pair[0].name, pair[1].name, round(score, 2)))
        # weak always wins, and stays at 1.0 even when the bonus is added
        test(self.file, "The best target is chosen and the path bonus is capped at 1", "2.8 / 2.9", [("source", "weak", 1.0), ("source", "weak", 1.0), ("source", "weak", 1.0)], results)

    def test_target_validity(self):
        # each test breaks one rule on same map and expects the AI to reject the target
        source, enemy_territory, neutral = TestTerritory("source", infantry=10), TestTerritory("enemy", infantry=5), TestTerritory("neutral")
        ai, enemy = AI(source, "balanced"), Player(enemy_territory)
        connect(source, enemy_territory)
        connect(source, neutral)
        map = TestMap([source, enemy_territory, neutral])
        test(self.file, "AI finds valid adjacent attack and expansion targets", "2.9", (True, True, True, True), get_target_stats(ai, map, [enemy]))
        # enemy that is not adjacent to any of owned territories
        territory, isolated = TestTerritory("territory", infantry=5), TestTerritory("isolated", infantry=10)
        isolated_ai = AI(isolated, "balanced")
        test(self.file, "AI ignores a non-adjacent enemy", "2.9", (False, False, False, False), get_target_stats(isolated_ai, TestMap([isolated, territory]), [Player(territory)]))
        # source with no units
        source.units["infantry"] = 0
        test(self.file, "AI rejects an empty source", "2.9", (False, False, False, False), get_target_stats(ai, map, [enemy]))
        source.units["infantry"] = 10
        # source already in combat
        source.combat = True
        test(self.file, "AI rejects a source in combat", "2.9", (False, False, False, False), get_target_stats(ai, map, [enemy]))
        source.combat = False
        # targets still in their attack cooldown
        enemy_territory.attack_cooldown = neutral.attack_cooldown = pygame.time.get_ticks() + 100000
        test(self.file, "AI rejects targets in cooldown", "2.9", (False, False, False, False), get_target_stats(ai, map, [enemy]))

    def test_transition_counts(self):
        # two transitions were seen - attacking to attacking and attacking to defending - each count goes from 5 to 6
        observer, matrix = get_observed_matrix()
        test(self.file, "Repeated and changed actions update transition counts", "2.12", (6, 6), (matrix["attacking"]["attacking"], matrix["attacking"]["defending"]))

    def test_prediction(self):
        # increases count of attacking to expanding, predict again - the outcome (expanding) increases in probability, others decrease
        observer, matrix = get_observed_matrix()
        before = observer.scorer.predict_next_state(matrix, "attacking")
        matrix["attacking"]["expanding"] += 5
        after = observer.scorer.predict_next_state(matrix, "attacking")
        # attacking row starts as 6, 5, 6, 5, 5 (total 27), then expanding goes 5 to 10 (total 32)
        # attacking 6/27 = 0.22 -> 6/32 = 0.19, expanding 5/27 = 0.19 -> 10/32 = 0.31
        test(self.file, "Prediction values increase as count increases", "2.13", (0.22, 0.19, 0.19, 0.31),
              rounded((before["attacking"], after["attacking"], before["expanding"], after["expanding"])))
        total = sum(after.values()) # adds probabilities
        test(self.file, "Prediction values sum to one", "2.13", True, abs(total - 1) < 1e-9) #may not be exactly 1 due to floats so difference measured

    def test_prediction_weight(self):
        # same position, once expecting a passive enemy and once an aggressive one
        # the relevant scores should differ by the prediction weight (0.25)
        passive, aggressive = get_state_scores("defending"), get_state_scores("attacking") 
        differences = (passive["attacking"] - aggressive["attacking"], aggressive["defending"] - passive["defending"], passive["expanding"] - aggressive["expanding"], aggressive["reinforcing"] - passive["reinforcing"])
        test(self.file, "Local and global predictions change relevant scores by 0.25", "2.14", (0.25, 0.25, 0.25, 0.25), rounded(differences))

    def test_two_step_prediction(self):
        # attacking is always followed by defending and defending by expanding, so two moves after attacking should be expanding
        observer = AI(TestTerritory("observer"), "balanced")
        matrix = {state: {next_state: 0 for next_state in STATES} for state in STATES}
        matrix["attacking"]["defending"] = 20
        matrix["defending"]["expanding"] = 20
        two_steps = observer.scorer.predict_future_state(matrix, "attacking")
        # tuple order follows STATES - attacking, expanding, defending, reinforcing, idle
        test(self.file, "Two move prediction multiplies the transition matrix by itself", "2.13", (0.0, 1.0, 0.0, 0.0, 0.0), rounded(two_steps[state] for state in STATES))

    def test_purchase_response(self):
        # an enemy expected to be aggressive should make the AI buy more tanks according to unit type mix as danger goes up
        test(self.file, "AI buys more tanks when aggression is predicted", "2.14", True, get_purchased_units(True) > get_purchased_units(False))

    def run(self):
        tests = [self.test_playstyle_weights, self.test_empty_territory_weights, self.test_territory_score, self.test_defence, self.test_bfs_path, self.test_attack_target_selection, 
                 self.test_expansion_target_selection, self.test_target_validity, self.test_purchasing, self.test_connected_regions,
                 self.test_reinforcement, self.test_transition_counts, self.test_prediction, self.test_prediction_weight, self.test_two_step_prediction, self.test_purchase_response]
        for test in tests:
            try:
                test()
            except Exception as error:
                self.file.write(f"\n{test.__name__} - {type(error).__name__}: {error}\n")

if __name__ == "__main__":
    with open("ai_tests_results.txt", "w") as file:
        AITests(file).run()