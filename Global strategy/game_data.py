import geopandas
import json

class GameData:
    def __init__(self,continent):
        self.continent = continent
        self.data = geopandas.read_file("./ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp")
        self.remove = self.get_remove()
        self.territories = self.get_territories()

    def get_remove(self):
        if self.continent == "Europe":
            remove = ["Russia", "Vatican", "Guernsey", "Liechtenstein",
                "Isle of Man", "San Marino", "Monaco", "Aland",
                "Faroe Islands", "Andorra", "Jersey", "Malta"]
        elif self.continent == "Asia":
            remove = ["Russia", "Cyprus", "Northern Cyprus",
                "Brunei", "Bahrain", "Singapore",
                "Maldives", "Timor-Leste", "Palestine","Taiwan", "Indian Ocean Territories", "East Timor"]
        elif self.continent == "Africa":
            remove = ["Antigua and Barbuda", "Barbados","Dominica",
            "Grenada","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines",
            "Trinidad and Tobago","Bahamas","Cuba", "Cabo Verde","São Tomé and Principe", "Comoros"]
        return remove
            
    def get_territories(self):
        territories = {}
        for i, row in self.data.iterrows():
            if row["CONTINENT"] == self.continent and row["ADMIN"] not in self.remove:
                name = row["ADMIN"]
                shape = row["geometry"].simplify(0.05)
                if shape.geom_type == "MultiPolygon":
                    parts = list(shape.geoms)
                else:
                    parts = [shape]
                largest = parts[0]
                for part in parts:
                    if part.area > largest.area:
                        largest = part
                coords = list(largest.exterior.coords)
                territories[name] = coords
        return territories

    def save(self):
        filename = f"{self.continent.lower()}_coords.json"
        with open(filename, "w") as file:
            json.dump(self.territories,file)

GameData("Europe").save()
GameData("Asia").save()
GameData("Africa").save()