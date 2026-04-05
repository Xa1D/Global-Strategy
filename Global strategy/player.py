import random

class Player:
    def __init__(self, country):
        self.country = country 
        self.territories = [country] 
        self.attacking_country = None
        self.defending_country = None
        self.attacking = False
        self.currency = 100
        self.income = 1

    def attack(self,enemy):
        if not self.attacking_country or not self.defending_country:
            return 
        self.attacking = True
        prob = (self.attacking_country.units**1.5) / (self.attacking_country.units**1.5 + self.defending_country.units**1.5)
        chance = random.random()
        lost_units = self.attacking_country.units // 2
        if chance < prob:
            if self.defending_country in enemy.territories:
                enemy.territories.remove(self.defending_country)
            if self.defending_country not in self.territories:
              self.territories.append(self.defending_country)
            self.attacking_country.units = max(1, self.attacking_country.units - self.defending_country.units)
            return "win"
        else:
            self.attacking_country.units = 1
            self.defending_country.units += lost_units
            return "lose"

    def buy_units(self, country, amount=1000):
        if country in self.territories:
            cost = 10
            if self.currency >= cost:
                self.currency -= cost
                country.units += amount

    def money_tick(self):
        self.currency += self.income

    def move_units(self, from_country, to_country, amount):
        if from_country not in self.territories or to_country not in self.territories:
            return False
        if to_country.name not in from_country.neighbours:
            return False
        amount = min(amount, from_country.units - 1)
        if amount <= 0:
            return False
        from_country.units -= amount
        to_country.units += amount
        return True

class AI(Player):
    def __init__(self, country, playstyle):
        super().__init__(country)
        self.playstyle = playstyle