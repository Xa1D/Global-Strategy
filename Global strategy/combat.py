import random

STATS = {"infantry": {"attack": 2,  "health": 3, "cost": 5, "miss": 0.2},
    "tank": {"attack": 2, "health": 6, "cost": 15, "miss": 0.15},
    "artillery": {"attack": 4, "health": 2, "cost": 20, "miss": 0.1}}

VALUE_WEIGHTS = {"infantry": 1.0, "tank": 1.5, "artillery": 2.0}

class Combat:
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender
        self.artillery_priority = ["tank", "infantry","artillery"]
        self.infantry_priority = ["artillery", "infantry","tank"]
        self.tank_priority = ["infantry","tank","artillery"]
        self.combat_log = []

    def units_left(self,player):
        if sum(player.units.values()) <= 0:
            return False
        return True

    def get_unit_counts(self, player):
        return {"infantry": player.units.get("infantry", 0),
            "tank": player.units.get("tank", 0),
            "artillery": player.units.get("artillery", 0)}

    def simulate_combat(self):
        while self.units_left(self.attacker) and self.units_left(self.defender): #while both sides still have units loops through the combat rounds
            self.combat_log.append(self.simulate_round())
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
        self.units_loss = {"infantry":0,"tank":0,"artillery":0}
        for unit in priority:
                if damage <= 0:
                    break
                units = defender.units.get(unit, 0)
                if units > 0:
                    unit_health = STATS[unit]["health"]
                    units_loss = min(units, damage // unit_health)
                    defender.units[unit] -= units_loss
                    damage -= units_loss * unit_health

    def simulate_phase(self,unit_type,priority):
        attacker_before = self.get_unit_counts(self.attacker)
        defender_before = self.get_unit_counts(self.defender)
        attacker_damage = self.get_damage(unit_type, self.attacker.units.get(unit_type, 0))
        defender_damage = self.get_damage(unit_type, self.defender.units.get(unit_type, 0))
        self.simulate_damage(self.defender, attacker_damage, priority)
        self.simulate_damage(self.attacker, defender_damage, priority)
        return {"unit_type": unit_type,
            "attacker_damage_dealt": attacker_damage,
            "defender_damage_dealt": defender_damage,
            "attacker_before": attacker_before,
            "defender_before": defender_before,
            "attacker_after": self.get_unit_counts(self.attacker),
            "defender_after": self.get_unit_counts(self.defender),}
        
#simulating one round
    def simulate_round(self):
        return {"phases": [self.simulate_phase("artillery", self.artillery_priority),
                self.simulate_phase("infantry", self.infantry_priority),
                self.simulate_phase("tank", self.tank_priority)]}       