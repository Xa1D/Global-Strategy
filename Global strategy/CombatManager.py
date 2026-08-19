import pygame
from combat import Combat

class CombatManager:
    def __init__(self, game):
        self.game = game
        self.incoming_attack = None
        self.attack_result, self.result_start_time, self.result_duration = None, 0, 2000
        self.combat_log = []
        self.round = 1
        self.max_round = 0
        self.pending_result = None
        self.pending_attacker_before = 0
        self.pending_defender_before = 0
        self.pending_defender_owner = None
        self.combat_start_time = 0
        self.skip_delay = 5000

    def enter_attack(self):
        if self.game.selected_country in self.game.player.territories:
            self.game.state = "select_attack"
            self.game.attacking_country = self.game.selected_country
            self.game.UI.highlight_attack(self.game.attacking_country, self.game.map, self.game.player)
            self.game.UI.update_sidebar(self.game.selected_country, self.game.player, self.game.update_unit_panel, self.enter_attack, self.game.move_manager.enter_move)

    def handle_attack(self, clicked_country):
        attacking_country = self.game.attacking_country
        if attacking_country:
            if clicked_country.name in attacking_country.adjacent:
                if clicked_country not in self.game.player.territories and not clicked_country.combat and not attacking_country.combat:
                    current_time = pygame.time.get_ticks()
                    if current_time < clicked_country.attack_cooldown:
                        return
                    self.game.player.attacking_country, self.game.player.defending_country = attacking_country, clicked_country
                    self.game.player.last_action = "attacking"
                    self.pending_attacker_before = attacking_country.total_units()
                    self.pending_defender_before = clicked_country.total_units()
                    self.pending_defender_owner = clicked_country.owner
                    battle = Combat(attacking_country, clicked_country)
                    self.pending_result = battle.simulate_combat()
                    self.combat_start_time = pygame.time.get_ticks()
                    self.combat_log = battle.combat_log
                    self.max_round = len(self.combat_log)
                    self.round = 1
                    self.game.state = "attacking"
                    self.incoming_attack = (attacking_country, clicked_country)
                    attacking_country.combat, clicked_country.combat = True, True
                    self.attack_result = None
                    self.game.UI.remove_highlight(self.game.map)
                    self.game.attacking_country = None
                    self.refresh_panel()

    def refresh_panel(self):
        current_time = pygame.time.get_ticks()
        can_skip = (current_time - self.combat_start_time) >= self.skip_delay
        is_last_round = self.round >= self.max_round
        result_text = None
        if is_last_round:
            result_text = "Victory" if self.pending_result == "attacker" else "Defeat"
        self.game.UI.show_combat(self.combat_log, self.round, self.max_round,self.next_round, self.skip_combat,can_skip, is_last_round, result_text)
        
    def next_round(self):
        if self.round < self.max_round:
            self.round += 1
            self.refresh_panel()
        else:
            self.finish_combat()

    def skip_combat(self):
        self.round = self.max_round

    def finish_combat(self):
        self.game.UI.panel_visible = False
        result = self.game.player.apply_attack_result(self.pending_result, self.pending_attacker_before,self.pending_defender_before, self.pending_defender_owner)
        self.game.state = "play"
        self.attack_result = None
        if self.incoming_attack:
            self.incoming_attack[0].combat = False
            self.incoming_attack[1].combat = False
        self.game.UI.remove_highlight(self.game.map)
        self.game.attacking_country = None

    def show_blocked_message(self, text):
        self.attack_result = text
        self.result_start_time = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        if self.game.state != "attacking":
            if self.attack_result:
                if current_time - self.result_start_time >= self.result_duration:
                    self.attack_result = None
            return
        self.refresh_panel()

    def draw(self, screen):
        font = pygame.font.SysFont(None, 35)
        if self.game.state != "attacking" and self.attack_result:
            text = font.render(self.attack_result, True, (255, 215, 0))
            screen.blit(text, text.get_rect(center=(640, 360)))