import pygame
from map import Map, MapDisplay
from shapely.geometry import Point
from player import Player
from ai import AI
from ui import UI
from combat import STATS
from CombatManager import CombatManager
from MoveManager import MoveManager


class Game:
    def __init__(self, screen, map_file, clock,ai_count=1):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 35)
        self.clock = clock
        self.UI = UI()
        self.UI.enemy_count = ai_count
        self.UI.enemies_placed = 0
        
        self.start_pause = None

        self.combat_manager = CombatManager(self)
        self.move_manager = MoveManager(self)
     

        self.map = Map(map_file)
        self.map_display = MapDisplay(self.map,screen)

        self.player_country, self.enemy_country = None, None
        self.player = None
        self.ai_players = []
        self.clicked_country = None 

        self.selected_country, self.attacking_country = None, None
        self.last_income_time = pygame.time.get_ticks()

        self.purchase_amounts = {"infantry": 1, "tank": 1, "artillery": 1}

        self.game_result = None
        self.state = "setup"

    def shift_timers(self, paused_duration):
        self.player.start_time += paused_duration
        self.player.last_income_time += paused_duration
        for ai in self.ai_players:
            ai.start_time += paused_duration
            ai.last_income_time += paused_duration
            ai.next_action += paused_duration
            ai.last_attack += paused_duration

    def adjust_buy_amount(self, unit_type, delta):
        cost = STATS[unit_type]["cost"]
        max_affordable = max(self.player.currency // cost, 1)
        new_value = self.purchase_amounts[unit_type] + delta
        new_value = max(1, min(new_value, max_affordable))
        self.purchase_amounts[unit_type] = new_value
        self.refresh_buy_panel()

    def attempt_buy(self, unit_type):
        amount = self.purchase_amounts[unit_type]
        cost = STATS[unit_type]["cost"] * amount
        if self.player.currency < cost:
            self.move_manager.show_message("Cannot afford units")
            return
        self.player.buy_units(self.selected_country, unit_type, amount)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.combat_manager.enter_attack, self.move_manager.enter_move)
        self.refresh_buy_panel()

    def refresh_buy_panel(self):
        self.UI.open_buy_panel(self.purchase_amounts, self.adjust_buy_amount,self.buy_infantry_country, self.buy_tank_country, self.buy_artillery_country)

    def buy_infantry_country(self):
        if self.selected_country:
            self.attempt_buy("infantry")

    def buy_tank_country(self):
        if self.selected_country:
            self.attempt_buy("tank")

    def buy_artillery_country(self):
        if self.selected_country:
            self.attempt_buy("artillery")
            
    def update_unit_panel(self):
        if self.selected_country and self.selected_country.combat:
            self.combat_manager.show_message("Country in combat")
            return
        self.UI.panel_visible = True
        self.refresh_buy_panel()
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
                    taken = [self.player_country] + [ai.country for ai in self.ai_players]
                    if country not in taken:
                        playstyles = ["aggressive", "defensive","balanced"]
                        playstyle = playstyles[len(self.ai_players) % len(playstyles)]
                        offset = 5000 + len(self.ai_players) * 2500
                        ai = AI(country, playstyle=playstyle,offset=offset)
                        self.ai_players.append(ai)
                        self.UI.enemies_placed += 1
                        if self.UI.enemies_placed >= self.UI.enemy_count:
                            self.state = "play"
                        return

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
                self.UI.sidebar_visible = False
                self.UI.player_sidebar_visible = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.UI.player_sidebar_visible = not self.UI.player_sidebar_visible
                if event.key == pygame.K_ESCAPE:
                    return "pause"
            if self.state == "attacking":
                if self.UI.panel_visible:
                    self.UI.panel.handle_event(event)
                return
            if self.UI.panel_visible:
                self.UI.panel.handle_event(event)
            if self.UI.sidebar_visible:
                self.UI.sidebar.handle_event(event)
            if self.UI.player_sidebar_visible:
                self.UI.player_sidebar.handle_event(event)
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
        self.UI.sidebar_visible = True
    
    def deselect_country(self):
        self.selected_country = None
        self.attacking_country = None
        self.UI.panel_visible = False
        self.UI.sidebar_visible = False
        self.UI.remove_highlight(self.map)
        self.UI.update_sidebar(self.selected_country, self.player, self.update_unit_panel, self.combat_manager.enter_attack, self.move_manager.enter_move)
        self.state = "play"

    def update(self,events):
        if self.state == "setup":
            return
        if self.player is None or not self.ai_players:
            return
        if self.state != "game_over":
            self.map_display.update(events)
            self.UI.update_player_sidebar(self.player,self.ai_players)
            elapsed = pygame.time.get_ticks() - self.player.start_time
            if elapsed >= 120000 and self.player.territories_at_2min is None:
                self.player.territories_at_2min = len(self.player.territories)
                for ai in self.ai_players:
                    ai.territories_at_2min = len(ai.territories)
            for ai in self.ai_players:
                ai.update_ai(self.map, self.player,self.ai_players)
                ai.update()
            if self.player:
                self.player.update()
            self.check_win()
        self.combat_manager.update()

    def draw(self):
        self.UI.draw(self.screen, self.map_display, self.state, self.player, self.ai_players, self.game_result)
        self.combat_manager.draw(self.screen)
        self.move_manager.draw(self.screen)
        current_display = 0
        for ai in self.ai_players:
            if ai.state == "attacking":
                text = self.font.render(f"{ai.attacking_country.name} attacking {ai.defending_country.name}", True, (255, 100, 100))
                self.screen.blit(text, (10, 680 - current_display*30))
                current_display += 1
        self.UI.draw_fps(self.screen, self.clock)