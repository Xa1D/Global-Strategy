from player import Player
from ai_scoring import AIScoring
import pygame
from combat import Combat, VALUE_WEIGHTS

class AI(Player):
    def __init__(self, territory, playstyle, offset):
        super().__init__(territory)
        self.playstyle = playstyle
        self.delay = 7000
        self.attack_duration = 6000
        self.last_attack = 0
        self.state = "idle"
        self.next_action = pygame.time.get_ticks() + offset
        self.scorer = AIScoring(self,playstyle)
        self.opponent_matrices = {}
        self.last_observed_action = {}

    def observe_opponents(self, enemies):
        for opponent in enemies:
            current_action = opponent.last_action
            if opponent not in self.opponent_matrices:
                self.opponent_matrices[opponent] = self.scorer.new_transition_matrix()
            last_action = self.last_observed_action.get(opponent)
            if last_action is not None and last_action != current_action:
                print(f"[MARKOV] {self.territory.name} observed {opponent.territory.name}: {last_action} -> {current_action}")
                self.scorer.record_transition(self.opponent_matrices[opponent], last_action, current_action)
            self.last_observed_action[opponent] = current_action

    def attack(self):
        if self.attacking_territory is None or self.defending_territory is None:
            return None
        attacker_before = self.attacking_territory.total_units()
        defender_before = self.defending_territory.total_units()
        defender_owner = self.defending_territory.owner
        battle = Combat(self.attacking_territory, self.defending_territory)
        result = battle.simulate_combat()
        return self.apply_attack_result(result, attacker_before, defender_before, defender_owner)

    def predicted_local_states(self, world, enemies):
        neighbouring_enemies = self.scorer.neighbouring_enemies(world, enemies)
        if not neighbouring_enemies:
            return 0.5, 0.5 
        passive_total, aggressive_total, count = 0.0, 0.0, 0
        for opponent in neighbouring_enemies:
            matrix = self.opponent_matrices.get(opponent)
            if matrix is None:
                continue
            predicted_state = self.scorer.predict_next_state(matrix, opponent.last_action)
            passive_total += predicted_state.get("defending", 0) + predicted_state.get("reinforcing", 0) + predicted_state.get("idle", 0)
            aggressive_total += predicted_state.get("attacking", 0) + predicted_state.get("expanding", 0)
            count += 1
        if count == 0:
            return 0.5, 0.5
        return passive_total / count, aggressive_total / count

    def predicted_global_states(self, enemies):
        if not enemies:
            return 0.5, 0.5
        passive_total, aggressive_total, count = 0.0, 0.0, 0
        for opponent in enemies:
            matrix = self.opponent_matrices.get(opponent)
            if matrix is None:
                continue
            predicted_state = self.scorer.predict_next_state(matrix, opponent.last_action)
            passive_total += predicted_state.get("defending", 0) + predicted_state.get("reinforcing", 0) + predicted_state.get("idle", 0)
            aggressive_total += predicted_state.get("attacking", 0) + predicted_state.get("expanding", 0)
            count += 1
        if count == 0:
            return 0.5, 0.5
        return passive_total / count, aggressive_total / count

    def get_target_value(self,pair):
        return pair[0]

    def choose_targets(self, world, count=4):
        targets = []
        for territory in world.territories.values():
            if territory in self.territories:
                continue
            value = territory.unit_value(VALUE_WEIGHTS) + len(territory.adjacent) * 2
            targets.append((value, territory))
        targets.sort(key=self.get_target_value, reverse=True)
        return [territory for value, territory in targets[:count]]

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
                    neighbour = world.territories[name]
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

    def best_attack_target(self, world, enemies, path_territories):
        best, best_score = None, -1
        current_time = pygame.time.get_ticks()
        for territory in self.territories:
            if territory.combat:
                continue
            for name in territory.adjacent:
                neighbour = world.territories[name]
                owner = None
                for enemy in enemies:
                    if neighbour in enemy.territories:
                        owner = enemy
                        break
                if owner is None or neighbour.combat:
                    continue
                if neighbour.attack_cooldown > current_time:
                    continue
                score = self.scorer.score_territory(territory, neighbour, world, owner)
                score += self.scorer.path_bonus(neighbour, path_territories)
                if score > best_score:
                    best_score = score
                    best = (territory, neighbour)
        return best, best_score

    def best_expansion_target(self, world, enemies, path_territories):
        best, best_score = None, -1
        current_time = pygame.time.get_ticks()
        for territory in self.territories:
            if territory.combat:
                continue
            for name in territory.adjacent:
                neighbour = world.territories[name]
                if neighbour in self.territories or neighbour.combat:
                    continue
                if any(neighbour in enemy.territories for enemy in enemies):
                    continue  
                if neighbour.attack_cooldown > current_time:
                    continue
                score = (self.scorer.count_ratio_score(territory, neighbour) + self.scorer.value_ratio_score(territory, neighbour)) / 2
                score += self.scorer.path_bonus(neighbour, path_territories)
                if score > best_score:
                    best_score = score
                    best = (territory, neighbour)
        return best, best_score

    def update_ai(self, world, player, ai_players):
        if not self.territories:
            return
        current_time = pygame.time.get_ticks()
        enemies = [enemy for enemy in ([player] + ai_players) if enemy is not self]
        if self.state == "attacking":
            if current_time - self.last_attack >= self.attack_duration:
                self.attack()
                self.attacking_territory.combat, self.defending_territory.combat = False, False
                self.state = "idle"
                self.next_action = current_time + self.delay
            return
        if current_time >= self.next_action:
            self.execute_actions(world, enemies)
            if self.state != "attacking":
                self.next_action += self.delay 

    def unit_type_mix(self,danger):
        if danger > 0.6:
            return {"tank": 0.6, "artillery": 0.2, "infantry": 0.2}
        elif danger > 0.3:
            return {"artillery": 0.4, "tank": 0.4, "infantry": 0.2}
        else:
            return {"infantry": 0.7, "artillery": 0.3}

    def spend_leftover(self,reserve,scored,infantry_cost,tank_cost,artillery_cost):
        if not scored:
            return
        top_territories = [territory for territory, danger in scored[:5]]
        leftover = self.currency - reserve
        if leftover < infantry_cost:
            return
        share = leftover / len(top_territories)
        for territory in top_territories:
            if self.currency - reserve < infantry_cost:
                break
            territory_share = min(share, self.currency - reserve)
            if territory_share >= artillery_cost * 3:
                amount = int(territory_share // artillery_cost)
                self.buy_units(territory, "artillery", amount)
            elif territory_share >= tank_cost * 2:
                amount = int(territory_share // tank_cost)
                self.buy_units(territory, "tank", amount)
            else:
                amount = int(territory_share // infantry_cost)
                if amount > 0:
                    self.buy_units(territory, "infantry", amount)
        remaining = self.currency - reserve
        if remaining >= infantry_cost:
            amount = int(remaining // infantry_cost)
            self.buy_units(top_territories[0], "infantry", amount)


    def purchase_units(self, world, enemies):
        infantry_cost = self.scorer.unit_cost("infantry")
        tank_cost = self.scorer.unit_cost("tank")
        artillery_cost = self.scorer.unit_cost("artillery")
        scored = self.scorer.purchase_priority(world, enemies)
        if not scored:
            return
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        reserve_fraction = 0.0 if elapsed < 60000 else 0.15
        reserve = self.currency * reserve_fraction
        budget = max(self.currency - reserve, 0)
        if budget <= 0:
            return
        weight_total = sum(0.2 + danger for territory, danger in scored)
        if weight_total <= 0:
            return
        for territory, danger in scored:
            if self.currency < infantry_cost:
                break
            share = (0.2 + danger) / weight_total
            territory_budget = budget * share
            mix = self.unit_type_mix(danger)
            for unit_type, fraction in mix.items():
                if self.currency < infantry_cost:
                    break
                type_budget = territory_budget * fraction
                cost = self.scorer.unit_cost(unit_type)
                amount = int(type_budget // cost)
                amount = min(amount, self.currency // cost)
                if amount > 0:
                    self.buy_units(territory, unit_type, amount)
        self.spend_leftover(reserve,scored,infantry_cost,tank_cost,artillery_cost)

    def evaluate_state(self, world, enemies):
        self.observe_opponents(enemies)
        strength_advantage = self.scorer.strength_advantage(enemies, world)
        expansion_advantage = self.scorer.expansion_advantage(world, enemies)
        can_expand = self.scorer.has_neutral_neighbour(world, enemies) and not self.scorer.check_empty_territory()
        can_attack = self.scorer.has_enemy_neighbour(world, enemies) and not self.scorer.check_empty_territory()
        weak_territory, threat = self.scorer.weakest_territory_threat(enemies, world)
        danger = 1 - threat
        can_defend = weak_territory is not None and any(world.territories[name] in self.territories for name in weak_territory.adjacent)
        can_reinforce = len(self.territories) >= 2
        local_passive, local_aggressive = self.predicted_local_states(world, enemies)
        global_passive, global_aggressive = self.predicted_global_states(enemies)
        state_scores = {
            "attacking": min(strength_advantage + local_passive * 0.25, 1.0) if can_attack else 0.0,
            "expanding": min(expansion_advantage + global_passive * 0.25, 1.0) if can_expand else 0.0,
            "defending": min(danger + local_aggressive * 0.25, 1.0) if can_defend else 0.0,
            "reinforcing": min(self.scorer.reinforcing_score() + global_aggressive * 0.25, 1.0) if can_reinforce else 0.0,
            "idle": 0.1,
            }
        state_scores = self.scorer.apply_playstyle_weights(state_scores)
        chosen = self.scorer.choose_state(state_scores)
        print(f"{state_scores} chosen state: {chosen}")
        return chosen,weak_territory

    def execute_actions(self,world,enemies):
        self.purchase_units(world, enemies)
        state, weak_territory = self.evaluate_state(world,enemies)
        self.last_action = state
        path = self.get_target_path(world)
        path_territories = {territory.name for territory in path} if path else set()
        if state == "attacking":
            pair, _ = self.best_attack_target(world, enemies, path_territories)
            if pair:
                self.start_attack(pair[0],pair[1])
                print(f"[ATTACK] state after start_attack: {self.state}")
            else:
                self.state = "idle"
                print("[ATTACK] no pair found, staying idle")
        elif state == "expanding":
            pair, _ = self.best_expansion_target(world, enemies, path_territories)
            print(f"[EXPAND] pair found: {pair is not None}")
            if pair:
                self.start_attack(pair[0],pair[1]) 
            else:
                self.state = "idle"
        elif state == "reinforcing":
            self.reinforce(world)
            self.state = "idle"
        elif state == "defending":
            if weak_territory:
                self.defend(weak_territory, world)
            self.state = "idle"
        else:
            self.state = "idle"

    def start_attack(self, attacker, defender):
        self.attacking_territory, self.defending_territory = attacker, defender
        self.state = "attacking"
        attacker.combat, defender.combat = True, True
        self.last_attack = pygame.time.get_ticks()

    def reinforce(self, world):
        for territory in self.territories:
            if territory.combat:
                continue
            for neighbour_name in territory.adjacent:
                neighbour = world.territories[neighbour_name]
                if neighbour in self.territories and territory.total_units() > neighbour.total_units() + 1:
                    amount = (territory.total_units() - neighbour.total_units()) // 2
                    self.move_units(territory, neighbour, amount)

    def defend(self, target, world):
        if target.combat:
            return
        best_source, best_units = None, -1
        for name in target.adjacent:
            neighbour = world.territories[name] 
            if neighbour in self.territories and neighbour.total_units() > best_units:
                best_units = neighbour.total_units()
                best_source = neighbour
        if best_source and best_units > 1:
            amount = best_units // 2
            self.move_units(best_source, target, amount)

    def move_units(self, original_territory, selected_territory, amount):
        total = original_territory.total_units()
        if total <= 0 or amount <= 0:
            return
        infantry = min(original_territory.units.get("infantry", 0), (amount * original_territory.units.get("infantry", 0)) // total)
        tank = min(original_territory.units.get("tank", 0), (amount * original_territory.units.get("tank", 0)) // total)
        artillery = min(original_territory.units.get("artillery", 0), (amount * original_territory.units.get("artillery", 0)) // total)
        super().move_units(original_territory, selected_territory, infantry, tank, artillery)