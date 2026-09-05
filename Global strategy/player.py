import pygame
from combat import STATS

class Player:
    def __init__(self, territory):
        self.territory = territory
        territory.owner = self
        self.territories = [territory] 
        self.attacking_territory, self.defending_territory = None, None
        self.currency = 50
        self.income = 1
        self.start_time = pygame.time.get_ticks()
        self.last_income_time = pygame.time.get_ticks()
        self.last_action = "idle"
        self.attacks_made = 0
        self.attacks_won = 0
        self.attacks_lost = 0
        self.units_lost = 0          # units lost while attacking
        self.units_lost_defending = 0  # units lost while being attacked
        self.times_defended = 0        # attacks survived (defender won)
        self.times_conquered = 0       # territories lost to an attack (defender lost)
        self.currency_earned = 0
        self.currency_spent = 0
        self.peak_territories = 1
        self.territories_at_2min = None

    def apply_attack_result(self, result, attacker_units_before, defender_units_before, defender_owner):
        cooldown_time = 9000
        current_time = pygame.time.get_ticks()
        attacker_units_after = self.attacking_territory.total_units()
        defender_units_after = self.defending_territory.total_units()
        self.attacks_made += 1
        self.units_lost += max(attacker_units_before - attacker_units_after, 0)
        if defender_owner:
            defender_owner.units_lost_defending += max(defender_units_before - defender_units_after, 0)
        self.attacking_territory.attack_cooldown = current_time + cooldown_time
        self.defending_territory.attack_cooldown = current_time + cooldown_time
        if result == "attacker":
            self.attacks_won += 1
            if defender_owner:
                defender_owner.times_conquered += 1
                if self.defending_territory in defender_owner.territories:
                    defender_owner.territories.remove(self.defending_territory)
            self.defending_territory.owner = self
            if self.defending_territory not in self.territories:
                self.territories.append(self.defending_territory)
            self.peak_territories = max(self.peak_territories, len(self.territories))
            return "win"
        else:
            self.attacks_lost += 1
            if defender_owner:
                defender_owner.times_defended += 1
            return "lose"
          
    def buy_units(self, territory,type, amount=1):
        if territory in self.territories and not territory.combat:
            cost = STATS[type]["cost"] * amount
            if self.currency >= cost:
                self.currency -= cost
                self.currency_spent += cost
                territory.units[type] = territory.units.get(type, 0) + amount

    def update(self):
        self.update_income()
        
    def update_income(self):
        self.income = len(self.territories)
        current_time = pygame.time.get_ticks()
        if current_time - self.last_income_time >= 1000: 
            self.currency += self.income
            self.currency_earned += self.income
            self.last_income_time = current_time

#moves the amount of units from original to selected territory
#if amount is too great then 1 - territory units is moved from min function
    def move_units(self, original_territory, selected_territory, infantry_amount, tank_amount, artillery_amount):
        if original_territory not in self.territories or selected_territory not in self.territories:
            return False
        if selected_territory.name not in original_territory.adjacent:
            return False
        if infantry_amount + tank_amount + artillery_amount <= 0:
            return False
        original_territory.units["infantry"] -= infantry_amount
        selected_territory.units["infantry"] += infantry_amount
        original_territory.units["tank"] -= tank_amount
        selected_territory.units["tank"] += tank_amount
        original_territory.units["artillery"] -= artillery_amount
        selected_territory.units["artillery"] += artillery_amount
        return True