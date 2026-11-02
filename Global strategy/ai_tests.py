import pygame
import ai_scoring
from ai import AI
from ai_scoring import STATES
from player import Player
from testing_classes import TestMap, TestTerritory, check

def connect(a, b):
    a.adjacent.append(b.name)
    b.adjacent.append(a.name)

def claim(player, territory):
    player.territories.append(territory)
    territory.owner = player

class ChoiceRecorder: #records the probabilities it is given
    def __init__(self):
        self.probabilities = []
    def choice(self, states, p):
        self.probabilities.extend(p)
        return states[0]

class ScoreRecorder: #records the final state scores
    def __init__(self):
        self.scores = {}
    def choose_state(self, scores):
        self.scores.update(scores)
        return "idle"

class CountingAI(AI): #counts actions instead of performing them
    def __init__(self, territory, playstyle):
        super().__init__(territory, playstyle)
        self.actions = 0
    def execute_actions(self, map, enemies):
        self.actions += 1

def rounded(values):
    return tuple(round(value, 2) for value in values)

def test_choose_state():
    scorer = AI(TestTerritory(), "balanced").scorer
    for state in STATES:
        scores = {name: 0 for name in STATES}
        scores[state] = 1 #only this state has a score
        check(f"AI can choose {state}", "2.2", state, scorer.choose_state(scores))

def test_zero_scores():
    scorer = AI(TestTerritory(), "balanced").scorer
    check("Zero state scores choose idle", "2.5", "idle", scorer.choose_state({state: 0 for state in STATES}))

def test_state_probabilities():
    scorer = AI(TestTerritory(), "balanced").scorer
    recorder, old_choice = ChoiceRecorder(), ai_scoring.np.random.choice
    ai_scoring.np.random.choice = recorder.choice
    scorer.choose_state({"attacking": 1, "expanding": 0, "defending": 3, "reinforcing": -1, "idle": 0}) #negative score counts as 0
    ai_scoring.np.random.choice = old_choice
    check("State probabilities are normalised and zero scores cannot be selected", "2.5", (0.25, 0.0, 0.75, 0.0, 0.0), rounded(recorder.probabilities))

def test_playstyle_weights():
    base = {state: 1.0 for state in STATES}
    aggressive = AI(TestTerritory(), "aggressive").scorer.apply_playstyle_weights(base)
    defensive = AI(TestTerritory(), "defensive").scorer.apply_playstyle_weights(base)
    check("Playstyles favour intended state groups", "2.1 / 2.6", (True, True),
          (aggressive["attacking"] + aggressive["expanding"] > defensive["attacking"] + defensive["expanding"],
           defensive["defending"] + defensive["reinforcing"] > aggressive["defending"] + aggressive["reinforcing"]))

def test_empty_territory_weights():
    scorer = AI(TestTerritory(), "balanced").scorer
    scores = {state: 1.0 for state in STATES}
    scores["idle"] = 0.0
    low, high = scorer.apply_empty_territory_weights(0.2, scores), scorer.apply_empty_territory_weights(0.4, scores) #20% and 40% empty
    check("Empty-territory weights change above 20 percent and preserve zero scores", "2.7",
          ((0.7, 0.7, 1.3, 1.3, 0.0), (0.5, 0.5, 2.0, 2.0, 0.0)),
          (tuple(low[state] for state in STATES), tuple(high[state] for state in STATES)))

def test_territory_score():
    attacker, defender, friend, support = (TestTerritory("Attacker", infantry=15), TestTerritory("Defender", infantry=10),
                                           TestTerritory("Friend", infantry=15), TestTerritory("Support", infantry=5))
    ai, enemy = AI(attacker, "balanced"), Player(defender)
    claim(ai, friend)
    claim(enemy, support)
    for territory in (defender, friend, support):
        connect(attacker, territory)
    world = TestMap([attacker, defender, friend, support])
    scores = (ai.scorer.count_ratio_score(attacker, defender), ai.scorer.value_ratio_score(attacker, defender),
              ai.scorer.connectivity_score(attacker, world, ai, 15), ai.scorer.threat_score(attacker, world, enemy, 15),
              ai.scorer.score_territory(attacker, defender, world, enemy))
    check("Territory score combines count, value, support and threat", "2.4", (0.5, 0.5, 1.0, 0.0, 0.5), rounded(scores))

def test_bfs_path():
    a, b, c, d, isolated = [TestTerritory(name) for name in "ABCDE"]
    for first, second in ((a, b), (b, d), (a, c), (c, d)):
        connect(first, second) #A-B-D and A-C-D are the two routes
    ai, world = AI(a, "balanced"), TestMap([a, b, c, d, isolated])
    check("BFS finds a shortest path", "2.8", ["A", "B", "D"], [territory.name for territory in ai.search(a, d, world)])
    check("BFS returns no route to an isolated territory", "2.8", None, ai.search(a, isolated, world))

def test_path_bonus():
    ai = AI(TestTerritory("A"), "balanced")
    on_route, off_route = TestTerritory("B"), TestTerritory("C")
    check("Path bonus applies only to the route", "2.9", (0.15, 0.0), (ai.scorer.path_bonus(on_route, {"B"}), ai.scorer.path_bonus(off_route, {"B"})))

