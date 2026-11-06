import numpy as np
from combat_config import UNIT_VALUE_WEIGHTS, UNIT_STATS  
from ai_config import PLAYSTYLE_TERRITORY_SCORING_WEIGHTS, PLAYSTYLE_STATE_WEIGHTS, THREAT_SCORING_WEIGHTS, STATES, TRANSITION_BASE_COUNT, PATH_BONUS,  MIN_OBSERVATIONS

class AIScoring:
    def __init__(self,player,playstyle):
        self.player = player
        self.playstyle = playstyle
        
    def clamp(self, x):  #limit score values between 0 and 1
        return max(0.0, min(1.0, x))

    def apply_playstyle_weights(self,state_scores):  #apply playstyle weights to state scores 
        weights = PLAYSTYLE_STATE_WEIGHTS.get(self.playstyle, PLAYSTYLE_STATE_WEIGHTS["balanced"])
        return {state: score * weights.get(state, 1.0) for state, score in state_scores.items()}

    def unit_cost(self,unit_type):
        return UNIT_STATS[unit_type]["cost"]

    def count_ratio_score(self,attacker, defender):
        attacker_units = attacker.total_units()
        defender_units = defender.total_units()
        if defender_units <= 0:
            return 1.0
        ratio = attacker_units / defender_units
        return self.clamp(ratio - 1)

    def value_ratio_score(self,attacker, defender):
        attacker_value = attacker.unit_value(UNIT_VALUE_WEIGHTS)
        defender_value = defender.unit_value(UNIT_VALUE_WEIGHTS)
        if defender_value <= 0:
            return 1.0
        ratio = attacker_value / defender_value
        return self.clamp(ratio - 1)

    def connectivity_score(self,territory, map, player, n):
        if n <= 0:
            return 0.0
        friendly_strength = 0
        for name in territory.adjacent:
            neighbour = map.territories[name]
            if neighbour in player.territories:
                friendly_strength += neighbour.total_units()
        return self.clamp(friendly_strength / n)

    def threat_score(self,territory, map, enemy, n):
        if n <= 0:
            return 0.0
        enemy_strength = 0
        for name in territory.adjacent:
            neighbour = map.territories[name]
            if neighbour in enemy.territories:
                enemy_strength += neighbour.total_units()
        return self.clamp(1 - (enemy_strength / n))

    def get_average_count(self):  #average territory unit count
        if not self.player.territories:
            return 1.0
        avg_strength = sum(territory.total_units() for territory in self.player.territories) / len(self.player.territories)
        return max(avg_strength, 1.0)

    def score_territory(self,attacker, defender, map, enemy):
        n = self.get_average_count()
        scores = np.array([
            self.count_ratio_score(attacker, defender),
            self.value_ratio_score(attacker, defender),
            self.connectivity_score(attacker, map, self.player, n),
            self.threat_score(attacker, map, enemy, n)])
        weights = PLAYSTYLE_TERRITORY_SCORING_WEIGHTS[self.playstyle]
        return float(np.dot(weights, scores))  #calculate dot product between scores and associated weights 

    def unit_strength(self,player):
        return sum(territory.unit_value(UNIT_VALUE_WEIGHTS) for territory in player.territories)

    def territory_control(self, player, map):  #ratio of players territories to total map territories 
        total = len(map.territories)
        if total <= 0:
            return 0.0
        return len(player.territories) / total

    def enemy_proximity(self, enemy, map):  #total neighbouring enemy strength
        strength = 0
        for territory in self.player.territories:
            for name in territory.adjacent:
                neighbour = map.territories[name]
                if neighbour in enemy.territories:
                    strength += neighbour.unit_value(UNIT_VALUE_WEIGHTS)
        return strength

    def total_map_strength(self,map):
        return max(sum(territory.unit_value(UNIT_VALUE_WEIGHTS) for territory in map.territories.values()), 1.0)

    def threat_of_enemy(self,enemy, map, weights=THREAT_SCORING_WEIGHTS):
        map_strength = self.total_map_strength(map)
        unit_threat = self.clamp(self.unit_strength(enemy) / map_strength)
        control_threat = self.territory_control(enemy, map)
        proximity = self.clamp(self.enemy_proximity(enemy, map) / map_strength)
        x1, x2, x3 = weights
        return x1 * unit_threat + x2 * control_threat + x3 * proximity

    def max_enemy_threat(self,enemies, map, weights=THREAT_SCORING_WEIGHTS):
        if not enemies:
            return 0.0
        return max(self.threat_of_enemy(enemy, map, weights) for enemy in enemies)

    def strength_advantage(self, enemies, map, weights=THREAT_SCORING_WEIGHTS):
        map_strength = self.total_map_strength(map)
        strength = self.clamp(self.unit_strength(self.player) / map_strength)
        threat = self.max_enemy_threat(enemies, map, weights)
        return self.clamp(0.5 + (strength - threat))  #calculates difference between strength and maximum threat - no difference leads to score of 0.5

    def neutral_strength(self, map, enemies): #returns total neighbouring neutral territories strength
        seen = set()
        total = 0
        for territory in self.player.territories:
            for name in territory.adjacent:
                neighbour = map.territories[name]
                if neighbour in self.player.territories:
                    continue
                if any(neighbour in enemy.territories for enemy in enemies):
                    continue
                if neighbour.name in seen:
                    continue
                seen.add(neighbour.name)
                total += neighbour.unit_value(UNIT_VALUE_WEIGHTS)
        return total

    def expansion_advantage(self, map, enemies): #similar to strength advantage method but enemy threat replaced with average neighbouring neutral strength
        map_strength = self.total_map_strength(map)
        my_strength = self.clamp(self.unit_strength(self.player) / map_strength)
        neutral_proximity = self.clamp(self.neutral_strength(map, enemies) / map_strength)
        return self.clamp(0.5 + (my_strength - neutral_proximity))

    def redistribution_score(self): #calculates average unit different between owned territories
        territories = self.player.territories
        if len(territories) < 2:
            return 0.0
        unit_counts = [territory.total_units() for territory in territories]
        average = sum(unit_counts) / len(unit_counts)
        if average <= 0:
            return 0.0
        unit_difference = sum(abs(count - average) for count in unit_counts) / len(unit_counts)
        return self.clamp(unit_difference / (average + 1))  #1 added to prevent high redistribution scores with low total units

    def reinforcing_score(self):
        imbalance = self.redistribution_score()
        currency_ratio = self.clamp(self.player.currency / 150)
        multiplier = 1.0 - (0.6 * currency_ratio)
        return self.clamp(imbalance * multiplier)  #calculates score using redistribution score and applying a multiplier based on currency

    def weakest_territory_threat(self, enemies, map):
        n = self.get_average_count()
        best_territory, best_threat = None, 2.0 
        for territory in self.player.territories:
            for enemy in enemies:
                threat = self.threat_score(territory, map, enemy, n)
                if threat < best_threat:
                    best_threat = threat   
                    best_territory = territory  #calculating territory with largest threat 
        if best_territory is None:
            return None, 1.0
        return best_territory, best_threat

    def choose_state(self,state_scores):
        scores = np.array([max(state_scores[state], 0.0) for state in STATES]) #NumPy array of state scores created
        if scores.sum() <= 0:
            return "idle"
        probabilities = scores / scores.sum()  #normalise state scores by dividing each by sum
        rounded_probabilities = [round(float(prob), 2) for prob in probabilities]
        #print(f"Normalised probabilities: {rounded_probabilities}")
        return str(np.random.choice(STATES, p=probabilities))  #returns random choice from state scores using the corresponding probabilities

    def get_empty_territories_ratio(self):  #ratio of empty territories to total owned territories
        total = len(self.player.territories)
        if total == 0:
            return 0
        empty = sum(territory.total_units() <= 0 for territory in self.player.territories)
        empty_ratio = empty / total
        return empty_ratio
    
    def apply_empty_territory_weights(self,ratio,state_scores):
        if ratio <= 0.2:
            weights = [0.7, 0.7, 1.3, 1.3, 1.0]
        else:
            weights = [0.5, 0.5, 2.0, 2.0, 1.0]
        return {state: score * weights[i] for i, (state, score) in enumerate(state_scores.items())}

    def get_priority(self,score):
        return score[0]

    def purchase_priority(self,map, enemies, shifts=None): 
        if shifts is None:
            shifts = {} 
        n = self.get_average_count()
        scored = []
        for territory in self.player.territories:
            if territory.combat:
                continue
            threat = min((self.threat_score(territory, map, enemy, n) for enemy in enemies), default=1.0)
            danger = 1 - threat
            if danger > 0:
                danger = self.clamp(danger + shifts.get(territory,0))
            neutral_adjacent = sum(1 for name in territory.adjacent if map.territories[name] not in self.player.territories
                            and not any(map.territories[name] in enemy.territories for enemy in enemies))
            priority = danger + (0.1 * neutral_adjacent)
            scored.append((priority, territory, danger))
        scored.sort(key=self.get_priority, reverse=True)
        return [(territory, danger) for priority, territory, danger in scored]   

    def path_bonus(self,territory, path_territories): #0.15 score bonus for territories on a selected path to a target
        return PATH_BONUS if territory.name in path_territories else 0.0

    def new_transition_matrix(self):  #creates a nested dictionary representing the transition matrix with each of 5 states as rows and columns
        return {state: {next_state: TRANSITION_BASE_COUNT for next_state in STATES} for state in STATES}

    def record_transition(self,matrix, previous_state, next_state):
        if previous_state in matrix and next_state in matrix[previous_state]:
            matrix[previous_state][next_state] += 1

    def predict_next_state(self,matrix, current_state):
        if current_state not in matrix:
            return {state: 1 / len(STATES) for state in STATES}
        row = matrix[current_state]
        total = sum(row.values())
        if total <= 0:
            return {state: 1 / len(STATES) for state in STATES}  
        return {state: count / total for state, count in row.items()} 

    def transition_probabilities(self,matrix):  #turns the count matrix into a numpy matrix of probabilities, one row per state in the order of STATES
        probabilities = np.zeros((len(STATES), len(STATES)))
        for row, state in enumerate(STATES):
            row_counts = self.predict_next_state(matrix, state)  #normalises the counts in this row
            for column, next_state in enumerate(STATES):
                probabilities[row][column] = row_counts[next_state]
        return probabilities

    def predict_future_state(self,matrix, current_state):
        if current_state not in STATES:
            return {state: 1 / len(STATES) for state in STATES}
        probabilities = self.transition_probabilities(matrix)
        future_states = np.dot(probabilities, probabilities)  #matrix multiplication - multiplying matrix by itself results in probabilities for predicting states 2 moves ahead
        row = future_states[STATES.index(current_state)]
        return {state: float(row[index]) for index, state in enumerate(STATES)}

    def get_observation_count(self,matrix, state):  #number of real transitions seen from this state (the base counts are not observations)
        if state not in matrix:
            return 0
        return sum(matrix[state].values()) - TRANSITION_BASE_COUNT * len(STATES)

    def predict_purchase_states(self,matrix, current_state):  #once minimum observations reached prediction of 2 states ahead used for purchasing
        if self.get_observation_count(matrix, current_state) < MIN_OBSERVATIONS:
            return self.predict_next_state(matrix, current_state)
        return self.predict_future_state(matrix, current_state)
    #purchasing units can help long-term strategising which is why the 2 moves ahead prediction is used here

    def neighbouring_enemies(self, map, enemies): #checking if any neighbouring enemy territories 
        result = []
        for enemy in enemies:
            for territory in self.player.territories:
                if any(map.territories[name] in enemy.territories for name in territory.adjacent):
                    result.append(enemy)
                    break
        return result