from shapely.geometry import Polygon
import pygame

class Country:
    def __init__(self, name, coordinates):
        self.position = coordinates
        self.name = name
        self.polygon = Polygon(self.position)
        self.colour = (128,128,128)
        self.combat, self.highlighted, self.hovered = False, False, False
        self.units = {}
        self.leftover_damage = {"infantry":0, "tank": 0, "artillery": 0}
        self.attack_cooldown = 0
        self.adjacent = []
    
#getting screen coordinates by subtracting camera value from the coordinates
    def get_coordinates(self,camera_pos,camera_zoom):
        points = []
        for coord in self.position:
            x = ((coord[0] - camera_pos[0]) * camera_zoom)
            y = ((coord[1] - camera_pos[1]) * camera_zoom)
            points.append((x,y))
        return points
    
    def get_colour(self,player,enemy):
        if self.highlighted:
            return (255, 150, 0)
        elif player and self in player.territories:
            return (0, 100, 255) 
        elif enemy and self in enemy.territories:
            return (0,255,0)
        elif self.hovered and not self.highlighted:
            return (250, 220, 110) 
        else:
          return self.colour 

#drawing country polygon along with the country outline/border
    def draw(self, screen, camera_pos, camera_zoom, player, enemy):
        colour = self.get_colour(player,enemy)
        pygame.draw.polygon(screen,colour,self.get_coordinates(camera_pos,camera_zoom)) # taking surface,colour,converted points and width
        pygame.draw.polygon(screen,("white"),self.get_coordinates(camera_pos,camera_zoom),width=1)

    def check_hovered(self, position):
        if self.polygon.contains(position):
            self.hovered = True
        else:
            self.hovered = False
