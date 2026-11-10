import numpy as np

AI_ACTION_DELAY = 7000          # time between AI decisions
AI_ATTACK_DURATION = 6000
SEARCH_TARGET_COUNT = 4                # how many long-term targets the AI considers
PATH_BONUS = 0.15               # score bonus for territories on the planned path
 
RESERVE_START_TIME = 60000      # the AI keeps a currency reserve after this point
RESERVE_FRACTION = 0.15
DANGER_WEIGHT_OFFSET = 0.2      # keeps safe territories from getting a zero budget share
 
STATES = ("attacking", "expanding", "defending", "reinforcing", "idle")   # order matters for the weight tuples below
 
PREDICTION_WEIGHT = 0.25        # how much the predicted enemy behaviour shifts a state score
TRANSITION_BASE_COUNT = 5
MIN_OBSERVATIONS = 5
NEUTRAL_AGGRESSION = 0.4
PURCHASE_PREDICTION_INFLUENCE = 0.35
 
# order: count ratio, value ratio, connectivity, threat
PLAYSTYLE_TERRITORY_SCORING_WEIGHTS = {"aggressive": np.array([0.35, 0.35, 0.15, 0.15]),
                                       "defensive":  np.array([0.20, 0.20, 0.25, 0.35]),
                                       "balanced":np.array([0.25, 0.25, 0.25, 0.25])}
 
PLAYSTYLE_STATE_WEIGHTS = {
    "aggressive": {"attacking": 1.2, "expanding": 1.2, "defending": 0.9, "reinforcing": 0.9, "idle": 0.8},
    "defensive": {"attacking": 0.8, "expanding": 0.8, "defending": 1.2, "reinforcing": 1.2, "idle": 1.0},
    "balanced": {"attacking": 1.0, "expanding": 1.0, "defending": 1.0, "reinforcing": 1.0, "idle": 1.0}}
 
THREAT_SCORING_WEIGHTS = (0.4, 0.3, 0.3)    # unit strength, territory control, proximity
