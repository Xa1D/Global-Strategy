import pygame
from country_coords import countries
from GUI import Camera
from country import Country

class Map:
    def __init__(self):
        self.width = 8000
        self.height = 4000
        self.country_data = countries
        self.countries = {}
        self.create_map()
        self.font = pygame.font.SysFont(None, 24)
        self.hovered_country = None
        self.camera = Camera()

    def create_map(self):
        self.get_countries()
        self.get_adjacent()
        self.get_units()

#converting longitude and latitude into screen coordinates
    def get_countries(self):
        for name,coords in self.country_data.items():
          map_coords = []
          for coord in coords:
              x = (self.width / 360) * (180 + coord[0])
              y = (self.height / 180) * (90 - coord[1])
              map_coords.append((x, y))
          self.countries[name] = Country(name, map_coords)

    def draw(self, screen, player, enemy):
     for country in self.countries.values():
        country.draw(screen, self.camera.pos, player,enemy)

    def get_world_pos(self):
        mouse_pos = pygame.mouse.get_pos()
        return pygame.Vector2(mouse_pos) + self.camera.pos

    def update(self):
        self.camera.update()
        self.hovered_country = None
        world_pos = self.get_world_pos()
        for country in self.countries.values():
            country.update(world_pos)
            if country.hovered:
                self.hovered_country = country
        
    def get_adjacent(self):
        for name, country in self.countries.items():
            country.adjacent = self.create_adjacent_countries(name)

    def get_units(self):
      starting_units = {"United Kingdom": 20,"Ukraine": 12,"Switzerland": 8,"Sweden": 9,"Spain": 15,"Slovakia": 5,"Slovenia": 5,
"Republic of Serbia": 5,"Romania": 5,"Portugal": 5,"Poland": 15,"Norway": 10,"Netherlands": 12,"Montenegro": 5,"Moldova": 5,"North Macedonia": 5,
"Luxembourg": 5,"Lithuania": 5,"Latvia": 5,"Kosovo": 15,"Italy": 20,"Ireland": 10,"Iceland": 10,"Hungary": 10,
"Greece": 10,"Germany": 20,"France": 20,"Finland": 10,"Estonia": 8,"Denmark": 10,"Czechia": 7,"Croatia": 10,"Bulgaria": 10,"Bosnia and Herzegovina": 6,
"Belgium": 10, "Belarus": 8,"Austria": 12,"Albania": 10, "Malta": 6}
      
      for country in self.countries.values():
        units = starting_units[country.name]
        infantry_units = units // 2
        artillery_units = (units - infantry_units) // 3
        tank_units = units - infantry_units - artillery_units
        country.units["infantry"] = infantry_units
        country.units["tank"] = tank_units
        country.units["artillery"] = artillery_units

#adding adjacent countries which do not intersect
    def add_adjacent_countries(self,country,adjacent):
        if country == "United Kingdom":
            adjacent += ["Ireland", "France", "Iceland"]
        elif country == "Ireland":
            adjacent += ["United Kingdom", "Iceland"]
        elif country == "Iceland":
            adjacent += ["United Kingdom", "Ireland"]
        elif country == "France":
            adjacent += ["United Kingdom"]
        elif country == "Denmark":
            adjacent += ["Norway", "Sweden"]
        elif country == "Norway":
            adjacent += ["Denmark"]
        elif country == "Sweden":
            adjacent += ["Denmark"]
        elif country == "Finland":
            adjacent += ["Estonia"]
        elif country == "Estonia":
            adjacent += ["Finland"]
        return adjacent

#storing adjacent countries through checking if their polygons intersect
    def create_adjacent_countries(self, country):
        adjacent = []
        country_polygon = self.countries[country].polygon
        for name, neighbour in self.countries.items():
            if country != name:
                if country_polygon.intersects(neighbour.polygon):
                    adjacent.append(name)
        adjacent = self.add_adjacent_countries(country,adjacent)
        return list(set(adjacent))
            