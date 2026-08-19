from player import Player
import ai_scoring
import pygame
from combat import Combat, VALUE_WEIGHTS

class AI(Player):
    def __init__(self, country, playstyle, offset):
        super().__init__(country)
        self.playstyle = playstyle
        self.delay = 7000
        self.attack_duration = 6000
        self.last_attack = 0
        self.state = "idle"
        self.next_action = pygame.time.get_ticks() + offset
        self.threshold = 0.3 if playstyle == "aggressive" else 0.5
        self.opponent_matrices = {}
        self.last_observed_action = {}

    def observe_opponents(self, enemies):
        for opponent in enemies:
            current_action = opponent.last_action
            if opponent not in self.opponent_matrices:
                self.opponent_matrices[opponent] = ai_scoring.new_transition_matrix()
            last_action = self.last_observed_action.get(opponent)
            if last_action is not None and last_action != current_action:
                print(f"[MARKOV] {self.country.name} observed {opponent.country.name}: {last_action} -> {current_action}")
                ai_scoring.record_transition(self.opponent_matrices[opponent], last_action, current_action)
            self.last_observed_action[opponent] = current_action

    def attack(self):
        if self.attacking_country is None or self.defending_country is None:
            return None
        attacker_before = self.attacking_country.total_units()
        defender_before = self.defending_country.total_units()
        defender_owner = self.defending_country.owner
        battle = Combat(self.attacking_country, self.defending_country)
        result = battle.simulate_combat()
        return self.apply_attack_result(result, attacker_before, defender_before, defender_owner)

    def predicted_local_posture(self, world, enemies):
        local_enemies = ai_scoring.neighbouring_enemies(self, world, enemies)
        if not local_enemies:
            return 0.5, 0.5  # no adjacent enemies, no data - neutral
        passive_total, aggressive_total, count = 0.0, 0.0, 0
        for opponent in local_enemies:
            matrix = self.opponent_matrices.get(opponent)
            if matrix is None:
                continue
            pred = ai_scoring.predict_next_state(matrix, opponent.last_action)
            passive_total += pred.get("defending", 0) + pred.get("reinforcing", 0) + pred.get("idle", 0)
            aggressive_total += pred.get("attacking", 0) + pred.get("expanding", 0)
            count += 1
        if count == 0:
            return 0.5, 0.5
        return passive_total / count, aggressive_total / count

    def predicted_global_posture(self, enemies):
        if not enemies:
            return 0.5, 0.5
        passive_total, aggressive_total, count = 0.0, 0.0, 0
        for opponent in enemies:
            matrix = self.opponent_matrices.get(opponent)
            if matrix is None:
                continue
            pred = ai_scoring.predict_next_state(matrix, opponent.last_action)
            passive_total += pred.get("defending", 0) + pred.get("reinforcing", 0) + pred.get("idle", 0)
            aggressive_total += pred.get("attacking", 0) + pred.get("expanding", 0)
            count += 1
        if count == 0:
            return 0.5, 0.5
        return passive_total / count, aggressive_total / count

    def choose_targets(self, world, count=4):
        candidates = []
        for country in world.countries.values():
            if country in self.territories:
                continue
            value = country.unit_value(VALUE_WEIGHTS) + len(country.adjacent) * 2
            candidates.append((value, country))
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        return [country for _, country in candidates[:count]]

    def search(self, start, target, world):
        queue = [start]
        visited = set([start])
        previous = {}
        path = []
        found = False
        while len(queue) > 0:
            current = queue.pop(0)
            if current == target:
                found = True
                break
            else:
                for name in current.adjacent:
                    neighbour = world.countries[name]
                    if neighbour not in visited:
                        visited.add(neighbour)
                        previous[neighbour] = current
                        queue.append(neighbour)
        if not found:
            return
        current = target
        while current != start:
            path.append(current)
            current = previous[current]
        path.append(start)
        path.reverse()
        return path

    def get_target_path(self, world):
        targets = self.choose_targets(world)
        best_path = None
        for target in targets:
            if target in self.territories:
                continue
            for start in self.territories:
                path = self.search(start, target, world)
                if not path:
                    continue
                if best_path is None or len(path) < len(best_path):
                    best_path = path
        return best_path

    def best_attack_target(self, world, enemy, path_countries ):
        best, best_score = None, -1
        current_time = pygame.time.get_ticks()
        for country in self.territories:
            if country.combat:
                continue
            for name in country.adjacent:
                neighbour = world.countries[name]
                if neighbour not in enemy.territories or neighbour.combat:
                    continue
                if neighbour.attack_cooldown > current_time:
                    continue
                score = ai_scoring.score_country(country, neighbour, world, self, enemy, self.playstyle)
                score += ai_scoring.path_bonus(neighbour, path_countries)
                if score > best_score:
                    best_score = score
                    best = (country, neighbour)
        return best, best_score

    def best_expansion_target(self, world, enemies, path_countries):
        best, best_score = None, -1
        current_time = pygame.time.get_ticks()
        for country in self.territories:
            if country.combat:
                continue
            for name in country.adjacent:
                neighbour = world.countries[name]
                if neighbour in self.territories or neighbour.combat:
                    continue
                if any(neighbour in e.territories for e in enemies):
                    continue  # owned by an enemy, not neutral - that's attacking's job
                if neighbour.attack_cooldown > current_time:
                    continue
                # score against no specific enemy - use a neutral "phantom" comparison:
                # treat threat_score as 1.0 (no enemy adjacency risk from this target)
                score = (ai_scoring.count_ratio_score(country, neighbour) + ai_scoring.value_ratio_score(country, neighbour)) / 2
                score += ai_scoring.path_bonus(neighbour, path_countries)
                if score > best_score:
                    best_score = score
                    best = (country, neighbour)
        return best, best_score

    def update_ai(self, world, player, ai_players):
         current_time = pygame.time.get_ticks()
         enemies = [p for p in ([player] + ai_players) if p is not self]
         if self.state == "attacking":
            if current_time - self.last_attack >= self.attack_duration:
                self.attack()
                self.attacking_country.combat, self.defending_country.combat = False, False
                self.state = "idle"
                self.next_action = current_time + self.delay
            return
         if current_time >= self.next_action:
            self.evaluate_state(world, enemies)
            if self.state != "attacking":
                self.next_action += self.delay 

    def unit_type_mix(self,danger):
        if danger > 0.6:
            return {"tank": 0.6, "artillery": 0.2, "infantry": 0.2}
        elif danger > 0.3:
            return {"artillery": 0.4, "tank": 0.4, "infantry": 0.2}
        else:
            return {"infantry": 0.7, "artillery": 0.3}

    def spend_leftover(self,reserve,country,infantry_cost,tank_cost,artillery_cost):
        while self.currency - reserve >= infantry_cost:
            leftover = self.currency - reserve
            if leftover >= artillery_cost * 3.5:
                amount = int(leftover // artillery_cost)
                self.buy_units(country, "artillery", amount)
            elif leftover >= tank_cost * 2.5:
                amount = int(leftover // tank_cost)
                self.buy_units(country, "tank", amount)
            else:
                amount = int(leftover // infantry_cost)
                self.buy_units(country, "infantry", max(amount, 1))


    def purchase_units(self, world, enemies):
        infantry_cost = ai_scoring.unit_cost("infantry")
        tank_cost = ai_scoring.unit_cost("tank")
        artillery_cost = ai_scoring.unit_cost("artillery")
        scored = ai_scoring.purchase_priority(self,world, enemies)
        if not scored:
            return
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        reserve_fraction = 0.0 if elapsed < 40000 else 0.15
        reserve = self.currency * reserve_fraction
        budget = max(self.currency - reserve, 0)
        if budget <= 0:
            return
        weight_total = sum(0.3 + d for _, d in scored)
        if weight_total <= 0:
            return
        for country, danger in scored:
            if self.currency < infantry_cost:
                break
            share = (0.3 + danger) / weight_total
            country_budget = budget * share
            mix = self.unit_type_mix(danger)
            for unit_type, fraction in mix.items():
                if self.currency < infantry_cost:
                    break
                type_budget = country_budget * fraction
                cost = ai_scoring.unit_cost(unit_type)
                amount = int(type_budget // cost)
                amount = min(amount, self.currency // cost)
                if amount > 0:
                    self.buy_units(country, unit_type, amount)
        top_country = scored[0][0]
        self.spend_leftover(reserve,top_country,infantry_cost,tank_cost,artillery_cost)

    def evaluate_state(self, world, enemies):
        self.observe_opponents(enemies)
        self.purchase_units(world, enemies)
        strength_advantage = ai_scoring.strength_advantage(self, enemies, world)
        expansion_advantage = ai_scoring.expansion_advantage(self, world, enemies)
        can_expand = ai_scoring.has_neutral_neighbour(self, world, enemies) and not ai_scoring.check_empty_territory(self)
        can_attack = ai_scoring.has_enemy_neighbour(self, world, enemies) and not ai_scoring.check_empty_territory(self)
        weak_country, threat = ai_scoring.weakest_territory_threat(self, enemies, world)
        danger = 1 - threat
        can_defend = weak_country is not None and any(world.countries[name] in self.territories for name in weak_country.adjacent)
        can_reinforce = len(self.territories) >= 2
        local_passive, local_aggressive = self.predicted_local_posture(world, enemies)
        global_passive, global_aggressive = self.predicted_global_posture(enemies)
        state_scores = {"attacking": (strength_advantage + local_passive * 0.2) if can_attack else 0.0,
            "expanding": (expansion_advantage + global_passive * 0.15) if can_expand else 0.0,
            "defending": min(danger + local_aggressive * 0.3, 1.0) if can_defend else 0.0,
            "reinforcing": min(ai_scoring.reinforcing_score(self) + global_aggressive * 0.2, 1.0) if can_reinforce else 0.0,
            "idle": 0.1,}
        chosen = ai_scoring.choose_state(state_scores)
        return chosen,weak_country

    def execute_actions(self,state,world,enemies):
        self.purchase_units(world, enemies)
        self.last_action, weak_country = self.evaluate_state(world,enemies)
        path = self.get_target_path(world)
        path_countries = {c.name for c in path} if path else set()
        if state == "attacking":
            pair, _ = self.best_attack_target(world, enemies[0], path_countries)
            if pair:
                self.start_attack(*pair)
                print(f"[ATTACK] state after start_attack: {self.state}")
            else:
                self.state = "idle"
                print("[ATTACK] no pair found, staying idle")
        elif state == "expanding":
            pair, _ = self.best_expansion_target(world, enemies, path_countries)
            print(f"[EXPAND] pair found: {pair is not None}")
            if pair:
                self.start_attack(*pair) 
            else:
                self.state = "idle"
        elif state == "reinforcing":
            self.send_units(world)
            self.state = "idle"
        elif state == "defending":
            if weak_country:
                self.reinforce(weak_country, world)
            self.state = "idle"
        else:
            self.state = "idle"

    def start_attack(self, attacker, defender):
        self.attacking_country, self.defending_country = attacker, defender
        self.state = "attacking"
        attacker.combat, defender.combat = True, True
        self.last_attack = pygame.time.get_ticks()

    def send_units(self, world):
        for country in self.territories:
            if country.combat:
                continue
            for neighbour_name in country.adjacent:
                neighbour = world.countries[neighbour_name]
                if neighbour in self.territories and country.total_units() > neighbour.total_units() + 1:
                    amount = (country.total_units() - neighbour.total_units()) // 2
                    self.split_move(country, neighbour, amount)

    def reinforce(self, target, world):
        if target.combat:
            return
        best_source, best_units = None, -1
        for name in target.adjacent:
            neighbour = world.countries[name]
            if neighbour in self.territories and neighbour.total_units() > best_units:
                best_units = neighbour.total_units()
                best_source = neighbour
        if best_source and best_units > 1:
            amount = best_units // 2
            self.split_move(best_source, target, amount)

    def split_move(self, source, dest, amount):
        total = source.total_units()
        if total <= 0 or amount <= 0:
            return
        infantry = min(source.units.get("infantry", 0), (amount * source.units.get("infantry", 0)) // total)
        tank = min(source.units.get("tank", 0), (amount * source.units.get("tank", 0)) // total)
        artillery = min(source.units.get("artillery", 0), (amount * source.units.get("artillery", 0)) // total)
        super().move_units(source, dest, infantry, tank, artillery)