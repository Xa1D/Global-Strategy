import random
import pygame

class Player:
    def __init__(self, country):
        self.country = country 
        self.territories = [country] 
        self.attacking_country, self.defending_country = None, None
        self.currency = 50
        self.income = 1
        self.last_income_time = pygame.time.get_ticks()

#based on probability formula on unit ratio
#simple model for unit losses for now (attacker loss = defender units, defender units = 1 in case of victory)
    def attack(self, enemy):
        if self.attacking_country is None or self.defending_country is None:
            return None
        attacker_units = self.attacking_country.units
        defender_units = self.defending_country.units
        probability = (attacker_units ** 1.5) / (attacker_units ** 1.5 + defender_units ** 1.5)
        cooldown_time = 5000
        current_time = pygame.time.get_ticks()
        if random.random() < probability:
            if self.defending_country in enemy.territories:
                enemy.territories.remove(self.defending_country)

            self.territories.append(self.defending_country)
            attacker_loss = defender_units
            self.attacking_country.units = max(1, attacker_units - attacker_loss)
            self.defending_country.units = 1
            self.defending_country.attack_cooldown = current_time + cooldown_time
            return "win"
        else:
            attacker_loss = attacker_units // 2
            defender_loss = defender_units // 4
            self.defending_country.attack_cooldown = current_time + cooldown_time
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

#moves the amount of units from original to selected country
#if amount is too great then 1 - country units is moved from min function
    def move_units(self, original_country, selected_country, amount):
        if original_country not in self.territories or selected_country not in self.territories:
            return False
        if selected_country.name not in original_country.adjacent:
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
        self.delay = 5000
        self.targets = ["United Kingdom", "Germany", "France", "Sweden"]
        self.target_country = None
        self.attack_duration = 2000
        self.last_attack = 0
        self.state = "idle"
        self.last_action = pygame.time.get_ticks()

#starts from the original country and goes through the adjacent countries repeatedly until it has reached a target country
#creates a dictionary with each country it has visited along with the country it visited from
#creates a path from the original country to target country using the previous countries dictionary
    def search(self,start, target, world):
        queue = [start]
        visited = [start]
        previous = {}
        path = []
        while len(queue) > 0:
            current = queue.pop(0)
            if current == target:
                break
            else:
                for name in current.adjacent:
                    neighbour = world.countries[name]
                    if neighbour not in visited:
                        visited.append(neighbour)
                        previous[neighbour] = current
                        queue.append(neighbour)
        current = target
        while current != start:
            path.append(current)
            current = previous[current]
        path.append(start)
        path.reverse()
        return path

#after delay it carries out any attacks and moves and buys units
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

#looping through all owned countries and then getting a path form each country to the target countries
#returning the shortest path to a target country
    def simulate_paths(self,world):
        best_path = None
        for country in self.territories:
          for i in self.targets:
              if i not in self.territories:
                target = world.countries[i]
                path = self.search(country,target,world)
                if path:
                    if best_path == None or len(path) < len(best_path):
                        best_path = path
        return best_path
    
#loops through all owned countries and their adjacent countries which are not owned and evaluates a score
#score is based on unit difference, returns the best score and corresponding attack 
#different thresholds for different ai - simple model for now
    def plan_attack(self, world):
        best_attack = None
        best_score = -1
        prob = random.random()
        for country in self.territories:
            for name in country.adjacent:
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

#loops through owned countries and neighbouring countries
#sends half the unit difference from countries with more units to neighbouring countries with less units
    def send_units(self, world):
        for country in self.territories:
            for neighbour_name in country.adjacent:
                neighbour = world.countries[neighbour_name]
                if neighbour in self.territories and country.units > neighbour.units + 1:
                    amount = (country.units - neighbour.units) // 2
                    super().move_units(country,neighbour,amount)
        
    def purchase_units(self):
        for country in self.territories:
            if self.currency >= 10:
                    self.buy_units(country)