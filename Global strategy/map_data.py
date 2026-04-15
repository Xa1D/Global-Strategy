import geopandas
import json

geo_data = geopandas.read_file("./ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp")
remove = ['Vatican', 'Jersey', 'Guernsey', 'Isle of Man', 'San Marino','Monaco', 'Russia', 'Liechtenstein', 'Aland','Faroe Islands', 'Andorra', 'Malta']
countries = {}
for index, row in geo_data.iterrows():
    if row["CONTINENT"] == "Europe" and row["ADMIN"] not in remove:
        name = row["ADMIN"]
        shape = row["geometry"].simplify(0.08)
        if shape.geom_type == "MultiPolygon":
            parts = list(shape.geoms)
        else:
            parts = [shape]
        largest = parts[0]
        for part in parts:
            if len(part.exterior.coords) > len(largest.exterior.coords):
                largest = part
        coords = list(largest.exterior.coords)
        countries[name] = coords
with open("country_coords.py", "w") as file:
    file.write("countries = ")
    file.write(str(countries))