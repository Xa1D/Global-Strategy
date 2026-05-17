import random

STATS = {"infantry": {"attack": 2, "defense": 2, "health": 3, "cost": 5, "miss": 0.2},
    "tank": {"attack": 2, "defense": 4, "health": 6, "cost": 15, "miss": 0.15},
    "artillery": {"attack": 4, "defense": 1, "health": 2, "cost": 20, "miss": 0.1}}

class Combat:
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender
        self.artillery_priority = ["tank", "infantry","artillery"]
        self.infantry_priority = ["artillery", "infantry","tank"]
        self.tank_priority = ["infantry","tank","artillery"]

    def units_left(self,player):
        if sum(player.units.values()) <= 0:
            return False
        return True

    def simulate_combat(self):
        while self.units_left(self.attacker) and self.units_left(self.defender):
            self.simulate_phase()
        if self.units_left(self.attacker):
            return "attacker"
        else:
            return "defender"
        
    def get_damage(self,type,count):
        damage = 0
        base_damage = STATS[type]["attack"]
        miss = STATS[type]["miss"]
        for i in range(count):
            if random.random() > miss:
                multiplier = random.uniform(0.75,1.25)
                damage += multiplier * base_damage
        return int(damage)
        
    def simulate_damage(self,defender,damage,priority):
        for unit in priority:
                if damage <= 0:
                    break
                units = defender.units.get(unit, 0)
                if units > 0:
                    unit_health = STATS[unit]["health"]
                    units_loss = min(units, damage // unit_health)
                    defender.units[unit] -= units_loss
                    damage -= units_loss * unit_health
        

    def simulate_phase(self):
        attacker_artillery_damage = self.get_damage("artillery",self.attacker.units["artillery"])
        defender_artillery_damage = self.get_damage("artillery",self.defender.units["artillery"])

        self.simulate_damage(self.defender, attacker_artillery_damage, self.artillery_priority)
        self.simulate_damage(self.attacker, defender_artillery_damage, self.artillery_priority)
        
        attacker_infantry_damage = self.get_damage("infantry", self.attacker.units["infantry"])
        defender_infantry_damage = self.get_damage("infantry", self.defender.units["infantry"])

        self.simulate_damage(self.defender, attacker_infantry_damage, self.infantry_priority)
        self.simulate_damage(self.attacker, defender_infantry_damage, self.infantry_priority)

        attacker_tank_damage = self.get_damage("tank", self.attacker.units["tank"])
        defender_tank_damage = self.get_damage("tank", self.defender.units["tank"])


        self.simulate_damage(self.defender, attacker_tank_damage, self.tank_priority)
        self.simulate_damage(self.attacker, defender_tank_damage, self.tank_priority)

        

        