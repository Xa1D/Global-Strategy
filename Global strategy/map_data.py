import geopandas as gpd
from shapely.geometry import mapping
import numpy as np
import json

geo_data = gpd.read_file("./ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp")
remove_list = ['Vatican','Jersey', 'Guernsey', 'Isle of Man','San Marino','Monaco','Russia','Liechtenstein','Aland','Faroe Islands','Andorra','Malta']
country_coords = {}
for index, country in geo_data[(geo_data.CONTINENT == "Europe") & (~geo_data.ADMIN.isin(remove_list))].iterrows():
    geojson_obj = mapping(country["geometry"].simplify(0.08))
    geo_coords = geojson_obj["coordinates"]
    main_index = np.argmax([len(coords[0]) for coords in geo_coords])
    country_coords[country["ADMIN"]] = geo_coords[main_index]
countries = {}
for country_name, country_coord in country_coords.items():
    while len(country_coord) < 5:
        country_coord = country_coord[0]
    countries[country_name] = country_coord
with open('country_coords.json', 'w') as f:
    json.dump(countries, f)