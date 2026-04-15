import pygame
from shapely.geometry import Point, Polygon
from country_coords import countries

class Country:
    def __init__(self, name, coords):
        self.name = name
        self.coords = coords 
        self.polygon = Polygon(self.coords)
        self.center = self.get_center()
        self.color = (128, 128, 128)
        self.hovered = False
        self.highlighted = False
        self.attack_cooldown = 0
        self.combat = False

    def update(self, mouse_pos):
        self.hovered = False
        if Point(mouse_pos.x, mouse_pos.y).within(self.polygon):
            self.hovered = True

    def draw(self, screen, scroll, player,enemy):
        if self.highlighted:
            colour = (255, 150, 0)
        elif player and self in player.territories:
          colour = (0, 100, 255) 
        elif enemy and self in enemy.territories:
            colour = (0,255,0)
        elif self.hovered and not self.highlighted:
          colour = (255, 0, 0) 
        else:
          colour = self.color     
        pygame.draw.polygon(screen,colour,[(x - scroll.x, y - scroll.y) for x, y in self.coords],)
        pygame.draw.polygon(screen,(255, 255, 255),[(x - scroll.x, y - scroll.y) for x, y in self.coords],width=1,)
       
    def get_center(self):
      x = sum([x for x, y in self.coords]) / len(self.coords)
      y = sum([y for x, y in self.coords]) / len(self.coords)
      return pygame.Vector2(x, y)


class Map:

    def __init__(self):
        self.width = 8000
        self.height = 4000
        self.geo_data = countries
        self.countries = self.create_countries()
        self.get_units()
        self.create_neighbours()
        self.scroll = pygame.Vector2(3500, 500)
        self.font = pygame.font.SysFont(None, 24)
        self.hovered_country = None

    def create_countries(self):
        countries = {}
        for name, coords in self.geo_data.items():
            map_coords = []
            for coord in coords:
                x = (self.width / 360) * (180 + coord[0])
                y = (self.height / 180) * (90 - coord[1])
                map_coords.append(pygame.Vector2(x, y))
            countries[name] = Country(name, map_coords)
        return countries

    def draw(self, screen, player, enemy):
     for country in self.countries.values():
            country.draw(screen, self.scroll, player,enemy)

    def update(self):
        self.update_camera()
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_country = None
        for country in self.countries.values():
            country.update(pygame.Vector2(mouse_pos[0] + self.scroll.x, mouse_pos[1] + self.scroll.y))
            if country.hovered:
                self.hovered_country = country

    def update_camera(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.scroll.x -= 10
        if keys[pygame.K_d]:
            self.scroll.x += 10
        if keys[pygame.K_w]:
            self.scroll.y -= 10
        if keys[pygame.K_s]:
            self.scroll.y += 10
        if keys[pygame.K_SPACE]:
            self.scroll = pygame.Vector2(3650, 395)
        
    def create_neighbours(self):
        for name, country in self.countries.items():
            country.neighbours = self.get_country_neighbours(name)

    def get_units(self):
      starting_units = {"United Kingdom": 20,"Ukraine": 12,"Switzerland": 8,"Sweden": 7,"Spain": 15,"Slovakia": 5,"Slovenia": 5,
"Republic of Serbia": 5,"Romania": 5,"Portugal": 5,"Poland": 15,"Norway": 10,"Netherlands": 12,"Montenegro": 5,"Moldova": 5,"North Macedonia": 5,
"Luxembourg": 5,"Lithuania": 5,"Latvia": 5,"Kosovo": 15,"Italy": 20,"Ireland": 10,"Iceland": 10,"Hungary": 10,
"Greece": 10,"Germany": 20,"France": 20,"Finland": 10,"Estonia": 8,"Denmark": 10,"Czechia": 7,"Croatia": 10,"Bulgaria": 10,"Bosnia and Herzegovina": 6,
"Belgium": 10, "Belarus": 8,"Austria": 12,"Albania": 10}
      for country in self.countries.values():
        country.units = starting_units.get(country.name, 5)

    def get_country_neighbours(self, country):
        neighbours = []
        country_polygon = self.countries[country].polygon
        for other_country_key, other_country_value in self.countries.items():
            if country != other_country_key:
                if country_polygon.intersects(other_country_value.polygon):
                    neighbours.append(other_country_key)
        if country == "United Kingdom":
            neighbours += ["Ireland", "France", "Iceland"]
        elif country == "Ireland":
            neighbours += ["United Kingdom", "Iceland"]
        elif country == "Iceland":
            neighbours += ["United Kingdom", "Ireland"]
        elif country == "France":
            neighbours += ["United Kingdom"]
        elif country == "Denmark":
            neighbours += ["Norway", "Sweden"]
        elif country == "Norway":
            neighbours += ["Denmark"]
        elif country == "Sweden":
            neighbours += ["Denmark"]
        elif country == "Finland":
            neighbours += ["Estonia"]
        elif country == "Estonia":
            neighbours += ["Finland"]
        
        return neighbours

            