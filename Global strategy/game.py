import pygame as pg
from geo import World
from shapely.geometry import Point
from GUI import Sidebar
from player import Player, AI

class Game:
    def __init__(self, screen, clock, window_size):
        self.screen = screen
        self.clock = clock
        self.window_size = window_size
        self.font = pg.font.SysFont(None, 35)
        self.world = World()
        self.player_country = self.world.countries["United Kingdom"]
        self.enemy_country = self.world.countries["Germany"]
        self.player = Player(self.player_country)
        self.enemy = AI(self.enemy_country, playstyle="aggressive")
        self.attacking = False
        self.attack_start_time = 0
        self.attack_duration = 4000
        self.attack_attacker = None
        self.attack_defender = None
        self.attack_result = None
        self.result_start_time = 0
        self.result_duration = 2000
        self.move_mode = False
        self.move_from = None 
        self.selected_country = None
        self.attacking_country = None
        self.attack_mode = False
        self.last_income_time = pg.time.get_ticks()
        self.sidebar = Sidebar(pos=(1000, 0), width=280, height=720, font=self.font)
        self.player_sidebar = Sidebar(pos=(0,40), width=250, height=640, font=self.font)
        self.player_sidebar_visible = False
        self.update_sidebar()
        self.game_over = False
        self.game_result = None
        self.move_text = None
        self.move_text_time = 0

    def update_sidebar(self):
        self.sidebar.buttons.clear()
        if self.selected_country:
            if self.selected_country in self.player.territories:
                self.sidebar.add_button("Buy Units", lambda: self.player.buy_units(self.selected_country))
                self.sidebar.add_button("Attack", self.enter_attack_mode)
                self.sidebar.add_button("Move Units", self.enter_move_mode)
   
    def check_win(self):
        if len(self.player.territories) == len(self.world.countries):
            self.game_over = True
            self.game_result = "win"
        elif len(self.player.territories) == 0:
            self.game_over = True
            self.game_result = "lose"

    def enter_attack_mode(self):
        if self.selected_country in self.player.territories:
            self.attack_mode = True
            self.attacking_country = self.selected_country
            for name in self.selected_country.neighbours:
                if self.world.countries[name] not in self.player.territories:
                    self.world.countries[name].highlighted = True
            self.update_sidebar()

    def enter_move_mode(self):
        if self.selected_country in self.player.territories:
            self.move_mode = True
            self.move_from = self.selected_country
            for name in self.selected_country.neighbours:
                country = self.world.countries[name]
                if country in self.player.territories:
                    country.highlighted = True

    def handle_event(self,event):
            if self.game_over:
                return 
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_TAB:
                    self.player_sidebar_visible = not self.player_sidebar_visible
            if self.attacking:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return "pause"  
            self.sidebar.handle_event(event)
            mouse_pos = pg.mouse.get_pos()
            point = Point(mouse_pos[0] + self.world.scroll.x, mouse_pos[1] + self.world.scroll.y)
            if event.type == pg.MOUSEBUTTONDOWN:
                clicked_country = None
                for country in self.world.countries.values():
                   if country.polygon.contains(point):
                      clicked_country = country
                      break
                if clicked_country:
                    self.handle_country_click(clicked_country)
    
    def handle_country_click(self, clicked_country):
        if self.selected_country == clicked_country:
            self.selected_country = None
            self.attack_mode = False
            self.attacking_country = None
            for c in self.world.countries.values():
                c.highlighted = False
            self.update_sidebar()
            return
        if self.move_mode and self.move_from:
            moved = False
            if clicked_country in self.player.territories:
                if clicked_country.name in self.move_from.neighbours:
                    amount = self.move_from.units // 2  # keep simple for now
                    success = self.player.move_units(self.move_from, clicked_country, amount)
                    if success:
                        moved = True
                        self.move_text = f"Moved {amount} units from {self.move_from.name} to {clicked_country.name}"
                        self.move_text_time = pg.time.get_ticks()
            # only reset if valid click OR cancel
            self.move_mode = False
            self.move_from = None

            for c in self.world.countries.values():
                c.highlighted = False

            self.update_sidebar()
            return
        if self.attack_mode and self.attacking_country:
            if clicked_country.name in self.attacking_country.neighbours:
                if clicked_country not in self.player.territories:
                    self.player.attacking_country = self.attacking_country
                    self.player.defending_country = clicked_country
                    self.attacking = True
                    self.attack_start_time = pg.time.get_ticks()
                    self.attack_attacker = self.attacking_country
                    self.attack_defender = clicked_country
                    self.attack_result = None
                    for c in self.world.countries.values():
                        c.highlighted = False
                    self.attack_mode = False
                    self.attacking_country = None
                    self.update_sidebar()
            return  
        self.selected_country = clicked_country 
        if not (self.attack_mode and self.attacking_country and clicked_country.name in self.attacking_country.neighbours):
            for c in self.world.countries.values():
                c.highlighted = False
            self.attack_mode = False
            self.attacking_country = None
        if clicked_country in self.player.territories:
            self.attacking_country = clicked_country
            self.attack_mode = False
        self.update_sidebar()

    def update(self):
        self.world.update()
        self.update_player_sidebar()
        current_time = pg.time.get_ticks()
        if current_time - self.last_income_time >= 1000: 
            self.player.money_tick()
            self.last_income_time = current_time
        if self.attacking:
            if current_time - self.attack_start_time >= self.attack_duration:
                self.player.attacking_country = self.attack_attacker
                self.player.defending_country = self.attack_defender
                result = self.player.attack(self.enemy)
                if result == "win":
                    self.attack_result = "Victory!"
                else:
                    self.attack_result = "Defeat!"
                self.attacking = False
                self.result_start_time = current_time
                for c in self.world.countries.values():
                    c.highlighted = False
                self.attack_mode = False
                self.attacking_country = None
                self.update_sidebar()
        elif self.attack_result:
            if current_time - self.result_start_time >= self.result_duration:
                self.attack_result = None
                self.attack_attacker = None
                self.attack_defender = None
        if not self.game_over:
            self.check_win()

    def update_player_sidebar(self):
        self.player_sidebar.buttons.clear()
        total_units = sum(c.units for c in self.player.territories)
        territory_count = len(self.player.territories)
        self.player_sidebar.add_button(f"Territories: {territory_count}", None)
        self.player_sidebar.add_button(f"Total Units: {total_units}", None)

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.world.draw(self.screen,self.player,self.enemy)
        if self.selected_country:
            self.sidebar.draw(self.screen, self.selected_country)
        fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255))
        self.screen.blit(fps_text, (50, 10))
        currency_text = self.font.render(f"Currency: {self.player.currency}", True, (255, 255, 255))
        self.screen.blit(currency_text, (250, 10))
        income_text = self.font.render(f"Income: {self.player.income}", True, (255, 255, 255))
        self.screen.blit(income_text, (500, 10))
        if self.attacking:
            text = self.font.render(f"Attacking {self.attack_defender.name}...",True,(255, 255, 255))
            rect = text.get_rect(center=(640, 320))
            self.screen.blit(text, rect)
        elif self.attack_result:
            text = self.font.render(self.attack_result, True, (255, 215, 0))
            rect = text.get_rect(center=(640, 360))
            self.screen.blit(text, rect)
        if self.player_sidebar_visible:
            self.player_sidebar.draw(self.screen, None)
        if self.game_over:
            if self.game_result == "win":
                text = self.font.render("YOU WIN!", True, (0, 255, 0))
            else:
                text = self.font.render("YOU LOSE!", True, (255, 0, 0))

            rect = text.get_rect(center=(640, 360))
            self.screen.blit(text, rect)
        if self.move_text:
            if pg.time.get_ticks() - self.move_text_time < 2000:
                text = self.font.render(self.move_text, True, (255, 255, 255))
                self.screen.blit(text, (200, 200))
            else:
                self.move_text = None
        
