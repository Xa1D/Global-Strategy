UNIT_STATS = {
    "infantry": {"attack": 2, "health": 2, "cost": 5, "miss": 0.2, "cooldown": 1},
    "tank": {"attack": 3.4, "health": 5.5, "cost": 10, "miss": 0.15, "cooldown": 2},
    "artillery": {"attack": 7, "health": 4.8, "cost": 15, "miss": 0.1, "cooldown": 1}}
# cooldown shows a unit attacks every N rounds
 
UNIT_VALUE_WEIGHTS = {"infantry": 1.0, "tank": 1.5, "artillery": 2.0}   # used by the AI to compare army strength
 
TARGET_PRIORITY = {                 # which enemy unit types each unit type attacks first
    "artillery": ["tank", "infantry", "artillery"],
    "infantry": ["artillery", "infantry", "tank"],
    "tank": ["infantry", "tank", "artillery"]}
 
ATTACK_COOLDOWN = 9000              # ms a territory cannot be attacked after a fight
COMBAT_SKIP_DELAY = 5000            # ms before the skip button works in the combat panel
COMBAT_FINISH_DELAY = 5000          # ms before combat can be finished
 