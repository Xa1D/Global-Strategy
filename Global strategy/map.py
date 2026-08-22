import pygame
from shapely.geometry import Point
from GUI import Camera
from territory import Territory
import json

class Map:
    def __init__(self, map_file):
        self.file = map_file
        self.width, self.height = self.get_size()
        self.countries = {}
        self.country_data = self.get_map_data()
        self.create_map()   

    def get_size(self):
        if self.file == "europe_coords.json":
            width, height = 8000, 4000
        elif self.file == "asia_coords.json":
            width, height = 4000, 2000
        elif self.file == "africa_coords.json":
            width, height = 4000, 2000
        return width, height
        
    def get_map_data(self):
        with open(self.file,"r") as file:
            country_data = json.load(file)
        return country_data

    def create_map(self):
        self.get_countries()
        self.get_adjacent()
        self.get_units()

#converting longitude and latitude into screen coordinates
    def get_countries(self):
        for name,coords in self.country_data.items():
          map_coords = []
          for coord in coords:
              x = (self.width / 360) * (coord[0] + 180)
              y = (self.height / 180) * (90 - coord[1])
              map_coords.append((x, y))
          self.countries[name] = Territory(name, map_coords)
        
    def get_adjacent(self):
        if self.file == "europe_coords.json":
            extra_adjacent = {"United Kingdom": ["Ireland", "France", "Iceland"],
            "Ireland": ["United Kingdom", "Iceland"],
            "Iceland": ["United Kingdom", "Ireland"],
            "Denmark": ["Norway", "Sweden"],
            "Sweden": ["Denmark"],
            "Norway": ["Denmark"],
            "Finland": ["Estonia"],
            "Estonia": ["Finland"],
            "France": ["United Kingdom"]}

        elif self.file == "asia_coords.json":
            extra_adjacent = {"Japan": ["South Korea", "China"],
            "South Korea": ["Japan"],
            "Sri Lanka": ["India"],
            "India": ["Sri Lanka"],
            "Philippines": ["Vietnam", "Malaysia"],
            "Vietnam": ["Philippines"],
            "Malaysia": ["Philippines"],
            "Indonesia": ["Malaysia"]}

        elif self.file == "africa_coords.json":
            extra_adjacent = {"Madagascar": ["Mozambique", "United Republic of Tanzania", "Comoros"],
            "Mozambique": ["Madagascar", "Comoros"],
            "United Republic of Tanzania": ["Madagascar", "Comoros"],
            "Comoros": ["Madagascar", "Mozambique", "United Republic of Tanzania"],
            "São Tomé and Principe": ["Gabon", "Cameroon"],
            "Gabon": ["São Tomé and Principe"],
            "Cameroon": ["São Tomé and Principe"]}

        for name, country in self.countries.items():
            adjacent = []
            for neighbour_name, neighbour in self.countries.items():
                if name != neighbour_name:
                    if country.polygon.intersects(neighbour.polygon):
                        adjacent.append(neighbour_name)
            if name in extra_adjacent:
                adjacent += extra_adjacent[name]
            country.adjacent = list(set(adjacent))

    def get_units(self):
      starting_units = {"United Kingdom": 20,"Ukraine": 12,"Switzerland": 8,"Sweden": 9,"Spain": 15,"Slovakia": 5,"Slovenia": 5,
"Republic of Serbia": 5,"Romania": 5,"Portugal": 5,"Poland": 15,"Norway": 10,"Netherlands": 12,"Montenegro": 5,"Moldova": 5,"North Macedonia": 5,
"Luxembourg": 5,"Lithuania": 5,"Latvia": 5,"Kosovo": 15,"Italy": 20,"Ireland": 10,"Iceland": 10,"Hungary": 10,
"Greece": 10,"Germany": 20,"France": 20,"Finland": 10,"Estonia": 8,"Denmark": 10,"Czechia": 7,"Croatia": 10,"Bulgaria": 10,"Bosnia and Herzegovina": 6,
"Belgium": 10, "Belarus": 8,"Austria": 12,"Albania": 10}
      
      for country in self.countries.values():
        units = starting_units.get(country.name,10)
        infantry_units = units // 2
        artillery_units = (units - infantry_units) // 3
        tank_units = units - infantry_units - artillery_units
        country.units["infantry"] = infantry_units
        country.units["tank"] = tank_units
        country.units["artillery"] = artillery_units


class MapDisplay:
    def __init__(self, map, screen):
        self.map = map
        self.screen = screen
        self.camera = Camera(self.get_camera_pos())

    def get_camera_pos(self):
        if self.map.file == "europe_coords.json":
            return [3500, 500]
        elif self.map.file == "asia_coords.json":
            return [2400, 240]
        elif self.map.file == "africa_coords.json":
            return [1700, 500]

    def get_map_pos(self):
        mouse_pos = pygame.mouse.get_pos()
        x = (mouse_pos[0] / self.camera.zoom) + self.camera.pos[0]
        y = (mouse_pos[1] / self.camera.zoom) + self.camera.pos[1]
        return (x, y)

    def update(self,events):
        self.camera.update(events)

    def draw(self, player, ai_players):
        position = Point(self.get_map_pos())
        for country in self.map.countries.values():
            country.check_hovered(position)
            country.draw(self.screen, self.camera.pos, self.camera.zoom, player, ai_players)

            