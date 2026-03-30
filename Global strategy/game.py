import pygame as pg
from geo import World
from shapely.geometry import Point
from GUI import Sidebar
from player import Player

class Game:
    def __init__(self, screen, clock, window_size):
        self.screen = screen
        self.clock = clock
        self.window_size = window_size
        self.font = pg.font.SysFont(None, 24)
        self.world = World()
        self.player_country = self.world.countries["United Kingdom"]
        self.player = Player(self.player_country)
        self.selected_country = None
        self.attacking_country = None
        self.attack_mode = False
        self.sidebar = Sidebar(pos=(1000, 0), width=280, height=720, font=self.font)
        self.update_sidebar()

    def update_sidebar(self):
        self.sidebar.buttons.clear()
        if self.selected_country:
            if self.selected_country in self.player.territories:
                self.sidebar.add_button("Buy Units", lambda: self.player.buy_units(self.selected_country))
                self.sidebar.add_button("Attack", self.enter_attack_mode)


    def enter_attack_mode(self):
        if self.selected_country in self.player.territories:
            self.attack_mode = True
            self.attacking_country = self.selected_country
            for name in self.selected_country.neighbours:
                self.world.countries[name].highlighted = True
            self.update_sidebar()

    def handle_event(self,event):
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
        if self.attack_mode and self.attacking_country:
            if clicked_country.name in self.attacking_country.neighbours:
                self.player.attacking_country = self.attacking_country
                self.player.defending_country = clicked_country
                self.player.attack()
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

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.world.draw(self.screen,self.player)
        if self.selected_country:
            self.sidebar.draw(self.screen, self.selected_country)
        fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255))
        self.screen.blit(fps_text, (10, 10))