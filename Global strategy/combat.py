STATS = {"infantry": {"attack": 2, "defense": 2, "health": 3, "cost": 5},
    "tank": {"attack": 2, "defense": 4, "health": 6, "cost": 15},
    "artillery": {"attack": 5, "defense": 1, "health": 2, "cost": 20}}

class Combat:
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender
        self.artillery_priority = ["tank", "infantry","artillery"]
        self.infantry_priority = ["artillery", "infantry","tank"]
        self.tank_priority = ["infantry","tank","artillery"]

    def not_empty(self,player):
        if sum(player.units.values()) <= 0:
            return False
        return True

    def simulate_combat(self):
        while self.not_empty(self.attacker) and self.not_empty(self.defender):
            self.simulate_phase()
        if self.not_empty(self.attacker):
            return "attacker"
        else:
            return "defender"
        
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
        attacker_artillery_damage = self.attacker.units["artillery"] * STATS["artillery"]["attack"]
        defender_artillery_damage = self.defender.units["artillery"] * STATS["artillery"]["attack"]

        self.simulate_damage(self.defender, attacker_artillery_damage, self.artillery_priority)
        self.simulate_damage(self.attacker, defender_artillery_damage, self.artillery_priority)

        attacker_infantry_damage = self.attacker.units["infantry"] * STATS["infantry"]["attack"]
        defender_infantry_damage = self.defender.units["infantry"] * STATS["infantry"]["attack"]

        self.simulate_damage(self.defender, attacker_infantry_damage, self.infantry_priority)
        self.simulate_damage(self.attacker, defender_infantry_damage, self.infantry_priority)

        attacker_tank_damage = self.attacker.units["tank"] * STATS["tank"]["attack"]
        defender_tank_damage = self.defender.units["tank"] * STATS["tank"]["attack"]

        self.simulate_damage(self.defender, attacker_tank_damage, self.tank_priority)
        self.simulate_damage(self.attacker, defender_tank_damage, self.tank_priority)

        

        