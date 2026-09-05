import pygame
from GUI import Button

class MenuUI:
    def __init__(self):
        self.menu_font = pygame.font.SysFont("cambria", 60)
        self.image = pygame.image.load("assets/Play Rect.png").convert_alpha()

        self.play_button = Button("Play", (640, 300), self.menu_font, "white", "blue", image=self.image)
        self.quit_button = Button("Quit", (640, 450), self.menu_font, "white", "red", image=self.image)

        self.continue_button = Button("Continue", (640, 300), self.menu_font, "white", "blue", image=self.image)
        self.newgame_button = Button("New Game", (640, 420), self.menu_font, "white", "blue", image=self.image)
        self.return_button = Button("Return", (640, 540), self.menu_font, "white", "red", image=self.image)

        self.europe_button = Button("Europe", (640, 250), self.menu_font, "white", "blue", image=self.image)
        self.asia_button = Button("Asia", (640, 385), self.menu_font, "white", "blue", image=self.image)
        self.africa_button = Button("Africa", (640, 510), self.menu_font, "white", "blue", image=self.image)

        self.one_ai_button = Button("1 AI", (640, 250), self.menu_font, "white", "blue", image=self.image)
        self.two_ai_button = Button("2 AI", (640, 385), self.menu_font, "white", "blue", image=self.image)
        self.three_ai_button = Button("3 AI", (640, 510), self.menu_font, "white", "blue", image=self.image)

        self.menu_buttons = [self.play_button, self.quit_button]
        self.option_buttons = [self.continue_button, self.newgame_button, self.return_button]
        self.map_buttons = [self.europe_button, self.asia_button, self.africa_button]
        self.ai_count_buttons = [self.one_ai_button, self.two_ai_button, self.three_ai_button]

    def draw_menu(self,screen):
        screen.fill("black")
        text = self.menu_font.render("MAIN MENU", True, "white")
        screen.blit(text, text.get_rect(center=(640, 150)))
        for button in self.menu_buttons:
            button.update(screen)

    def handle_menu_event(self,event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = event.pos
        if self.play_button.rect.collidepoint(mouse_pos):
            return "play"
        if self.quit_button.rect.collidepoint(mouse_pos):
            return "quit"
        return None

    def draw_map_selection(self,screen):
        screen.fill("black")
        text = self.menu_font.render("SELECT A MAP TO PLAY ON", True, "white")
        screen.blit(text,text.get_rect(center=(640,100)))
        for button in self.map_buttons:
            button.update(screen)

    def select_map(self,event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = event.pos
        if self.europe_button.rect.collidepoint(mouse_pos):
            return "Europe"
        if self.asia_button.rect.collidepoint(mouse_pos):
            return "Asia"
        if self.africa_button.rect.collidepoint(mouse_pos):
            return "Africa"
        return None

    def draw_pause_screen(self,screen):
        screen.fill("black")
        text = self.menu_font.render("PAUSED", True, "white")
        screen.blit(text, text.get_rect(center=(640, 150)))
        for button in self.option_buttons:
            button.update(screen)

    def handle_pause_event(self,event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = event.pos
        if self.continue_button.rect.collidepoint(mouse_pos):
            return "continue"
        if self.newgame_button.rect.collidepoint(mouse_pos):
            return "new_game"
        if self.return_button.rect.collidepoint(mouse_pos):
            return "menu"
        return None

    def draw_ai_selection(self,screen):
        screen.fill("black")
        text = self.menu_font.render("SELECT NUMBER OF AI OPPONENTS", True, "white")
        screen.blit(text, text.get_rect(center=(640, 100)))
        for button in self.ai_count_buttons:
            button.update(screen)

    def select_ai_count(self,event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = event.pos
        if self.one_ai_button.rect.collidepoint(mouse_pos):
            return 1
        elif self.two_ai_button.rect.collidepoint(mouse_pos):
            return 2
        elif self.three_ai_button.rect.collidepoint(mouse_pos):
            return 3
        else:
            return None
