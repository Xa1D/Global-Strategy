import geopandas

#reading the file from natural earth and filtering the required countries
data = geopandas.read_file("./ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp")
remove = ['Russia', 'Vatican', 'Guernsey', 'Liechtenstein', 'Isle of Man', 'San Marino','Monaco', 'Aland','Faroe Islands', 'Andorra','Jersey', 'Malta']
countries = {}

for index, row in data.iterrows():
    if row["CONTINENT"] == "Europe" and row["ADMIN"] not in remove:
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
        countries[name] = coords

#saving dictionary to a file
with open("country_coords.py", "w") as file:
    file.write("countries = ")
    file.write(str(countries))