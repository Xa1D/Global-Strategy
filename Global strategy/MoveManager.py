import pygame

class MoveManager:
    def __init__(self, game):
        self.game = game
        self.count = {"infantry": 0, "tank": 0, "artillery": 0}
        self.move_from, self.move_to = None, None
        self.move_text, self.move_text_time = None, 0

    def enter_move(self):
        if len(self.game.player.territories) <= 1:
            self.show_message("Cannot move units with only 1 country")
            return
        if self.game.selected_country in self.game.player.territories:
            self.game.state = "moving"
            self.move_from = self.game.selected_country
            self.move_to = None
            self.count = {"infantry": 0, "tank": 0, "artillery": 0}
            self.game.UI.highlight_move(self.move_from, self.game.map, self.game.player)

    def handle_move(self, clicked_country):
        if self.move_from and self.move_to is None:
            if clicked_country in self.game.player.territories:
                if clicked_country.name in self.move_from.adjacent:
                    if clicked_country.combat:
                        self.show_message("Country in combat")
                        return
                    self.move_to = clicked_country
                    self.game.UI.remove_highlight(self.game.map)
                    self.refresh_panel()
                    self.game.UI.panel_visible = True

    def refresh_panel(self):
        self.game.UI.open_move_info(self.move_from, self.count, self.adjust, self.confirm_move, self.finish_move)

    def show_message(self, text):
        self.move_text = text
        self.move_text_time = pygame.time.get_ticks()

    def adjust(self, unit_type, delta):
        max_amount = self.move_from.units.get(unit_type, 0)
        new_value = self.count[unit_type] + delta
        self.count[unit_type] = max(0, min(new_value, max_amount))
        self.refresh_panel()

    def confirm_move(self):
        if sum(self.count.values()) <= 0:
            return
        success = self.game.player.move_units(self.move_from, self.move_to,self.count["infantry"], self.count["tank"], self.count["artillery"])
        if success:
            self.game.player.last_action = "reinforcing"
            self.move_text = (f"Moved {self.count['infantry']} infantry, {self.count['tank']} tanks, {self.count['artillery']} artillery to {self.move_to.name}")
            self.move_text_time = pygame.time.get_ticks()
        self.finish_move()

    def finish_move(self):
        self.move_from = None
        self.move_to = None
        self.game.state = "play"
        self.game.UI.panel_visible = False
        self.game.UI.remove_highlight(self.game.map)

    def draw(self, screen):
        font = pygame.font.SysFont(None, 35)
        if self.move_text:
            if pygame.time.get_ticks() - self.move_text_time < 2000:
                text = font.render(self.move_text, True, (255, 255, 255))
                screen.blit(text, (200, 200))
            else:
                self.move_text = None