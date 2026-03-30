import random

class Player:
    def __init__(self, country):
        self.country = country 
        self.territories = [country] 
        self.attacking_country = None
        self.defending_country = None
        self.attacking = False

    def attack(self):
        if not self.attacking_country or not self.defending_country:
            return 
        self.attacking = True
        prob = (self.attacking_country.units**1.5) / (self.attacking_country.units**1.5 + self.defending_country.units**1.5)
        chance = random.random()
        if chance < prob:
            self.territories.append(self.defending_country)
            self.defending_country.units = max(1, self.attacking_country.units // 2)  # assign some units to new territory
            self.attacking_country.units = max(1, self.attacking_country.units - self.defending_country.units)
        else:
            self.attacking_country.units = max(1, self.attacking_country.units - self.defending_country.units)
        self.attacking_country = None
        self.defending_country = None
        self.attacking = False

    def buy_units(self, country, amount=1):
        if country in self.territories:
            country.units += amount

class AI:
    def __init__(self):
        self.country = self.country
        self.territories = []
