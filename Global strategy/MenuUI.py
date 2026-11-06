import pygame
from GUI import Button
from combat_config import UNIT_STATS
from ui_config import AI_COLOURS, PLAYER_COLOUR, NEUTRAL_COLOUR

class MenuUI:
    def __init__(self):
        self.menu_font = pygame.font.SysFont("viga", 60)
        self.heading_font = pygame.font.SysFont("viga", 30)
        self.body_font = pygame.font.SysFont("viga", 22)
        self.image = pygame.image.load("assets/Play Rect.png").convert_alpha()

        self.play_button = Button("Play", (640, 300), self.menu_font, "white", "blue", image=self.image)
        self.quit_button = Button("Quit", (640, 450), self.menu_font, "white", "red", image=self.image)

        self.continue_button = Button("Continue", (640, 250), self.menu_font, "white", "blue", image=self.image)
        self.newgame_button = Button("New Game", (640, 360), self.menu_font, "white", "blue", image=self.image)
        self.rules_button = Button("Rules", (640, 470), self.menu_font, "white", "blue", image=self.image)
        self.return_button = Button("Return", (640, 580), self.menu_font, "white", "red", image=self.image)
        self.back_button = Button("Back", (640, 665), self.menu_font, "white", "blue", image=self.image)  

        self.europe_button = Button("Europe", (640, 250), self.menu_font, "white", "blue", image=self.image)
        self.asia_button = Button("Asia", (640, 385), self.menu_font, "white", "blue", image=self.image)
        self.africa_button = Button("Africa", (640, 510), self.menu_font, "white", "blue", image=self.image)

        self.one_ai_button = Button("1 AI", (640, 250), self.menu_font, "white", "blue", image=self.image)
        self.two_ai_button = Button("2 AI", (640, 385), self.menu_font, "white", "blue", image=self.image)
        self.three_ai_button = Button("3 AI", (640, 510), self.menu_font, "white", "blue", image=self.image)

        self.menu_buttons = [self.play_button, self.quit_button]
        self.option_buttons = [self.continue_button, self.newgame_button, self.rules_button, self.return_button]
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
        if self.rules_button.rect.collidepoint(mouse_pos):
            return "rules"
        if self.return_button.rect.collidepoint(mouse_pos):
            return "menu"
        return None

    def draw_rules_section(self,screen,sections,x,y):
        for heading, lines in sections:
            screen.blit(self.heading_font.render(heading, True, (255, 220, 110)), (x, y))
            y += 40
            for line in lines:
                screen.blit(self.body_font.render(line, True, "white"), (x, y))
                y += 30
            y += 20
        return y

    def draw_rules_screen(self,screen):
        left_rules = [("OBJECTIVE", ["Capture every territory on the map, neutral ones included."]),
                      ("ACTIONS", ["Buy Units: spend currency on units for that territory",
                                    "Attack: battle an adjacent territory you do not own",
                                    "Move Units: send units to an adjacent territory you own",
                                    "Territories in combat or on cooldown cannot be attacked"]),
                      ("CONTROLS", ["W A S D moves the map, the mouse wheel zooms.",
                                    "TAB shows player stats, ESC pauses."])]
        right_rules = [("COMBAT", ["Armies fight in rounds and both sides hit at the same time.",
                                   "Each hit does 75% to 125% of the unit's attack, and can miss."])]
        #each AI gets a colour and a playstyle in the order it is placed (colours from AI_COLOURS, playstyles from handle_setup in game.py)
        territory_colours = [("Blue", PLAYER_COLOUR, "You - the player"),
                             ("Green", AI_COLOURS[0], "AI 1 (aggressive)"),
                             ("Magenta", AI_COLOURS[1], "AI 2 (defensive)"),
                             ("Orange", AI_COLOURS[2], "AI 3 (balanced)"),
                             ("Grey", NEUTRAL_COLOUR, "Neutral - not owned")]
        unit_columns = [("Unit", 700), ("Cost", 830), ("Attack", 900), ("Health", 990), ("Miss", 1080), ("Attacks", 1150)]
        unit_rows = []
        for unit, stats in UNIT_STATS.items():
            attacks = "Every round" if stats["cooldown"] == 1 else f"Every {stats['cooldown']} rounds"
            unit_rows.append([unit.capitalize(), str(stats["cost"]), str(stats["attack"]), str(stats["health"]), f"{round(stats["miss"] * 100)}%", attacks]) 

        screen.fill("black")
        text = self.menu_font.render("RULES", True, "white")
        screen.blit(text, text.get_rect(center=(640, 50)))
        self.draw_rules_section(screen, left_rules, 60, 110)
        y = self.draw_rules_section(screen, right_rules, 700, 110)
        screen.blit(self.heading_font.render("UNIT INFO", True, (255, 220, 110)), (700, y))
        y += 40
        for column_name, x in unit_columns:
            screen.blit(self.body_font.render(column_name, True, (160, 160, 160)), (x, y))
        for row in unit_rows:
            y += 35
            for index in range(len(row)):
                screen.blit(self.body_font.render(row[index], True, "white"), (unit_columns[index][1], y))
        y += 50
        screen.blit(self.heading_font.render("TERRITORY COLOURS", True, (255, 220, 110)), (700, y))
        y += 40
        for colour_name, colour, description in territory_colours:
            pygame.draw.rect(screen, colour, (700, y + 2, 20, 20))
            screen.blit(self.body_font.render(f"{colour_name}: {description}", True, "white"), (732, y))
            y += 30
        self.back_button.update(screen)

    def handle_rules_event(self,event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"
        if event.type == pygame.MOUSEBUTTONDOWN and self.back_button.rect.collidepoint(event.pos):
            return "back"
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
