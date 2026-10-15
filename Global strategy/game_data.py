import geopandas
import json

class GameData:
    def __init__(self,continent):
        self.continent = continent
        #loads shapefile into a table with country information and shape type
        self.data = geopandas.read_file("./ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp")
        self.remove = self.get_remove()
        self.territories = self.get_territories()

    #return excluded country names
    def get_remove(self):
        if self.continent == "Europe":
            remove = ["Russia", "Vatican", "Guernsey", "Liechtenstein",
                "Isle of Man", "San Marino", "Monaco", "Aland",
                "Faroe Islands", "Andorra", "Jersey", "Malta"]
        elif self.continent == "Asia":
            remove = ["Russia", "Cyprus", "Northern Cyprus",
                "Brunei", "Bahrain", "Singapore",
                "Maldives", "Timor-Leste", "Palestine","Taiwan", "Indian Ocean Territories", "East Timor", "Hong Kong S.A.R.", "Macao S.A.R"]
        elif self.continent == "Africa":
            remove = ["Antigua and Barbuda", "Barbados","Dominica",
            "Grenada","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines",
            "Trinidad and Tobago","Bahamas","Cuba", "Cabo Verde","São Tomé and Principe", "Comoros"]
        return remove

    #builds a dictionary with country names along with corresponding coordinates    
    def get_territories(self):
        territories = {}
        for i, row in self.data.iterrows(): #read each country record 
            if row["CONTINENT"] == self.continent and row["ADMIN"] not in self.remove: #checking continent and country name not in excluded
                name = row["ADMIN"]
                shape = row["geometry"].simplify(0.05) #simplifies outline by reducing number of vertices 
                minimum_area = 0.05
                min_longitude, min_latitude, max_longitude, max_latitude = -35, 35, 50, 90
                if shape.geom_type == "MultiPolygon":
                    parts = list(shape.geoms)
                else:
                    parts = [shape]
                coordinates = []
                for part in parts:
                    left, bottom, right, top = part.bounds
                    valid = True
                    if row["CONTINENT"] == "Europe":
                        if left >= min_longitude and right <= max_longitude and bottom >= min_latitude and top <= max_latitude:
                            valid = True
                        else:
                            valid = False
                    if part.area > minimum_area and valid:
                        coordinates.append(list(part.exterior.coords))
                territories[name] = coordinates
        return territories

    def save(self):
        filename = f"{self.continent.lower()}_coordinates.json"
        with open(filename, "w") as file:
            json.dump(self.territories,file)  #create a JSON file with the corresponding filename and write the territories dictionary to it

#Saving a file for each map available
GameData("Europe").save()
GameData("Asia").save()
GameData("Africa").save()