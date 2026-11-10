from GUI import Camera
import pygame
from shapely.geometry import Point

#Displays the map and translates coordinates to screen positions
class MapDisplay:
    def __init__(self, map, screen):
        self.map = map  
        self.screen = screen
        self.camera = Camera(self.get_camera_pos(),self.get_camera_bounds(), self.screen)

    # Select initial camera offset for the continent - represents starting coordinates of top left of screen
    def get_camera_pos(self):
        if self.map.file == "europe_coordinates.json":
            return [3400, 400]
        elif self.map.file == "asia_coordinates.json":
            return [2200, 240]
        elif self.map.file == "africa_coordinates.json":
            return [1550, 500]

    #Calculate camera limits using territory bounds
    def get_camera_bounds(self):
        bounds = []
        for territory in self.map.territories.values():
            bounds.append(territory.shape.bounds)
        padding = 1000
        left = min(bound[0] for bound in bounds) - padding
        top = min(bound[1] for bound in bounds) - padding
        right = max(bound[2] for bound in bounds) + padding
        bottom = max(bound[3] for bound in bounds) + padding
        return left, top, right, bottom
    
#Converts mouse position on screen to a map coordinate - detect hovering and clicking a territory
    def get_map_pos(self):
        mouse_pos = pygame.mouse.get_pos()
        x = (mouse_pos[0] / self.camera.zoom) + self.camera.pos[0]
        y = (mouse_pos[1] / self.camera.zoom) + self.camera.pos[1]
        return (x, y)

    def update(self,events):
        self.camera.update(events)

    def draw(self, player, ai_players):
        position = Point(self.get_map_pos())    #create a shapely point for polygon checks
        for territory in self.map.territories.values():
            territory.check_hovered(position)
            territory.draw(self.screen, self.camera.pos, self.camera.zoom, player, ai_players)
