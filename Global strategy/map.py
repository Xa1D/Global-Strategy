from territory import Territory
import json

MAP_SETTINGS = {"europe_coordinates.json": ("Europe", 8000, 4000),
                "asia_coordinates.json": ("Asia", 4000, 2000),
                "africa_coordinates.json": ("Africa", 4000, 2000)}

#loads selected map and constructs territory data to be used by the game
class Map:
    def __init__(self, map_file):
        self.file = map_file
        self.map, self.width, self.height = self.get_map_size()
        self.territories = {}
        self.territory_data = self.get_map_data()
        self.create_map()   

    #Decides the map size which determines the coordinate scaling - Europe is smaller so greater map size means Europe will appear larger
    def get_map_size(self):
        if self.file not in MAP_SETTINGS:
            raise ValueError(f"Unknown map file: {self.file}")
        name, width, height = MAP_SETTINGS[self.file]
        return name, width, height

    #reads the selected JSON file and returns the dictionary containing territory data 
    def get_map_data(self):
        try:
            with open(self.file,"r") as file:
                territory_data = json.load(file)
                return territory_data
        except Exception as error:
            raise RuntimeError(f"Could not load map file {self.file} : {error}")

    def create_map(self):
        self.get_territories()
        self.get_adjacent()
        self.get_units()

#converting longitude and latitude into map coordinates
    def get_territories(self):
        for name, territory_parts in self.territory_data.items():
            map_parts = []
            for part in territory_parts:
                map_coordinates = []
                for coord in part:
                    x = (self.width / 360) * (coord[0] + 180)
                    y = (self.height / 180) * (90 - coord[1])
                    map_coordinates.append((x, y))
                map_parts.append(map_coordinates)
            self.territories[name] = Territory(name, map_parts) #creates one territory containing all the country's parts
    
    def get_adjacent(self):
        # adding extra adjacency links for islands and disconnected territories
        if self.file == "europe_coordinates.json":
            extra_adjacent = {"United Kingdom": ["Ireland", "France", "Iceland"],
            "Ireland": ["United Kingdom", "Iceland"],
            "Iceland": ["United Kingdom", "Ireland"],
            "Denmark": ["Norway", "Sweden"],
            "Sweden": ["Denmark"],
            "Norway": ["Denmark"],
            "Finland": ["Estonia"],
            "Estonia": ["Finland"],
            "France": ["United Kingdom"]}

        elif self.file == "asia_coordinates.json":
            extra_adjacent = {"Japan": ["South Korea", "North Korea"],
            "South Korea": ["Japan"],
            "North Korea" : ["Japan"],
            "Sri Lanka": ["India"],
            "India": ["Sri Lanka"],
            "Philippines": ["Vietnam", "Malaysia"],
            "Vietnam": ["Philippines"],
            "Malaysia": ["Philippines"],
            "Indonesia": ["Malaysia"]}

        elif self.file == "africa_coordinates.json":
            extra_adjacent = {"Madagascar": ["Mozambique", "United Republic of Tanzania"],
            "Mozambique": ["Madagascar"],
            "United Republic of Tanzania": ["Madagascar"]}

        #compare each territory with every other one to check polygon intersection for adjacency
        for name, territory in self.territories.items():
            adjacent = []
            for neighbour_name, neighbour in self.territories.items():
                if name != neighbour_name:
                    if territory.shape.intersects(neighbour.shape):
                        adjacent.append(neighbour_name)
            if name in extra_adjacent:
                adjacent += extra_adjacent[name]
            territory.adjacent = list(set(adjacent))

    def get_units(self):
        #starting units determined by countries development, population and resources
        starting_units = {"Europe": {
            "Albania": 12, "Austria": 17, "Belarus": 14, "Belgium": 18,
            "Bosnia and Herzegovina": 12, "Bulgaria": 14, "Croatia": 16, "Czechia": 17,
            "Denmark": 18, "Estonia": 16, "Finland": 18, "France": 19,
            "Germany": 20, "Greece": 16, "Hungary": 15, "Iceland": 17,
            "Ireland": 18, "Italy": 18, "Latvia": 15, "Lithuania": 16,
            "Luxembourg": 15, "Moldova": 10, "Montenegro": 12, "Netherlands": 18,
            "North Macedonia": 11, "Norway": 18, "Poland": 17, "Portugal": 16,
            "Romania": 16, "Republic of Serbia": 14, "Slovakia": 16, "Slovenia": 17,
            "Spain": 18, "Sweden": 18, "Switzerland": 19, "Kosovo": 11,
            "Ukraine": 11, "United Kingdom": 19},

            "Asia": {
            "Afghanistan": 10, "Armenia": 12, "Azerbaijan": 14, "Bangladesh": 14,
            "Bhutan": 11, "Cambodia": 11, "China": 20, "Georgia": 13,
            "India": 19, "Indonesia": 17, "Iran": 16, "Turkey": 16, "Iraq": 13,
            "Israel": 17, "Japan": 19, "Jordan": 12, "Kazakhstan": 16,
            "Kuwait": 15, "Kyrgyzstan": 10, "Laos": 10, "Lebanon": 11,
            "Malaysia": 16, "Mongolia": 12, "Myanmar": 10, "Nepal": 11,
            "North Korea": 11, "Oman": 15, "Pakistan": 13, "Philippines": 14,
            "Qatar": 15, "Saudi Arabia": 17, "South Korea": 19, "Sri Lanka": 12,
            "Syria": 10, "Tajikistan": 10, "Thailand": 15, "Turkmenistan": 12,
            "United Arab Emirates": 16, "Uzbekistan": 13, "Vietnam": 15, "Yemen": 10},
            
            "Africa": {
            "Algeria": 15, "Angola": 13, "Benin": 10, "Botswana": 13,
            "Burkina Faso": 10, "Burundi": 10, "Cameroon": 12, "Central African Republic": 10,
            "Chad": 10, "Democratic Republic of the Congo": 14, "Republic of the Congo": 12, 
            "Egypt": 16, "Equatorial Guinea": 12, "Eritrea": 10, "eSwatini": 11,
            "Ethiopia": 13, "Gabon": 12, "Ghana": 14, "Guinea": 11, "Guinea-Bissau": 10, 
            "Ivory Coast": 14, "Kenya": 14, "United Republic of Tanzania": 13,
            "Liberia": 10, "Libya": 13, "Madagascar": 11,
            "Malawi": 10, "Mali": 10, "Mauritania": 11, "Morocco": 15,
            "Mozambique": 11, "Namibia": 13, "Niger": 10, "Nigeria": 16,
            "Rwanda": 12, "Senegal": 12, "Sierra Leone": 10, "Somalia": 10,
            "South Africa": 17, "South Sudan": 10, "Sudan": 10, "Djibouti": 10,
            "Togo": 10, "Tunisia": 14, "Uganda": 12, "Zambia": 12, "Zimbabwe": 12}}

        #starting units assigned - half as infantry, 1/6 as artillery and 1/3 as tank
        for territory in self.territories.values():
            units = starting_units[self.map].get(territory.name, 10)
            infantry_units = units // 2
            artillery_units = (units - infantry_units) // 3
            tank_units = units - infantry_units - artillery_units
            territory.units["infantry"] = infantry_units
            territory.units["tank"] = tank_units
            territory.units["artillery"] = artillery_units