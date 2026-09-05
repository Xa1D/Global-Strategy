import pygame
from shapely.geometry import Point
from GUI import Camera
from territory import Territory
import json

class Map:
    def __init__(self, map_file):
        self.file = map_file
        self.width, self.height, self.map = self.get_map_size()
        self.territories = {}
        self.territory_data = self.get_map_data()
        self.create_map()   

    def get_map_size(self):
        if self.file == "europe_coords.json":
            width, height = 8000, 4000
            map = "Europe"
        elif self.file == "asia_coords.json":
            width, height = 4000, 2000
            map = "Asia"
        elif self.file == "africa_coords.json":
            width, height = 4000, 2000
            map = "Africa"
        return width, height, map
        
    def get_map_data(self):
        with open(self.file,"r") as file:
            territory_data = json.load(file)
        return territory_data

    def create_map(self):
        self.get_territories()
        self.get_adjacent()
        self.get_units()

#converting longitude and latitude into screen coordinates
    def get_territories(self):
        for name,coords in self.territory_data.items():
          map_coords = []
          for coord in coords:
              x = (self.width / 360) * (coord[0] + 180)
              y = (self.height / 180) * (90 - coord[1])
              map_coords.append((x, y))
          self.territories[name] = Territory(name, map_coords)
        
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
            extra_adjacent = {"Madagascar": ["Mozambique", "United Republic of Tanzania"],
            "Mozambique": ["Madagascar"],
            "United Republic of Tanzania": ["Madagascar"]}

        for name, territory in self.territories.items():
            adjacent = []
            for neighbour_name, neighbour in self.territories.items():
                if name != neighbour_name:
                    if territory.polygon.intersects(neighbour.polygon):
                        adjacent.append(neighbour_name)
            if name in extra_adjacent:
                adjacent += extra_adjacent[name]
            territory.adjacent = list(set(adjacent))

    def get_units(self):
        starting_units = {"Europe": {
            # Europe
            "Albania": 12, "Austria": 17, "Belarus": 16,
            "Belgium": 18, "Bosnia and Herzegovina": 13, "Bulgaria": 14, "Croatia": 14,
            "Cyprus": 12, "Czechia": 17, "Denmark": 16, "Estonia": 13,
            "Finland": 16, "France": 20, "Germany": 20, "Greece": 16,
            "Hungary": 16, "Iceland": 11, "Ireland": 16, "Italy": 19,
            "Kosovo": 12, "Latvia": 13, "Liechtenstein": 10, "Lithuania": 14,
            "Luxembourg": 11, "Malta": 11, "Moldova": 11, "Monaco": 10,
            "Montenegro": 11, "Netherlands": 18, "North Macedonia": 12, "Norway": 17,
            "Poland": 18, "Portugal": 15, "Romania": 17, "Russia": 20,
            "San Marino": 10, "Republic of Serbia": 14, "Slovakia": 15, "Slovenia": 14,
            "Spain": 18, "Sweden": 17, "Switzerland": 17, "Turkey": 20,
            "Ukraine": 17, "United Kingdom": 20, "Vatican": 10},
            "Asia": {
            "Afghanistan": 10, "Armenia": 11, "Azerbaijan": 14, "Bahrain": 13,
            "Bangladesh": 17, "Bhutan": 10, "Brunei": 11, "Cambodia": 12,
            "China": 20, "Georgia": 12, "India": 20, "Indonesia": 18,
            "Iran": 18, "Iraq": 15, "Israel": 16, "Japan": 19,
            "Jordan": 12, "Kazakhstan": 15, "Kuwait": 14, "Kyrgyzstan": 10,
            "Laos": 10, "Lebanon": 11, "Malaysia": 16, "Maldives": 10,
            "Mongolia": 11, "Myanmar": 12, "Nepal": 11, "North Korea": 14,
            "Oman": 14, "Pakistan": 17, "Philippines": 15, "Qatar": 13,
            "Saudi Arabia": 17, "Singapore": 13, "South Korea": 19, "Sri Lanka": 12,
            "Syria": 10, "Tajikistan": 10, "Thailand": 16,
            "Turkmenistan": 12, "United Arab Emirates": 15, "Uzbekistan": 14, "Vietnam": 16,
            "Yemen": 10, "Taiwan": 16, "Palestine": 10},
            "Africa": {
            "Algeria": 16, "Angola": 14, "Benin": 11, "Botswana": 13,
            "Burkina Faso": 10, "Burundi": 10, "Cameroon": 13,
            "Central African Republic": 10, "Chad": 11, "Republic of Congo": 12,
            "Democratic Republic of the Congo": 15, "Ivory Coast": 14, "Djibouti": 10, "Egypt": 17,
            "Equatorial Guinea": 12, "Eritrea": 10, "eSwatini": 11, "Ethiopia": 14,
            "Gabon": 13, "Gambia": 10, "Ghana": 15, "Guinea": 11,
            "Guinea-Bissau": 10, "Kenya": 15, "Lesotho": 10, "Liberia": 10,
            "Libya": 13, "Madagascar": 11, "Malawi": 10, "Mali": 11,
            "Mauritania": 12, "Mauritius": 12, "Morocco": 16, "Mozambique": 12,
            "Namibia": 13, "Niger": 10, "Nigeria": 18, "Rwanda": 11,
            "Senegal": 13, "Seychelles": 10, "Sierra Leone": 10,
            "Somalia": 10, "South Africa": 18, "South Sudan": 10, "Sudan": 12,
            "United Republic of Tanzania": 14, "Togo": 11, "Tunisia": 15, "Uganda": 14,
            "Zambia": 13, "Zimbabwe": 12}}

        for territory in self.territories.values():
            units = starting_units[self.map].get(territory.name, 10)
            infantry_units = units // 2
            artillery_units = (units - infantry_units) // 3
            tank_units = units - infantry_units - artillery_units
            territory.units["infantry"] = infantry_units
            territory.units["tank"] = tank_units
            territory.units["artillery"] = artillery_units


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
        for territory in self.map.territories.values():
            territory.check_hovered(position)
            territory.draw(self.screen, self.camera.pos, self.camera.zoom, player, ai_players)

            