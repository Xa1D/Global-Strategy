import random
import pygame
from collections import deque

class Player:
    def __init__(self, country):
        self.country = country 
        self.territories = [country] 
        self.attacking_country = None
        self.defending_country = None
        self.currency = 100
        self.income = 1
        self.last_income_time = pygame.time.get_ticks()

    def attack(self, enemy):
        if self.attacking_country is None or self.defending_country is None:
            return None
        attacker_units = self.attacking_country.units
        defender_units = self.defending_country.units
        probability = (attacker_units ** 1.5) / (attacker_units ** 1.5 + defender_units ** 1.5)
        if random.random() < probability:
            if self.defending_country in enemy.territories:
                enemy.territories.remove(self.defending_country)
            self.territories.append(self.defending_country)
            attacker_loss = defender_units
            self.attacking_country.units = max(1, attacker_units - attacker_loss)
            self.defending_country.units = 1
            cooldown_time = 5000
            current_time = pygame.time.get_ticks()
            self.defending_country.attack_cooldown = current_time + cooldown_time
            return "win"
        else:
            attacker_loss = attacker_units // 2
            defender_loss = defender_units // 4
            self.attacking_country.units = max(1, attacker_units - attacker_loss)
            self.defending_country.units = max(1, defender_units - defender_loss)
            return "lose"

    def buy_units(self, country, amount=10):
        if country in self.territories:
            cost = 10
            if self.currency >= cost:
                self.currency -= cost
                country.units += amount
    
    def update(self):
        self.update_income()
        
    def update_income(self):
        self.income = len(self.territories)
        current_time = pygame.time.get_ticks()
        if current_time - self.last_income_time >= 1000: 
            self.currency += self.income
            self.last_income_time = current_time

    def move_units(self, original_country, selected_country, amount):
        if original_country not in self.territories or selected_country not in self.territories:
            return False
        if selected_country.name not in original_country.neighbours:
            return False
        amount = min(amount, original_country.units - 1)
        if amount <= 0:
            return False
        original_country.units -= amount
        selected_country.units += amount
        return True

class AI(Player):
    def __init__(self, country, playstyle):
        super().__init__(country)
        self.playstyle = playstyle
        self.delay = 4000
        self.targets = ["United Kingdom", "Germany", "France", "Sweden"]
        self.target_country = None
        self.attack_duration = 2000
        self.last_attack = 0
        self.state = "idle"
        self.last_action = pygame.time.get_ticks()

    def bfs_path(start_country, target_country, world):
        queue = deque([start_country])
        visited = set([start_country])
        parent = {}
        while queue:
            current = queue.popleft()
            if current == target_country:
                break
            for neighbour_name in current.neighbours:
                neighbour = world.countries[neighbour_name]
                if neighbour not in visited:
                    visited.add(neighbour)
                    parent[neighbour] = current
                    queue.append(neighbour)
        if target_country != start_country and target_country not in parent:
            return None
        path = []
        current = target_country
        while current != start_country:
            path.append(current)
            current = parent[current]
        path.append(start_country)
        path.reverse()
        return path

    def update_ai(self, world, enemy):
        current_time = pygame.time.get_ticks()
        if self.state == "attacking":
            if current_time - self.last_attack >= self.attack_duration:
                self.attack(enemy)
                self.state = "idle"
                self.attacking_country.combat, self.defending_country.combat = False, False
                self.last_action = current_time 
            return
        if current_time - self.last_action >= self.delay:
            self.send_units(world)
            self.purchase_units()
            self.plan_attack(world)
            self.last_action = current_time

    def simulate_paths(self,world):
        best_path = None
        start = None
        for target in self.targets:
            if target in self.territories:
                self.targets.remove(target)
        for country in self.territories:
          for target in self.targets:
              path = self.bfs_path(country,target,world)
              if path:
                if best_path == None or len(path) < len(best_path):
                    path = best_path
                    start = country

    def plan_attack(self, world):
        best_attack = None
        best_score = -1
        prob = random.random()
        for country in self.territories:
            for name in country.neighbours:
                neighbour = world.countries[name]
                if neighbour not in self.territories and neighbour.attack_cooldown <= pygame.time.get_ticks():
                    if not country.combat and not neighbour.combat:
                        if self.playstyle == "aggressive":
                            if country.units > neighbour.units * 1.2:
                                score = country.units - neighbour.units
                                if score > best_score:
                                    best_score = score
                                    best_attack = (country, neighbour)
                        elif self.playstyle == "defensive":
                            if country.units > neighbour.units * 1.5:
                                score = country.units - neighbour.units
                                if score > best_score:
                                    best_score = score
                                    best_attack = (country, neighbour)
        if best_attack and prob >= 0.15:
            attacker, defender = best_attack
            self.attacking_country, self.defending_country = attacker, defender
            self.state = "attacking"
            self.attacking_country.combat, self.defending_country.combat = True, True
            self.last_attack = pygame.time.get_ticks()

    def send_units(self, world):
        for country in self.territories:
            for neighbour_name in country.neighbours:
                neighbour = world.countries[neighbour_name]
                if neighbour in self.territories and country.units > neighbour.units + 1:
                    amount = (country.units - neighbour.units) // 2
                    super().move_units(country,neighbour,amount)
        
    def purchase_units(self):
        for country in self.territories:
            if self.currency >= 10:
                    self.buy_units(country)