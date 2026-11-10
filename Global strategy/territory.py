from shapely.geometry import Polygon, MultiPolygon
import pygame
from ui_config import AI_COLOURS, PLAYER_COLOUR, NEUTRAL_COLOUR, HOVER_COLOUR, HIGHLIGHT_COLOUR

class Territory:
    def __init__(self, name, coordinates):
        self.position = coordinates  #stores map coordinates for territory
        self.name = name
        self.owner = None
        self.polygons = []
        for part in self.position:
            self.polygons.append(Polygon(part))  #creates a shapely polygon using the exterior map coordinates
        self.shape = MultiPolygon(self.polygons)
        self.colour = NEUTRAL_COLOUR
        self.combat, self.highlighted, self.hovered = False, False, False
        self.units = {}  #stores unit counts of each unit type
        self.attack_cooldown = 0
        self.adjacent = []

    def total_units(self):
        return sum(self.units.values())

    def unit_value(self,value_weights):
        return sum(self.units.get(unit,0) * weight for unit,weight in value_weights.items())
    
#converts map coordinates to screen coordinates 
    def get_coordinates(self, camera_pos, camera_zoom):
        screen_coordinates = []
        for part in self.position:
            points = []
            for coord in part:
                x = (coord[0] - camera_pos[0]) * camera_zoom  #subtract camera position to obtain the screen position then multiply by camera zoom
                y = (coord[1] - camera_pos[1]) * camera_zoom
                points.append((x, y))
            screen_coordinates.append(points)
        return screen_coordinates
    
    def get_colour(self,player,ai_players):
        if self.highlighted:
            return HIGHLIGHT_COLOUR
        if player and self in player.territories:
            return PLAYER_COLOUR
        count = 0
        for ai in ai_players:
            if self in ai.territories:
                return AI_COLOURS[count % len(AI_COLOURS)]
            count += 1
        if self.hovered and not self.highlighted:
            return HOVER_COLOUR
        return self.colour

#drawing territory polygon along with the territory outline/border
    def draw(self, screen, camera_pos, camera_zoom, player, ai_players):
        colour = self.get_colour(player,ai_players)
        screen_coordinates = self.get_coordinates(camera_pos, camera_zoom)
        for coordinates in screen_coordinates:
            pygame.draw.polygon(screen,colour, coordinates) #draws polygon using screen coordinates and colour
            pygame.draw.polygon(screen,("white"), coordinates, width=1) #draws polygon outline

    def check_hovered(self, position):
        min_x, min_y, max_x, max_y = self.shape.bounds
        if not(min_x <= position.x <= max_x and min_y <= position.y <= max_y):
            self.hovered = False
            return
        self.hovered = self.shape.contains(position)
