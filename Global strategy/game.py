import pygame
from map import Map
from shapely.geometry import Point
from player import Player, AI
from ui import UI

class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.font = pygame.font.SysFont(None, 35)
       
        self.UI = UI()

        self.world = Map()
        self.player_country, self.enemy_country = None, None
        self.player, self.enemy = None, None

        self.attack_start_time, self.attack_duration = 0, 4000
        self.incoming_attack = None
        self.attack_result, self.result_start_time, self.result_duration = None, 0, 2000

        self.move_from = None 
        self.move_text, self.move_text_time = None, 0

        self.selected_country, self.attacking_country = None, None
        self.last_income_time = pygame.time.get_ticks()

        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)

        self.game_result = None
        self.state = "setup"

    def buy_infantry_country(self):
        if self.selected_country:
            self.player.buy_infantry(self.selected_country)

    def buy_tank_country(self):
        if self.selected_country:
            self.player.buy_tank(self.selected_country)

    def buy_artillery_country(self):
        if self.selected_country:
            self.player.buy_artillery(self.selected_country)

    def update_unit_panel(self):
        self.UI.panel_visible = True
        self.UI.open_units_info(self.buy_infantry_country, self.buy_tank_country, self.buy_artillery_country)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)

#game ends when player captures all territories or loses all territories
    def check_win(self):
        if len(self.player.territories) == len(self.world.countries):
            self.state = "game_over"
            self.game_result = "win"
            self.end_time = pygame.time.get_ticks()
        elif len(self.player.territories) == 0:
            self.state = "game_over"
            self.game_result = "lose"
            self.end_time = pygame.time.get_ticks()

#enters attack when attack button is clicked
    def enter_attack(self):
        if self.selected_country in self.player.territories:
            self.state = "select_attack"
            self.attacking_country = self.selected_country
            self.UI.panel_visible = True
            self.UI.open_attack_info()
            self.UI.highlight_attack(self.attacking_country, self.world, self.player)
            self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)

#enters move mode when move units button clicked
    def enter_move(self):
        if self.selected_country in self.player.territories:
            self.state = "moving"
            self.move_from = self.selected_country
            self.UI.panel_visible = True
            self.UI.open_move_info()
            self.UI.highlight_move(self.move_from, self.world, self.player)

#handles events based on state of the game
    def handle_event(self,event):
            if self.state == "setup":
                self.handle_setup(event)
                return 
            if self.state == "game_over":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.UI.player_sidebar_visible = not self.UI.player_sidebar_visible
                if event.key == pygame.K_ESCAPE:
                    return "pause"
            if self.state == "attacking":
                return
            if self.UI.panel_visible:
                self.UI.panel.handle_event(event)
            self.UI.sidebar.handle_event(event)
            world_pos = self.world.get_world_pos()
            point = Point(world_pos.x,world_pos.y)
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked_country = None
                for country in self.world.countries.values():
                   if country.polygon.contains(point):
                      clicked_country = country
                      self.handle_country_click(clicked_country)

#allows player to choose starting countries
    def handle_setup(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        world_pos = self.world.get_world_pos()
        point = Point(world_pos.x,world_pos.y)
        for country in self.world.countries.values():
            if country.polygon.contains(point):
                if self.UI.setup_mode == "player":
                    self.player_country = country
                    self.player = Player(country)
                    self.UI.setup_mode = "enemy"
                    return
                elif self.UI.setup_mode == "enemy":
                    if country != self.player_country:
                        self.enemy_country = country
                        self.enemy = AI(country, playstyle="aggressive")
                        self.state = "play"

#moves half the units from original to clicked country from player countries           
    def handle_move(self,clicked_country):
        if self.move_from:
            if clicked_country in self.player.territories:
                if clicked_country.name in self.move_from.adjacent:
                    amount = self.move_from.units["infantry"] // 2 
                    success = self.player.move_units(self.move_from, clicked_country, amount)
                    if success:
                        self.move_text = f"Moved {amount} units from {self.move_from.name} to {clicked_country.name}"
                        self.move_text_time = pygame.time.get_ticks()
            self.move_from = None
            self.state = "play"
            self.UI.remove_highlight(self.world)
            self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)

#changes state to attacking and creates an incoming attack
    def handle_attack(self, clicked_country):
         if self.attacking_country:
            if clicked_country.name in self.attacking_country.adjacent:
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
                        self.UI.remove_highlight(self.world)
                        self.attacking_country = None
                        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)

    def select_country(self, clicked_country):
        self.selected_country = clicked_country 
        self.UI.remove_highlight(self.world)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)
    
    def deselect_country(self):
        self.selected_country = None
        self.attacking_country = None
        self.UI.units_sidebar_visible = False
        self.UI.remove_highlight(self.world)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)
        self.state = "play"

#handles player clicking countries on map  
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
            self.UI.update_player_sidebar(self.player,self.enemy)
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
                self.UI.remove_highlight(self.world)
                self.attacking_country = None
                self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.enter_attack, self.enter_move)
        elif self.attack_result:
            if current_time - self.result_start_time >= self.result_duration:
                self.attack_result = None

    def draw(self):
        self.UI.draw(self.screen, self.world, self.state,self.selected_country,self.player, self.enemy,self.game_result)
        self.UI.draw_fps(self.clock, self.screen)
        if self.state == "attacking":
            text = self.font.render(f"Attacking {self.incoming_attack[1].name}",True,(255, 255, 255))
            rect = text.get_rect(center=(640, 320))
            self.screen.blit(text, rect)
        elif self.attack_result:
            text = self.font.render(self.attack_result, True, (255, 215, 0))
            rect = text.get_rect(center=(640, 360))
            self.screen.blit(text, rect)
        if self.move_text:
            if pygame.time.get_ticks() - self.move_text_time < 2000:
                text = self.font.render(self.move_text, True, (255, 255, 255))
                self.screen.blit(text, (200, 200))
            else:
                self.move_text = None
        if self.enemy:
            if self.enemy.state == "attacking":
                text = self.font.render("Enemy Attacking", True, (255, 100, 100))
                self.screen.blit(text, (600, 100))