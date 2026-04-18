import pygame
from map import Map
from shapely.geometry import Point
from GUI import Sidebar
from player import Player, AI

class Game:
    def __init__(self, screen, clock, width, height):
        self.screen = screen
        self.clock = clock
        self.window_size = pygame.Vector2(width, height)
        self.font = pygame.font.SysFont(None, 35)
        self.world = Map()
        self.player_country, self.enemy_country = None, None
        self.player, self.enemy = None, None
        self.attack_start_time = 0
        self.attack_duration = 4000
        self.incoming_attack = None
        self.attack_result = None
        self.result_start_time = 0
        self.result_duration = 2000
        self.move_from = None 
        self.selected_country, self.attacking_country = None, None
        self.last_income_time = pygame.time.get_ticks()
        self.sidebar = Sidebar(pos=(1000, 0), width=280, height=720, font=self.font)
        self.player_sidebar = Sidebar(pos=(0,40), width=250, height=640, font=self.font)
        self.player_sidebar_visible = False
        self.update_sidebar()
        self.game_result = None
        self.move_text = None
        self.move_text_time = 0
        self.state = "setup"
        self.setup_mode = "player"

    def remove_highlight(self):
        for country in self.world.countries.values():
            country.highlighted = False

    def highlight(self):
        if self.state == "select_attack":
            for name in self.selected_country.neighbours:
                if self.world.countries[name] not in self.player.territories and not self.world.countries[name].combat:
                    self.world.countries[name].highlighted = True
        elif self.state == "moving":
            for name in self.selected_country.neighbours:
                if self.world.countries[name] in self.player.territories and not self.world.countries[name].combat:
                    self.world.countries[name].highlighted = True

    def draw_setup(self):
        self.screen.fill((0, 0, 0))
        self.world.draw(self.screen, None, None)
        if self.setup_mode == "player":
             text = self.font.render("Choose your starting country", True, (255, 255, 255))
        elif self.setup_mode == "enemy":
            text = self.font.render("Choose an enemy country", True, (255, 255, 255))
        rect = text.get_rect(center=(640, 100))
        self.screen.blit(text, rect)

    def buy_units_country(self):
        if self.selected_country:
            self.player.buy_units(self.selected_country)

    def update_sidebar(self):
        self.sidebar.buttons.clear()
        if self.selected_country:
            if self.selected_country in self.player.territories:
                self.sidebar.add_button("Buy Units", self.buy_units_country)
                self.sidebar.add_button("Attack", self.enter_attack)
                self.sidebar.add_button("Move Units", self.enter_move)
   
    def check_win(self):
        if len(self.player.territories) == len(self.world.countries):
            self.state = "game_over"
            self.game_result = "win"
            self.end_time = pygame.time.get_ticks()
        elif len(self.player.territories) == 0:
            self.state = "game_over"
            self.game_result = "lose"
            self.end_time = pygame.time.get_ticks()

    def enter_attack(self):
        if self.selected_country in self.player.territories:
            self.state = "select_attack"
            self.attacking_country = self.selected_country
            self.highlight()
            self.update_sidebar()

    def enter_move(self):
        if self.selected_country in self.player.territories:
            self.state = "moving"
            self.move_from = self.selected_country
            self.highlight()

    def handle_event(self,event):
            if self.state == "setup":
                self.handle_setup(event)
                return 
            if self.state == "game_over":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.player_sidebar_visible = not self.player_sidebar_visible
                if event.key == pygame.K_ESCAPE:
                    return "pause"
            if self.state == "attacking":
                return
            self.sidebar.handle_event(event)
            mouse_pos = pygame.mouse.get_pos()
            point = Point(mouse_pos[0] + self.world.scroll.x, mouse_pos[1] + self.world.scroll.y)
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked_country = None
                for country in self.world.countries.values():
                   if country.polygon.contains(point):
                      clicked_country = country
                      self.handle_country_click(clicked_country)

    def handle_setup(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        mouse_pos = pygame.mouse.get_pos()
        point = Point(mouse_pos[0] + self.world.scroll.x, mouse_pos[1] + self.world.scroll.y)
        for country in self.world.countries.values():
            if country.polygon.contains(point):
                if self.setup_mode == "player":
                    self.player_country = country
                    self.player = Player(country)
                    self.setup_mode = "enemy"
                    return
                elif self.setup_mode == "enemy":
                    if country != self.player_country:
                        self.enemy_country = country
                        self.enemy = AI(country, playstyle="aggressive")
                        self.state = "play"
            
    def handle_move(self,clicked_country):
        if self.move_from:
            if clicked_country in self.player.territories:
                if clicked_country.name in self.move_from.neighbours:
                    amount = self.move_from.units // 2 
                    success = self.player.move_units(self.move_from, clicked_country, amount)
                    if success:
                        self.move_text = f"Moved {amount} units from {self.move_from.name} to {clicked_country.name}"
                        self.move_text_time = pygame.time.get_ticks()
            self.move_from = None
            self.state = "play"
            self.remove_highlight()
            self.update_sidebar()

    def handle_attack(self, clicked_country):
         if self.attacking_country:
            if clicked_country.name in self.attacking_country.neighbours:
                if clicked_country not in self.player.territories and not clicked_country.combat and not self.attacking_country.combat:
                    current_time = pygame.time.get_ticks()
                    if current_time < clicked_country.attack_cooldown:
                      return
                    else: 
                        self.player.attacking_country, self.player.defending_country = self.attacking_country, clicked_country
                        self.state = "attacking"
                        self.attack_start_time = pygame.time.get_ticks()
                        self.incoming_attack = (self.attacking_country, clicked_country)
                        self.attacking_country.combat, clicked_country.combat = True, True
                        self.attack_result = None
                        self.remove_highlight()
                        self.attacking_country = None
                        self.update_sidebar()

    def select_country(self, clicked_country):
        self.selected_country = clicked_country 
        self.remove_highlight()
        self.update_sidebar()
    
    def deselect_country(self):
        self.selected_country = None
        self.attacking_country = None
        self.remove_highlight()
        self.update_sidebar()
        self.state = "play"
    
    def handle_country_click(self, clicked_country):
        if self.selected_country == clicked_country:
            self.deselect_country()
            return
        if self.state == "moving":
            self.handle_move(clicked_country)
            return
        if self.state == "select_attack":
            self.handle_attack(clicked_country)
            return  
        self.select_country(clicked_country)

    def update(self):
        if self.state == "setup":
            return
        if self.state != "game_over":
            self.world.update()
            self.update_player_sidebar()
            self.enemy.update_ai(self.world, self.player)
            self.player.update()
            self.enemy.update()
            self.check_win()
        current_time = pygame.time.get_ticks()
        if self.state == "attacking":
            if current_time - self.attack_start_time >= self.attack_duration:
                self.player.attacking_country = self.incoming_attack[0]
                self.player.defending_country = self.incoming_attack[1]
                result = self.player.attack(self.enemy)
                self.state = "play"
                if result == "win":
                    self.attack_result = "Victory"
                else:
                    self.attack_result = "Defeat"
                self.player.defending_country.combat, self.player.attacking_country.combat = False, False
                self.result_start_time = current_time
                self.remove_highlight()
                self.attacking_country = None
                self.update_sidebar()
        elif self.attack_result:
            if current_time - self.result_start_time >= self.result_duration:
                self.attack_result = None

    def update_player_sidebar(self):
        if self.player is None:
            return 
        self.player_sidebar.buttons.clear()
        total_units = 0
        for country in self.player.territories:
            total_units += country.units
        territory_count = len(self.player.territories)
        self.player_sidebar.add_button(f"Territories: {territory_count}", None)
        self.player_sidebar.add_button(f"Total Units: {total_units}", None)
        self.player_sidebar.add_button(f"Enemy territories: {len(self.enemy.territories)}", None)
        self.player_sidebar.add_button(f"Enemy units: {sum(c.units for c in self.enemy.territories)}", None)
        self.player_sidebar.add_button(f"Enemy income: {self.enemy.income}", None)
        self.player_sidebar.add_button(f"Enemy currency: {self.enemy.currency}", None)

    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.state == "setup":
            self.draw_setup()
            return
        else:
            self.world.draw(self.screen,self.player,self.enemy)
        if self.selected_country:
            self.sidebar.draw(self.screen, self.selected_country)
        fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255))
        self.screen.blit(fps_text, (50, 10))
        if self.player:
            currency_text = self.font.render(f"Currency: {self.player.currency}", True, (255, 255, 255))
            self.screen.blit(currency_text, (250, 10))
            income_text = self.font.render(f"Income: {self.player.income}", True, (255, 255, 255))
            self.screen.blit(income_text, (500, 10))
        if self.state == "attacking":
            text = self.font.render(f"Attacking {self.incoming_attack[1].name}...",True,(255, 255, 255))
            rect = text.get_rect(center=(640, 320))
            self.screen.blit(text, rect)
        elif self.attack_result:
            text = self.font.render(self.attack_result, True, (255, 215, 0))
            rect = text.get_rect(center=(640, 360))
            self.screen.blit(text, rect)
        if self.player_sidebar_visible:
            self.player_sidebar.draw(self.screen, None)
        if self.state == "game_over":
            overlay = pygame.Surface((1280, 720))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            if self.game_result == "win":
                text = self.font.render("YOU WIN!", True, (0, 255, 0))
            else:
                text = self.font.render("YOU LOSE!", True, (255, 0, 0))
            rect = text.get_rect(center=(640, 300))
            self.screen.blit(text, rect)
            subtext = self.font.render("Click to return to menu", True, (255, 255, 255))
            self.screen.blit(subtext, subtext.get_rect(center=(640, 400)))
        if self.move_text:
            if pygame.time.get_ticks() - self.move_text_time < 2000:
                text = self.font.render(self.move_text, True, (255, 255, 255))
                self.screen.blit(text, (200, 200))
            else:
                self.move_text = None
        if self.enemy.state == "attacking":
            text = self.font.render("Enemy Attacking...", True, (255, 100, 100))
            self.screen.blit(text, (600, 100))