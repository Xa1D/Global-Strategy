import numpy as np
from combat import VALUE_WEIGHTS
from combat import STATS    

PLAYSTYLE_SCORING_WEIGHTS = {"aggressive": np.array([0.35, 0.35, 0.15, 0.15]),"defensive":  np.array([0.20, 0.20, 0.25, 0.35]),"balanced":np.array([0.25, 0.25, 0.25, 0.25])}
PLAYSTYLE_STATE_WEIGHTS = {"aggressive": {"attacking": 1.2, "expanding": 1.2, "defending": 0.9, "reinforcing": 0.9, "idle": 0.8},
    "defensive": {"attacking": 0.8, "expanding": 0.8, "defending": 1.2, "reinforcing": 1.2, "idle": 1.0},
    "balanced": {"attacking": 1.0, "expanding": 1.0, "defending": 1.0, "reinforcing": 1.0, "idle": 1.0}}
THREAT_WEIGHTS = (0.4, 0.3, 0.3)

STATES = ["attacking", "expanding", "defending", "reinforcing", "idle"]
BASE_COUNT = 5

class AIScoring:
    def __init__(self,player,playstyle):
        self.player = player
        self.playstyle = playstyle
        
    def clamp(self, x):
        return max(0.0, min(1.0, x))

    def apply_playstyle_weights(self,state_scores):
        weights = PLAYSTYLE_STATE_WEIGHTS.get(self.playstyle, PLAYSTYLE_STATE_WEIGHTS["balanced"])
        return {state: score * weights.get(state, 1.0) for state, score in state_scores.items()}

    def unit_cost(self,unit_type):
        return STATS[unit_type]["cost"]

    def count_ratio_score(self,attacker, defender):
        attacker_units = attacker.total_units()
        defender_units = defender.total_units()
        if defender_units <= 0:
            return 1.0
        ratio = attacker_units / defender_units
        return self.clamp(ratio - 1)

    def value_ratio_score(self,attacker, defender):
        attacker_value = attacker.unit_value(VALUE_WEIGHTS)
        defender_value = defender.unit_value(VALUE_WEIGHTS)
        if defender_value <= 0:
            return 1.0
        ratio = attacker_value / defender_value
        return self.clamp(ratio - 1)

    def connectivity_score(self,territory, world, player, n):
        if n <= 0:
            return 0.0
        friendly_strength = 0
        for name in territory.adjacent:
            neighbour = world.territories[name]
            if neighbour in player.territories:
                friendly_strength += neighbour.total_units()
        return self.clamp(friendly_strength / n)

    def threat_score(self,territory, world, enemy, n):
        if n <= 0:
            return 0.0
        enemy_strength = 0
        for name in territory.adjacent:
            neighbour = world.territories[name]
            if neighbour in enemy.territories:
                enemy_strength += neighbour.total_units()
        return self.clamp(1 - (enemy_strength / n))

    def get_average_count(self):
        if not self.player.territories:
            return 1.0
        avg_strength = sum(territory.total_units() for territory in self.player.territories) / len(self.player.territories)
        return max(avg_strength, 1.0)

    def score_territory(self,attacker, defender, world, enemy):
        n = self.get_average_count()
        scores = np.array([
            self.count_ratio_score(attacker, defender),
            self.value_ratio_score(attacker, defender),
            self.connectivity_score(attacker, world, self.player, n),
            self.threat_score(attacker, world, enemy, n),])
        weights = PLAYSTYLE_SCORING_WEIGHTS[self.playstyle]
        return float(weights @ scores)

    def unit_strength(self,player):
        return sum(territory.unit_value(VALUE_WEIGHTS) for territory in player.territories)

    def territory_control(self,player,world):
        total = len(world.territories)
        if total <= 0:
            return 0.0
        return len(player.territories) / total

    def enemy_proximity(self, enemy, world):
        strength = 0
        for territory in self.player.territories:
            for name in territory.adjacent:
                neighbour = world.territories[name]
                if neighbour in enemy.territories:
                    strength += neighbour.unit_value(VALUE_WEIGHTS)
        return strength

    def total_map_strength(self,world):
        return max(sum(c.unit_value(VALUE_WEIGHTS) for c in world.territories.values()), 1.0)

    def threat_of_enemy(self,enemy, world, weights=THREAT_WEIGHTS):
        map_strength = self.total_map_strength(world)
        unit_threat = self.clamp(self.unit_strength(enemy) / map_strength)
        control_threat = self.territory_control(enemy, world)
        proximity = self.clamp(self.enemy_proximity(enemy, world) / map_strength)
        x1, x2, x3 = weights
        return x1 * unit_threat + x2 * control_threat + x3 * proximity

    def max_threat(self,enemies, world, weights=THREAT_WEIGHTS):
        if not enemies:
            return 0.0
        return max(self.threat_of_enemy(enemy, world, weights) for enemy in enemies)

    def strength_advantage(self, enemies, world, weights=THREAT_WEIGHTS):
        map_strength = self.total_map_strength(world)
        my_strength = self.clamp(self.unit_strength(self.player) / map_strength)
        threat = self.max_threat(enemies, world, weights)
        return self.clamp(0.5 + (my_strength - threat))

    def neutral_strength(self, world, enemies):
        seen = set()
        total = 0
        for territory in self.player.territories:
            for name in territory.adjacent:
                neighbour = world.territories[name]
                if neighbour in self.player.territories:
                    continue
                if any(neighbour in enemy.territories for enemy in enemies):
                    continue
                if neighbour.name in seen:
                    continue
                seen.add(neighbour.name)
                total += neighbour.unit_value(VALUE_WEIGHTS)
        return total

    def expansion_advantage(self, world, enemies):
        map_strength = self.total_map_strength(world)
        my_strength = self.clamp(self.unit_strength(self.player) / map_strength)
        neutral_proximity = self.clamp(self.neutral_strength(world, enemies) / map_strength)
        return self.clamp(0.5 + (my_strength - neutral_proximity))

    def redistribution_score(self):
        territories = self.player.territories
        if len(territories) < 2:
            return 0.0
        unit_counts = [territory.total_units() for territory in territories]
        average = sum(unit_counts) / len(unit_counts)
        if average <= 0:
            return 0.0
        unit_difference = sum(abs(count - average) for count in unit_counts) / len(unit_counts)
        return self.clamp(unit_difference / (average + 1))

    def reinforcing_score(self):
        imbalance = self.redistribution_score()
        afford_infantry = self.unit_cost("infantry")
        multiplier = 1.0 if self.player.currency < afford_infantry * 2 else 0.4
        return self.clamp(imbalance * multiplier)

    def has_neutral_neighbour(self, world, enemies):
        for territory in self.player.territories:
            for name in territory.adjacent:
                neighbour = world.territories[name]
                if neighbour in self.player.territories:
                    continue
                if any(neighbour in enemy.territories for enemy in enemies):
                    continue
                return True
        return False

    def has_enemy_neighbour(self, world, enemies):
        for territory in self.player.territories:
            for name in territory.adjacent:
                neighbour = world.territories[name]
                if any(neighbour in enemy.territories for enemy in enemies):
                    return True
        return False

    def weakest_territory_threat(self, enemies, world):
        n = self.get_average_count()
        best_territory, best_threat = None, 2.0 
        for territory in self.player.territories:
            for enemy in enemies:
                t = self.threat_score(territory, world, enemy, n)
                if t < best_threat:
                    best_threat = t
                    best_territory = territory
        if best_territory is None:
            return None, 1.0
        return best_territory, best_threat

    def choose_state(self,state_scores):
        states = list(state_scores.keys())
        scores = np.array([max(state_scores[state], 0.0) for state in states])
        if scores.sum() <= 0:
            return "idle"
        probabilities = scores / scores.sum()
        return str(np.random.choice(states, p=probabilities))

    def check_empty_territory(self):
        return any(territory.total_units() <= 0 for territory in self.player.territories)

    def get_priority(self,score):
        return score[0]

    def purchase_priority(self,world, enemies):
        n = self.get_average_count()
        scored = []
        for territory in self.player.territories:
            if territory.combat:
                continue
            threat = min((self.threat_score(territory, world, enemy, n) for enemy in enemies), default=1.0)
            danger = 1 - threat
            neutral_adjacent = sum(1 for name in territory.adjacent if world.territories[name] not in self.player.territories
                            and not any(world.territories[name] in enemy.territories for enemy in enemies))
            priority = danger + (0.1 * neutral_adjacent)
            scored.append((priority, territory, danger))
        scored.sort(key=self.get_priority, reverse=True)
        return [(territory, danger) for priority, territory, danger in scored]   

    def path_bonus(self,territory, path_territories):
        return 0.15 if territory.name in path_territories else 0.0

    def new_transition_matrix(self):
        return {state: {state_2: BASE_COUNT for state_2 in STATES} for state in STATES}

    def record_transition(self,matrix, from_state, to_state):
        if from_state in matrix and to_state in matrix[from_state]:
            matrix[from_state][to_state] += 1

    def predict_next_state(self,matrix, current_state):
        if current_state not in matrix:
            return {state: 1 / len(STATES) for state in STATES}
        row = matrix[current_state]
        total = sum(row.values())
        if total <= 0:
            return {state: 1 / len(STATES) for state in STATES}
        return {state: count / total for state, count in row.items()}

    def neighbouring_enemies(self, world, enemies):
        result = []
        for enemy in enemies:
            for territory in self.player.territories:
                if any(world.territories[name] in enemy.territories for name in territory.adjacent):
                    result.append(enemy)
                    break
        return result