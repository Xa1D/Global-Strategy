import pygame

class CombatManager:
    def __init__(self,game):
        self.game = game
        self.attack_start_time, self.attack_duration = 0, 4000
        self.incoming_attack = None
        self.attack_result, self.result_start_time, self.result_duration = None, 0, 2000

    def enter_attack(self):
        if self.game.selected_country in self.game.player.territories:
            self.game.state = "select_attack"
            self.game.attacking_country = self.game.selected_country
            self.game.UI.highlight_attack(self.game.attacking_country,self.game.map,self.game.player)
            self.game.UI.update_sidebar(self.game.selected_country,self.game.player,self.game.update_unit_panel,self.enter_attack,self.game.move_manager.enter_move)

    def handle_attack(self, clicked_country):
         attacking_country = self.game.attacking_country
         if attacking_country:
            if clicked_country.name in attacking_country.adjacent:
                if clicked_country not in self.game.player.territories and not clicked_country.combat and not attacking_country.combat:
                    current_time = pygame.time.get_ticks()
                    if current_time < clicked_country.attack_cooldown:
                        return
                    else: 
                        self.game.player.attacking_country, self.game.player.defending_country = attacking_country, clicked_country
                        self.game.state = "attacking"
                        self.attack_start_time = pygame.time.get_ticks()
                        self.incoming_attack = (attacking_country, clicked_country)
                        attacking_country.combat, clicked_country.combat = True, True
                        self.attack_result = None
                        self.game.UI.remove_highlight(self.game.map)
                        self.game.attacking_country = None
                        self.game.UI.update_sidebar(self.game.selected_country, self.game.player, self.game.update_unit_panel, self.enter_attack, self.game.move_manager.enter_move)

    def update(self):
        current_time = pygame.time.get_ticks()
        if self.game.state != "attacking":
            if self.attack_result:
                if current_time - self.result_start_time >= self.result_duration:
                    self.attack_result = None
            return
        if current_time - self.attack_start_time >= self.attack_duration:
            self.game.player.attacking_country = self.incoming_attack[0]
            self.game.player.defending_country = self.incoming_attack[1]
            result = self.game.player.attack(self.game.enemy)
            self.game.state = "play"
            if result == "win":
                self.attack_result = "Victory"
            else:
                self.attack_result = "Defeat"
            self.incoming_attack[0].combat = False
            self.incoming_attack[1].combat = False
            self.result_start_time = current_time
            self.game.UI.remove_highlight(self.game.map)
            self.game.attacking_country = None

    def draw(self, screen):
        font = pygame.font.SysFont(None, 35)
        if self.game.state == "attacking" and self.incoming_attack:
            text = font.render(f"Attacking {self.incoming_attack[1].name}",True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(640, 320)))
        elif self.attack_result:
            text = font.render(self.attack_result, True, (255, 215, 0))
            screen.blit(text, text.get_rect(center=(640, 360)))


