import numpy as np
from combat import VALUE_WEIGHTS
from combat import STATS    
PLAYSTYLE_WEIGHTS = {"aggressive": np.array([0.35, 0.35, 0.15, 0.15]),"defensive":  np.array([0.20, 0.20, 0.25, 0.35]),"balanced":np.array([0.25, 0.25, 0.25, 0.25])}
THREAT_WEIGHTS = (0.4, 0.3, 0.3)
STATES = ["attacking", "expanding", "defending", "reinforcing", "idle"]
BASE_COUNT = 5

def clamp(x):
    return max(0.0, min(1.0, x))

def unit_cost(unit_type):
    return STATS[unit_type]["cost"]

def count_ratio_score(attacker, defender):
    attacker_units = attacker.total_units()
    defender_units = defender.total_units()
    if defender_units <= 0:
        return 1.0
    ratio = attacker_units / defender_units
    return clamp(ratio - 1)

def value_ratio_score(attacker, defender):
    attacker_value = attacker.unit_value(VALUE_WEIGHTS)
    defender_value = defender.unit_value(VALUE_WEIGHTS)
    if defender_value <= 0:
        return 1.0
    ratio = attacker_value / defender_value
    return clamp(ratio - 1)

def connectivity_score(country, world, player, n):
    if n <= 0:
        return 0.0
    friendly_strength = 0
    for name in country.adjacent:
        neighbour = world.countries[name]
        if neighbour in player.territories:
            friendly_strength += neighbour.total_units()
    return clamp(friendly_strength / n)

def threat_score(country, world, enemy, n):
    if n <= 0:
        return 0.0
    enemy_strength = 0
    for name in country.adjacent:
        neighbour = world.countries[name]
        if neighbour in enemy.territories:
            enemy_strength += neighbour.total_units()
    return clamp(1 - (enemy_strength / n))

def get_average_count(player):
    if not player.territories:
        return 1.0
    avg_strength = sum(territory.total_units() for territory in player.territories) / len(player.territories)
    return max(avg_strength, 1.0)

def score_country(attacker, defender, world, player, enemy, playstyle):
    n = get_average_count(player)
    scores = np.array([
        count_ratio_score(attacker, defender),
        value_ratio_score(attacker, defender),
        connectivity_score(attacker, world, player, n),
        threat_score(attacker, world, enemy, n),])
    weights = PLAYSTYLE_WEIGHTS[playstyle]
    return float(weights @ scores)

def unit_strength(player):
    return sum(country.unit_value(VALUE_WEIGHTS) for country in player.territories)

def territory_control(player, world):
    total = len(world.countries)
    if total <= 0:
        return 0.0
    return len(player.territories) / total

def enemy_proximity(player, enemy, world):
    strength = 0
    for territory in player.territories:
        for name in territory.adjacent:
            neighbour = world.countries[name]
            if neighbour in enemy.territories:
                strength += neighbour.unit_value(VALUE_WEIGHTS)
    return strength

def total_map_strength(world):
    return max(sum(c.unit_value(VALUE_WEIGHTS) for c in world.countries.values()), 1.0)

def threat_of_enemy(enemy, player, world, weights=THREAT_WEIGHTS):
    map_strength = total_map_strength(world)
    unit_threat = clamp(unit_strength(enemy) / map_strength)
    control_threat = territory_control(enemy, world)
    proximity = clamp(enemy_proximity(player, enemy, world) / map_strength)
    x1, x2, x3 = weights
    return x1 * unit_threat + x2 * control_threat + x3 * proximity

def max_threat(enemies, player, world, weights=THREAT_WEIGHTS):
    if not enemies:
        return 0.0
    return max(threat_of_enemy(enemy, player, world, weights) for enemy in enemies)

def strength_advantage(player, enemies, world, weights=THREAT_WEIGHTS):
    map_strength = total_map_strength(world)
    my_strength = clamp(unit_strength(player) / map_strength)
    threat = max_threat(enemies, player, world, weights)
    return clamp(0.5 + (my_strength - threat))

