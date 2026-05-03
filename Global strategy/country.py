from shapely.geometry import Polygon,Point
import pygame

class Country:
    def __init__(self, name, coordinates):
        self.position = coordinates
        self.name = name
        self.polygon = Polygon(self.position)
        self.colour = (128,128,128)
        self.combat, self.highlighted, self.hovered = False, False, False
        self.units = {}
        self.attack_cooldown = 0
        self.adjacent = []
    
#getting screen coordinates by subtracting camera value from the coordinates
    def get_coordinates(self,scroll):
        points = []
        for coord in self.position:
            points.append((coord[0]-scroll.x,coord[1]-scroll.y))
        return points
    
    def get_colour(self,player,enemy):
        if self.highlighted:
            return (255, 150, 0)
        elif player and self in player.territories:
            return (0, 100, 255) 
        elif enemy and self in enemy.territories:
            return (0,255,0)
        elif self.hovered and not self.highlighted:
            return (255, 0, 0) 
        else:
          return self.colour 

#drawing country polygon along with the country outline/border
    def draw(self, screen, scroll, player, enemy):
        colour = self.get_colour(player,enemy)
        pygame.draw.polygon(screen,colour,self.get_coordinates(scroll))
        pygame.draw.polygon(screen,("white"),self.get_coordinates(scroll),width=1)

    def update(self, mouse_pos):
        self.hovered = False
        if Point(mouse_pos.x, mouse_pos.y).within(self.polygon):
            self.hovered = True