def test_purchases():
    danger, safe, enemy_territory = TestTerritory("Danger", infantry=10), TestTerritory("Safe", infantry=10), TestTerritory("Enemy", infantry=5)
    buyer, enemy = AI(danger, "balanced"), Player(enemy_territory)
    claim(buyer, safe)
    connect(danger, enemy_territory) #only Danger borders the enemy
    buyer.currency = 100
    buyer.purchase_units(TestMap([danger, safe, enemy_territory]), [enemy])
    check("AI purchases remain within currency and prioritise danger", "2.11", True,
          0 <= buyer.currency <= 100 and danger.total_units() - 10 > safe.total_units() - 10) #both started with 10

def test_reinforcement():
    strong, weak = TestTerritory("Strong", infantry=12), TestTerritory("Weak", infantry=2)
    ai = AI(strong, "balanced")
    claim(ai, weak)
    connect(strong, weak)
    ai.reinforce(TestMap([strong, weak]))
    check("AI reinforcement moves units without losses", "2.12", True,
          strong.total_units() < 12 and weak.total_units() > 2 and strong.total_units() + weak.total_units() == 14)

def test_valid_targets():
    source, enemy_territory, neutral = TestTerritory("Source", infantry=10), TestTerritory("Enemy", infantry=5), TestTerritory("Neutral")
    ai, enemy = AI(source, "balanced"), Player(enemy_territory)
    connect(source, enemy_territory)
    connect(source, neutral)
    world = TestMap([source, enemy_territory, neutral])
    check("AI finds valid adjacent attack and expansion targets", "2.10", (True, True), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))
    source.units["infantry"] = 0
    check("AI rejects an empty source", "2.10", (False, False), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))
    source.units["infantry"] = 10
    enemy_territory.attack_cooldown = neutral.attack_cooldown = pygame.time.get_ticks() + 100000
    check("AI rejects targets in cooldown", "2.10", (False, False), (ai.can_attack(world, [enemy]), ai.can_expand(world, [enemy])))

def test_ai_timing():
    ai = CountingAI(TestTerritory("Scheduled", infantry=1), "balanced")
    world = TestMap(ai.territories)
    ai.next_action = pygame.time.get_ticks() + 100000 #next action is far in the future
    ai.update(world, None, [])
    waited = ai.actions == 0
    action_time = pygame.time.get_ticks()
    ai.next_action = action_time #next action is due now
    ai.update(world, None, [])
    check("AI waits for next_action then advances by seven seconds", "2.3", (True, 1, action_time + 7000), (waited, ai.actions, ai.next_action))

def observed_matrix(): #opponent attacks twice then defends, observed after each action
    observer, opponent = AI(TestTerritory("Observer"), "balanced"), Player(TestTerritory("Opponent"))
    observer.observe_opponents([opponent])
    for action in ("attacking", "attacking", "defending"):
        opponent.record_action(action)
        observer.observe_opponents([opponent])
    return observer, observer.opponent_matrices[opponent]

def test_transition_counts():
    observer, matrix = observed_matrix()
    check("Repeated and changed actions update transition counts", "2.13", (6, 6), (matrix["attacking"]["attacking"], matrix["attacking"]["defending"])) #counts start at 5

def test_prediction():
    observer, matrix = observed_matrix()
    prediction = observer.scorer.predict_next_state(matrix, "attacking")
    check("Predictions are normalised and favour observed outcomes", "2.14", (True, True),
          (abs(sum(prediction.values()) - 1) < 1e-9, prediction["attacking"] > prediction["expanding"] and prediction["defending"] > prediction["expanding"]))

def state_scores(predicted_state): #final state scores when the enemy is predicted to follow "attacking" with predicted_state
    source, friend = TestTerritory("Source", infantry=10), TestTerritory("Friend", infantry=10)
    enemy_territory, neutral = TestTerritory("Enemy", infantry=5), TestTerritory("Neutral", infantry=100)
    ai, enemy = AI(source, "balanced"), Player(enemy_territory)
    claim(ai, friend)
    for territory in (friend, enemy_territory, neutral):
        connect(source, territory)
    world = TestMap([source, friend, enemy_territory, neutral])
    enemy.record_action("attacking")
    matrix = ai.scorer.new_transition_matrix()
    matrix["attacking"] = {state: 0 for state in STATES}
    matrix["attacking"][predicted_state] = 100
    ai.opponent_matrices[enemy] = matrix
    recorder = ScoreRecorder()
    ai.scorer.choose_state = recorder.choose_state
    ai.evaluate_state(world, [enemy])
    return recorder.scores

def test_prediction_influence():
    passive, aggressive = state_scores("defending"), state_scores("attacking")
    differences = (passive["attacking"] - aggressive["attacking"], aggressive["defending"] - passive["defending"],
                   passive["expanding"] - aggressive["expanding"], aggressive["reinforcing"] - passive["reinforcing"])
    check("Local and global predictions change relevant scores by 0.25", "2.15", (0.25, 0.25, 0.25, 0.25), rounded(differences))


if __name__ == "__main__":
    test_choose_state()
    test_zero_scores()
    test_state_probabilities()
    test_playstyle_weights()
    test_empty_territory_weights()
    test_territory_score()
    test_bfs_path()
    test_path_bonus()
    test_purchases()
    test_reinforcement()
    test_valid_targets()
    test_ai_timing()
    test_transition_counts()
    test_prediction()
    test_prediction_influence()