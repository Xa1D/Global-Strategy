import pygame
from map import Map, MapDisplay
from shapely.geometry import Point
from player import Player
from ai import AI
from GameUI import GameUI
from combat import STATS
from CombatManager import CombatManager
from MovementManager import MovementManager
from PurchaseManager import PurchaseManager


class Game:
    def __init__(self, screen, map_file, clock,ai_count=1):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 35)
        self.clock = clock
        self.ui = GameUI()
        self.ui.reset_game_ui(ai_count)

        self.start_pause = None
     
        self.map = Map(map_file)
        self.map_display = MapDisplay(self.map,screen)

        self.player_territory, self.enemy_territory = None, None
        self.player = None
        self.ai_players = []
        self.clicked_territory = None 

        self.selected_territory, self.attacking_territory = None, None
        self.last_income_time = pygame.time.get_ticks()

        self.combat_manager = None
        self.movement_manager = None
        self.purchase_manager = None

        self.game_result = None
        self.game_state = "setup"

    def shift_timers(self, paused_duration):
        self.player.start_time += paused_duration
        self.player.last_income_time += paused_duration
        for ai in self.ai_players:
            ai.start_time += paused_duration
            ai.last_income_time += paused_duration
            ai.next_action += paused_duration
            ai.last_attack += paused_duration
   
    def enter_attack(self):
        self.game_state, self.attacking_territory = self.combat_manager.enter_attack(self.selected_territory,self.attacking_territory,self.game_state,self.map)

    def enter_move(self):
         self.game_state = self.movement_manager.enter_move(self.selected_territory, self.game_state, self.map)

    def open_purchase_panel(self):
        self.purchase_manager.open_panel(self.selected_territory)
        self.ui.update_sidebar(self.selected_territory, self.player, self.open_purchase_panel, self.enter_attack, self.enter_move)

#game ends when player captures all territories or loses all territories
    def check_win(self):
        if len(self.player.territories) == len(self.map.territories):
            self.game_state = "game_over"
            self.game_result = "win"
            self.end_time = pygame.time.get_ticks()
        elif len(self.player.territories) == 0:
            self.game_state = "game_over"
            self.game_result = "lose"
            self.end_time = pygame.time.get_ticks()

#allows player to choose starting territories
    def handle_setup(self, event, point):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        for territory in self.map.territories.values():
            if territory.polygon.contains(point):
                if self.ui.get_setup_mode() == "player":
                    self.player_territory = territory
                    self.player = Player(territory)
                    self.combat_manager = CombatManager(self.player,self.ui)
                    self.movement_manager = MovementManager(self.player,self.ui)
                    self.purchase_manager = PurchaseManager(self.player,self.ui)
                    self.ui.set_setup_mode("enemy")
                    return
                elif self.ui.get_setup_mode() == "enemy":
                    taken = [self.player_territory] + [ai.territory for ai in self.ai_players]
                    if territory not in taken:
                        playstyles = ["aggressive", "defensive","balanced"]
                        playstyle = playstyles[len(self.ai_players) % len(playstyles)]
                        offset = 5000 + len(self.ai_players) * 2500
                        ai = AI(territory, playstyle=playstyle,offset=offset)
                        self.ai_players.append(ai)
                        self.ui.place_enemy()
                        if self.ui.all_enemies_placed():
                            self.game_state = "play"
                        return
                    else:
                        self.ui.show_message("Territory already selected")
#handles player clicking territories on map  
    def handle_territory_click(self, clicked_territory):
        if self.selected_territory == clicked_territory:
            self.deselect_territory()
            return
        if self.game_state == "moving":
            self.movement_manager.handle_move(clicked_territory)
            return
        if self.game_state == "select_attack":
            self.game_state, self.attacking_territory = self.combat_manager.handle_attack(clicked_territory,self.attacking_territory,self.game_state,self.map)
            return  
        self.select_territory(clicked_territory)

#handles events based on game_state of the game
    def handle_event(self,event):
            if event.type == pygame.MOUSEWHEEL:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                return
            point = Point(self.map_display.get_map_pos())
            if self.game_state == "setup":
                self.handle_setup(event, point)
                return 
            if self.game_state == "game_over":
                self.ui.close_sidebar()
                self.ui.close_player_sidebar()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.ui.toggle_player_sidebar()
                if event.key == pygame.K_ESCAPE:
                    return "pause"
            if self.game_state == "attacking":
                if self.ui.is_panel_visible():
                    self.ui.handle_panel_event(event)
                return
            if self.ui.is_panel_visible():
                self.ui.handle_panel_event(event)
            if self.ui.is_sidebar_visible():
                self.ui.handle_sidebar_event(event)
            if self.ui.is_player_sidebar_visible():
                self.ui.handle_player_sidebar_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.clicked_territory = None
                for territory in self.map.territories.values():
                   if territory.polygon.contains(point):
                      self.clicked_territory = territory
                      self.handle_territory_click(self.clicked_territory)

    def select_territory(self, clicked_territory):
        self.selected_territory = clicked_territory 
        self.ui.remove_highlight(self.map)
        self.ui.update_sidebar(self.selected_territory, self.player, self.open_purchase_panel, self.enter_attack, self.enter_move)
        self.ui.open_sidebar()
    
    def deselect_territory(self):
        self.selected_territory = None
        self.attacking_territory = None
        self.ui.close_panel()
        self.ui.close_sidebar()
        self.ui.remove_highlight(self.map)
        self.ui.update_sidebar(self.selected_territory, self.player, self.open_purchase_panel, self.enter_attack, self.enter_move)
        self.game_state = "play"

    def update(self,events):
        if self.game_state == "setup":
            return
        if self.player is None or not self.ai_players:
            return
        self.ui.update_message()
        if self.game_state != "game_over":
            self.map_display.update(events)
            self.ui.update_player_sidebar(self.player,self.ai_players)
            self.game_state = self.combat_manager.update(self.game_state)
            self.game_state = self.movement_manager.update(self.game_state)
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

    def draw(self):
        self.ui.draw(self.screen, self.map_display, self.game_state, self.player, self.ai_players, self.game_result)
        current_display = 0
        for ai in self.ai_players:
            if ai.state == "attacking":
                text = self.font.render(f"{ai.attacking_territory.name} attacking {ai.defending_territory.name}", True, (255, 100, 100))
                self.screen.blit(text, (10, 680 - current_display*30))
                current_display += 1
        self.ui.draw_fps(self.screen, self.clock)