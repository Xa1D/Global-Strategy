import pygame

class MoveManager:
    def __init__(self,game):
        self.game = game
        self.count = {"infantry": 0, "tank": 0, "artillery": 0}
        self.move_from, self.move_to = None, None
        self.move_text, self.move_text_time = None, 0

    def enter_move(self):
        if self.game.selected_country in self.game.player.territories:
            self.game.state = "moving"
            self.move_from = self.game.selected_country
            self.count = {"infantry": 0, "tank": 0, "artillery": 0}
            self.game.UI.highlight_move(self.move_from, self.game.map, self.game.player)

    def handle_move(self, clicked_country):
        if self.move_from:
            if clicked_country in self.game.player.territories:
                if clicked_country.name in self.move_from.adjacent:
                    self.move_to = clicked_country
                    infantry_amount = self.move_from.units["infantry"] // 2
                    tank_amount = self.move_from.units["tank"] // 2
                    artillery_amount = self.move_from.units["artillery"] // 2
                    success = self.game.player.move_units(self.move_from,self.move_to, infantry_amount , tank_amount , artillery_amount)
                    if success:
                        self.move_text = (f"Moved {infantry_amount} infantry, {tank_amount} tanks, {artillery_amount} artillery to {self.move_to.name}")
                        self.move_text_time = pygame.time.get_ticks()
        self.cancel_move()

    def cancel_move(self):
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