def neutral_strength(player, world, enemies):
    seen = set()
    total = 0
    for country in player.territories:
        for name in country.adjacent:
            neighbour = world.countries[name]
            if neighbour in player.territories:
                continue
            if any(neighbour in enemy.territories for enemy in enemies):
                continue
            if neighbour.name in seen:
                continue
            seen.add(neighbour.name)
            total += neighbour.unit_value(VALUE_WEIGHTS)
    return total

def expansion_advantage(player, world, enemies):
    map_strength = total_map_strength(world)
    my_strength = clamp(unit_strength(player) / map_strength)
    neutral_proximity = clamp(neutral_strength(player, world, enemies) / map_strength)
    return clamp(0.5 + (my_strength - neutral_proximity))

def redistribution_score(player):
    territories = player.territories
    if len(territories) < 2:
        return 0.0
    unit_counts = [territory.total_units() for territory in territories]
    average = sum(unit_counts) / len(unit_counts)
    if average <= 0:
        return 0.0
    unit_difference = sum(abs(count - average) for count in unit_counts) / len(unit_counts)
    return clamp(unit_difference / (average + 1))

def reinforcing_score(player):
    imbalance = redistribution_score(player)
    afford_infantry = unit_cost("infantry")
    multiplier = 1.0 if player.currency < afford_infantry * 2 else 0.4
    return clamp(imbalance * multiplier)

def has_neutral_neighbour(player, world, enemies):
    for country in player.territories:
        for name in country.adjacent:
            neighbour = world.countries[name]
            if neighbour in player.territories:
                continue
            if any(neighbour in enemy.territories for enemy in enemies):
                continue
            return True
    return False

def has_enemy_neighbour(player, world, enemies):
    for country in player.territories:
        for name in country.adjacent:
            neighbour = world.countries[name]
            if any(neighbour in enemy.territories for enemy in enemies):
                return True
    return False

def weakest_territory_threat(player, enemies, world):
    n = get_average_count(player)
    best_country, best_threat = None, 2.0 
    for country in player.territories:
        for enemy in enemies:
            t = threat_score(country, world, enemy, n)
            if t < best_threat:
                best_threat = t
                best_country = country
    if best_country is None:
        return None, 1.0
    return best_country, best_threat

def choose_state(state_scores):
    states = list(state_scores.keys())
    scores = np.array([max(state_scores[state], 0.0) for state in states])
    if scores.sum() <= 0:
        return "idle"
    probabilities = scores / scores.sum()
    return str(np.random.choice(states, p=probabilities))

def check_empty_territory(player):
    return any(country.total_units() <= 0 for country in player.territories)

def purchase_priority(player, world, enemies):
    n = get_average_count(player)
    scored = []
    for country in player.territories:
        if country.combat:
            continue
        threat = min((threat_score(country, world, enemy, n) for enemy in enemies), default=1.0)
        danger = 1 - threat
        neutral_adjacent = sum(1 for name in country.adjacent if world.countries[name] not in player.territories
                        and not any(world.countries[name] in enemy.territories for enemy in enemies))
        priority = danger + (0.1 * neutral_adjacent)
        scored.append((priority, country, danger))
    def get_priority(score):
        return score[0]
    scored.sort(key=get_priority, reverse=True)
    return [(country, danger) for priority, country, danger in scored]   

def path_bonus(country, path_countries):
    return 0.15 if country.name in path_countries else 0.0

def new_transition_matrix():
    return {state: {state_2: BASE_COUNT for state_2 in STATES} for state in STATES}

def record_transition(matrix, from_state, to_state):
    if from_state in matrix and to_state in matrix[from_state]:
        matrix[from_state][to_state] += 1

def predict_next_state(matrix, current_state):
    if current_state not in matrix:
        return {state: 1 / len(STATES) for state in STATES}
    row = matrix[current_state]
    total = sum(row.values())
    if total <= 0:
        return {state: 1 / len(STATES) for state in STATES}
    return {state: count / total for state, count in row.items()}

def neighbouring_enemies(player, world, enemies):
    result = []
    for enemy in enemies:
        for country in player.territories:
            if any(world.countries[name] in enemy.territories for name in country.adjacent):
                result.append(enemy)
                break
    return result