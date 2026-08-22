import random

STATS = {"infantry": {"attack": 2,  "health": 2, "cost": 5, "miss": 0.2,"cooldown":1},
    "tank": {"attack": 3.5, "health": 5.5, "cost": 10, "miss": 0.15,"cooldown":2},
    "artillery": {"attack": 7, "health": 4.8, "cost": 15, "miss": 0.1,"cooldown":1}}

VALUE_WEIGHTS = {"infantry": 1.0, "tank": 1.5, "artillery": 2.0}


class Combat:
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender
        self.artillery_priority = ["tank", "infantry","artillery"]
        self.infantry_priority = ["artillery", "infantry","tank"]
        self.tank_priority = ["infantry","tank","artillery"]
        self.combat_log = []
        self.attacker_hp = self.get_hp_counts(self.attacker)
        self.defender_hp = self.get_hp_counts(self.defender)

    def get_hp_counts(self, player):
        hp_counts = {}
        for unit_type, stats in STATS.items():
            count = player.units.get(unit_type, 0)
            hp_counts[unit_type] = [stats["health"]] * count
        return hp_counts

    def units_left(self,player):
        if sum(player.units.values()) <= 0:
            return False
        return True

    def get_unit_counts(self, player):
        return {"infantry": player.units.get("infantry", 0),
            "tank": player.units.get("tank", 0),
            "artillery": player.units.get("artillery", 0)}

    def simulate_combat(self):
        if not self.units_left(self.defender):
            return "attacker"  
        round_number = 1
        while self.units_left(self.attacker) and self.units_left(self.defender): #while both sides still have units loops through the combat rounds
            round = self.simulate_round(round_number)
            self.combat_log.append(round)
            for phase in round["phases"]:
                attacker_alive = self.units_left(self.attacker)
                defender_alive = self.units_left(self.defender)
                if not attacker_alive and not defender_alive:
                    attacker_damage = phase["attacker_damage_dealt"]
                    defender_damage = phase["defender_damage_dealt"]
                    if attacker_damage > defender_damage:
                        return "attacker"
                    elif defender_damage > attacker_damage:
                        return "defender"
                    else:
                        return "defender"
            round_number += 1
        if self.units_left(self.attacker) and not self.units_left(self.defender):
            return "attacker"
        if self.units_left(self.defender) and not self.units_left(self.attacker):
            return "defender"
        
    def get_damage(self,type,count):
        damage = 0
        base_damage = STATS[type]["attack"]
        miss = STATS[type]["miss"]
        for i in range(count):
            if random.random() > miss:
                multiplier = random.uniform(0.75,1.25)
                damage += multiplier * base_damage
        return damage

    def simulate_damage(self, defender, damage, priority, defender_hp):
        damage_list = {}
        for unit_type in priority:
            if damage <= 0:
                break
            units = defender_hp[unit_type]
            while units and damage > 0:
                current_hp = units[0]
                if damage >= current_hp:
                    damage_list[unit_type] = damage_list.get(unit_type,0) + current_hp
                    damage -= current_hp
                    units.pop(0)
                    defender.units[unit_type] -= 1
                else:
                    damage_list[unit_type] = damage_list.get(unit_type, 0) + damage
                    units[0] -= damage
                    damage = 0
        return damage_list

    def get_priority(self,unit_type):
        if unit_type == "artillery":
            return self.artillery_priority
        if unit_type == "infantry":
            return self.infantry_priority
        if unit_type == "tank":
            return self.tank_priority

    def simulate_round(self, round_number):
        attacker_before = self.get_unit_counts(self.attacker)
        defender_before = self.get_unit_counts(self.defender)
        attacker_types = [unit_type for unit_type in STATS if self.attacker.units.get(unit_type, 0) > 0 and (round_number - 1) % STATS[unit_type]["cooldown"] == 0]
        defender_types = [unit_type for unit_type in STATS if self.defender.units.get(unit_type, 0) > 0 and (round_number - 1) % STATS[unit_type]["cooldown"] == 0]
        attacker_attacks = {unit_type: self.get_damage(unit_type,self.attacker.units[unit_type]) for unit_type in attacker_types}
        defender_attacks = {unit_type: self.get_damage(unit_type,self.defender.units[unit_type])for unit_type in defender_types}
        attacker_damage = sum(attacker_attacks.values())
        defender_damage = sum(defender_attacks.values())
        attacker_damage_list = {}
        defender_damage_list = {}
        for unit_type, damage in attacker_attacks.items():
            attacker_damage_list[unit_type] = self.simulate_damage(self.defender,damage,self.get_priority(unit_type),self.defender_hp)
        for unit_type, damage in defender_attacks.items():
            defender_damage_list[unit_type] = self.simulate_damage(self.attacker,damage,self.get_priority(unit_type),self.attacker_hp)
        return {
            "phases": [{
                "attacker_unit_type": attacker_types,
                "defender_unit_type": defender_types,

                "attacker_damage_dealt": attacker_damage,
                "defender_damage_dealt": defender_damage,

                "attacker_breakdowns": attacker_damage_list,
                "defender_breakdowns": defender_damage_list,

                "attacker_before": attacker_before,
                "defender_before": defender_before,

                "attacker_after": self.get_unit_counts(self.attacker),
                "defender_after": self.get_unit_counts(self.defender)}]
            }
