import pygame
from combat import STATS

class Player:
    def __init__(self, country):
        self.country = country
        country.owner = self
        self.territories = [country] 
        self.attacking_country, self.defending_country = None, None
        self.currency = 50
        self.income = 1
        self.start_time = pygame.time.get_ticks()
        self.last_income_time = pygame.time.get_ticks()
        self.last_action = "idle"
        self.last_order_change = 0
        self.order_cooldown = 20000
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
        attacker_units_after = self.attacking_country.total_units()
        defender_units_after = self.defending_country.total_units()
        self.attacks_made += 1
        self.units_lost += max(attacker_units_before - attacker_units_after, 0)
        if defender_owner:
            defender_owner.units_lost_defending += max(defender_units_before - defender_units_after, 0)
        self.attacking_country.attack_cooldown = current_time + cooldown_time
        self.defending_country.attack_cooldown = current_time + cooldown_time
        if result == "attacker":
            self.attacks_won += 1
            if defender_owner:
                defender_owner.times_conquered += 1
                if self.defending_country in defender_owner.territories:
                    defender_owner.territories.remove(self.defending_country)
            self.defending_country.owner = self
            if self.defending_country not in self.territories:
                self.territories.append(self.defending_country)
            self.peak_territories = max(self.peak_territories, len(self.territories))
            return "win"
        else:
            self.attacks_lost += 1
            if defender_owner:
                defender_owner.times_defended += 1
            return "lose"
          
    def buy_units(self, country,type,amount=1):
        if country in self.territories and not country.combat:
            cost = STATS[type]["cost"] * amount
            if self.currency >= cost:
                self.currency -= cost
                self.currency_spent += cost
                country.units[type] = country.units.get(type, 0) + amount

    def update(self):
        self.update_income()
        
    def update_income(self):
        self.income = len(self.territories)
        current_time = pygame.time.get_ticks()
        if current_time - self.last_income_time >= 1000: 
            self.currency += self.income
            self.currency_earned += self.income
            self.last_income_time = current_time

#moves the amount of units from original to selected country
#if amount is too great then 1 - country units is moved from min function
    def move_units(self, original_country, selected_country, infantry_amount, tank_amount, artillery_amount):
        if original_country not in self.territories or selected_country not in self.territories:
            return False
        if selected_country.name not in original_country.adjacent:
            return False
        if infantry_amount + tank_amount + artillery_amount <= 0:
            return False
        original_country.units["infantry"] -= infantry_amount
        selected_country.units["infantry"] += infantry_amount
        original_country.units["tank"] -= tank_amount
        selected_country.units["tank"] += tank_amount
        original_country.units["artillery"] -= artillery_amount
        selected_country.units["artillery"] += artillery_amount
        return True