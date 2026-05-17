import pygame
from map import Map, MapDisplay
from shapely.geometry import Point
from player import Player, AI
from ui import UI
from handle_combat import CombatManager
from handle_move import MoveManager

class Game:
    def __init__(self, screen, map_file, clock):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 35)
        self.clock = clock
        self.UI = UI()

        self.combat_manager = CombatManager(self)
        self.move_manager = MoveManager(self)

        self.map = Map(map_file)
        self.map_display = MapDisplay(self.map,screen)

        self.player_country, self.enemy_country = None, None
        self.player, self.enemy = None, None

        self.clicked_country = None 

        self.selected_country, self.attacking_country = None, None
        self.last_income_time = pygame.time.get_ticks()

        self.game_result = None
        self.state = "setup"

    def buy_infantry_country(self):
        if self.selected_country:
            self.player.buy_units(self.selected_country, "infantry")

    def buy_tank_country(self):
        if self.selected_country:
            self.player.buy_units(self.selected_country, "tank")

    def buy_artillery_country(self):
        if self.selected_country:
            self.player.buy_units(self.selected_country, "artillery")
    
    def update_unit_panel(self):
        self.UI.panel_visible = True
        self.UI.open_units_info(self.buy_infantry_country, self.buy_tank_country, self.buy_artillery_country)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.combat_manager.enter_attack, self.move_manager.enter_move)

#game ends when player captures all territories or loses all territories
    def check_win(self):
        if len(self.player.territories) == len(self.map.countries):
            self.state = "game_over"
            self.game_result = "win"
            self.end_time = pygame.time.get_ticks()
        elif len(self.player.territories) == 0:
            self.state = "game_over"
            self.game_result = "lose"
            self.end_time = pygame.time.get_ticks()

#allows player to choose starting countries
    def handle_setup(self, event, point):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        for country in self.map.countries.values():
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

#handles player clicking countries on map  
    def handle_country_click(self, clicked_country):
        if self.selected_country == clicked_country:
            self.deselect_country()
            return
        if self.state == "moving":
            self.move_manager.handle_move(clicked_country)
            return
        if self.state == "select_attack":
            self.combat_manager.handle_attack(clicked_country)
            return  
        self.select_country(clicked_country)

#handles events based on state of the game
    def handle_event(self,event):
            if event.type == pygame.MOUSEWHEEL:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                return
            point = Point(self.map_display.get_map_pos())
            if self.state == "setup":
                self.handle_setup(event, point)
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.clicked_country = None
                for country in self.map.countries.values():
                   if country.polygon.contains(point):
                      self.clicked_country = country
                      self.handle_country_click(self.clicked_country)

    def select_country(self, clicked_country):
        self.selected_country = clicked_country 
        self.UI.remove_highlight(self.map)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.combat_manager.enter_attack, self.move_manager.enter_move)
    
    def deselect_country(self):
        self.selected_country = None
        self.attacking_country = None
        self.UI.panel_visible = False
        self.UI.remove_highlight(self.map)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.combat_manager.enter_attack, self.move_manager.enter_move)
        self.state = "play"

    def update(self,events):
        if self.state == "setup":
            return
        if self.player is None or self.enemy is None:
            return
        if self.state != "game_over":
            self.map_display.update(events)
            self.UI.update_player_sidebar(self.player,self.enemy)
            if self.enemy:
                self.enemy.update_ai(self.map, self.player)
                self.enemy.update()
            if self.player:
                self.player.update()
            self.check_win()
        self.combat_manager.update()

    def draw(self):
        self.UI.draw(self.screen, self.map_display, self.state,self.selected_country,self.player, self.enemy,self.game_result)
        self.combat_manager.draw(self.screen)
        self.move_manager.draw(self.screen)
        if self.enemy and self.enemy.state == "attacking":
                text = self.font.render("Enemy Attacking", True, (255, 100, 100))
                self.screen.blit(text, (600, 100))
        self.UI.draw_fps(self.screen,self.clock)