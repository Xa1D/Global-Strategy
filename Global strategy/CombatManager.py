import pygame
from combat import Combat

class CombatManager:
    def __init__(self, player, ui):
        self.player = player
        self.ui = ui
        self.map = None
        self.combat_finished = False
        self.incoming_attack = None
        self.combat_log = []
        self.round = 0
        self.max_round = 0
        self.pending_result = None
        self.pending_attacker_before = 0
        self.pending_defender_before = 0
        self.pending_defender_owner = None
        self.combat_start_time = 0
        self.skip_delay, self.finish_delay = 5000, 5000

    def enter_attack(self, selected_territory, attacking_territory, state, map):
        if selected_territory in self.player.territories:
            attacking_territory = selected_territory
            state = "select_attack"
            self.ui.highlight_attack(attacking_territory, map, self.player)
        return state, attacking_territory

    def handle_attack(self, clicked_territory, attacking_territory, state, map):
        if not attacking_territory:
            return state, attacking_territory

        if clicked_territory.name not in attacking_territory.adjacent:
            return state, attacking_territory

        if clicked_territory in self.player.territories:
            return state, attacking_territory

        if clicked_territory.combat or attacking_territory.combat:
            return state, attacking_territory

        current_time = pygame.time.get_ticks()
        if current_time < clicked_territory.attack_cooldown:
            self.ui.show_message("Cannot attack - territory is on cooldown")
            return state, attacking_territory

        if attacking_territory.total_units() <= 0:
            self.ui.show_message("No units to attack with")
            return state, attacking_territory
        
        self.player.attacking_territory, self.player.defending_territory = attacking_territory, clicked_territory
        self.player.last_action = "attacking"
        self.pending_attacker_before = attacking_territory.total_units()
        self.pending_defender_before = clicked_territory.total_units()
        self.pending_defender_owner = clicked_territory.owner
        battle = Combat(attacking_territory, clicked_territory)
        self.pending_result = battle.simulate_combat()
        self.combat_start_time = pygame.time.get_ticks()
        self.combat_log = battle.combat_log
        self.max_round = len(self.combat_log)
        self.round = 1
        self.incoming_attack = (attacking_territory, clicked_territory)
        attacking_territory.combat, clicked_territory.combat = True, True
        self.map = map
        self.ui.remove_highlight(map)
        state = "attacking"
        attacking_territory = None
        self.refresh_panel()
        return state, attacking_territory
        return state, attacking_territory

    def refresh_panel(self):
        current_time = pygame.time.get_ticks()
        can_skip = (current_time - self.combat_start_time) >= self.skip_delay
        can_finish = (current_time - self.combat_start_time) >= self.finish_delay
        is_last_round = self.round >= self.max_round
        result_text = None
        if is_last_round:
            result_text = "Victory" if self.pending_result == "attacker" else "Defeat"
        self.ui.open_combat_panel(self.combat_log, self.round, self.max_round, self.next_round, self.skip_combat, can_skip, can_finish, is_last_round, result_text)

    def next_round(self):
        if self.round < self.max_round:
            self.round += 1
            self.refresh_panel()
        else:
            self.finish_combat()

    def skip_combat(self):
        self.round = self.max_round

    def finish_combat(self):
        self.ui.close_panel()
        self.player.apply_attack_result(self.pending_result, self.pending_attacker_before, self.pending_defender_before, self.pending_defender_owner)
        self.player.attacking_territory = None
        self.player.defending_territory = None
        if self.incoming_attack:
            self.incoming_attack[0].combat = False
            self.incoming_attack[1].combat = False
        if self.map:
            self.ui.remove_highlight(self.map)
        self.incoming_attack = None
        self.combat_finished = True

    def update(self, state):
        if self.combat_finished:
            self.combat_finished = False
            state = "play"
        if state != "attacking":  #prevent refresh panel being called when not in combat
            return state
        self.refresh_panel()
        return state