from shapely.geometry import Polygon
import pygame

AI_COLOURS = [(0, 255, 0), (255, 0, 255), (255, 165, 0)]

class Territory:
    def __init__(self, name, coordinates):
        self.position = coordinates
        self.name = name
        self.owner = None
        self.polygon = Polygon(self.position)
        self.colour = (128,128,128)
        self.combat, self.highlighted, self.hovered = False, False, False
        self.units = {}
        self.attack_cooldown = 0
        self.adjacent = []

    def total_units(self):
        return sum(self.units.values())

    def unit_value(self,value_weights):
        return sum(self.units.get(unit,0) * weight for unit,weight in value_weights.items())
    
#getting screen coordinates by subtracting camera value from the coordinates
    def get_coordinates(self,camera_pos,camera_zoom):
        points = []
        for coord in self.position:
            x = ((coord[0] - camera_pos[0]) * camera_zoom)
            y = ((coord[1] - camera_pos[1]) * camera_zoom)
            points.append((x,y))
        return points
    
    def get_colour(self,player,ai_players):
        if self.highlighted:
            return (255, 80, 80)
        if player and self in player.territories:
            return (0, 100, 255)
        count = 0
        for ai in ai_players:
            if self in ai.territories:
                return AI_COLOURS[count % len(AI_COLOURS)]
            count += 1
        if self.hovered and not self.highlighted:
            return (250, 220, 110)
        return self.colour

#drawing territory polygon along with the territory outline/border
    def draw(self, screen, camera_pos, camera_zoom, player, ai_players):
        colour = self.get_colour(player,ai_players)
        pygame.draw.polygon(screen,colour,self.get_coordinates(camera_pos,camera_zoom)) # taking surface,colour,converted points and width
        pygame.draw.polygon(screen,("white"),self.get_coordinates(camera_pos,camera_zoom),width=1)

    def check_hovered(self, position):
        if self.polygon.contains(position):
            self.hovered = True
        else:
            self.hovered = False
