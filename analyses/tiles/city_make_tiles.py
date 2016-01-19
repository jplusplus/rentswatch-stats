#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import csv as csv
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import math, os, json

# from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def num2deg(xtile, ytile, zoom):
	n = 2.0 ** zoom
	lon_deg = xtile / n * 360.0 - 180.0
	lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
	lat_deg = math.degrees(lat_rad)
	return (lat_deg, lon_deg)

def deg2num(lat_deg, lon_deg, zoom):
	lat_rad = math.radians(lat_deg)
	n = 2.0 ** zoom
	xtile = int((lon_deg + 180.0) / 360.0 * n)
	ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
	return (xtile, ytile)

# Open cities list
readdata_cities = csv.reader(open("analyses/tiles/cities_eur.csv"))

cities = []

for row in readdata_cities:
	cities.append(row)
cities.pop(0)

# Opens data
readdata = csv.reader(open("data/20151208/ad.csv"))

data = []

for row in readdata:
	data.append(row)

# Save header
Header = data[0]

# Remove header from data
data.pop(0)

# Organize the data in a table
table = pd.DataFrame(data, columns=Header)

# Removes values where price_per_sqm or lat is NULL

table = table[table.price_per_sqm != "NULL"]
table = table[table.latitude != "NULL"]
table = table[table.longitude != "NULL"]

# Converts price, area and price_per_sqm to float

table[['total_rent']] = table[['total_rent']].astype(float)
table[['living_space']] = table[['living_space']].astype(float)
table[['price_per_sqm']] = table[['price_per_sqm']].astype(float)
table[['latitude']] = table[['latitude']].astype(float)
table[['longitude']] = table[['longitude']].astype(float)

# These are the bounds of Europe
N_max = 72
E_max = 34
W_max = -13
S_max = 33

#Each tile is divided in 100x100 squares
squares_per_tile = 10

# Loops through all zoom levels
for zoom_level in range(4,5):

	#Loops through all cities
	for city in cities:

		print city[0],
		
		city_lat = float(city[2])
		city_lng = float(city[1])

		#Finds out which tile the city is in
		X_city, Y_city = deg2num(city_lat, city_lng, zoom_level)
		
		for X in range(X_city - 2, X_city + 2):
			for Y in range (Y_city - 2, Y_city + 2):

				print X, Y,

				# Checks if tile exists
				zoom_dir = "tiles_city/" + str(zoom_level)
				X_dir = zoom_dir + '/' + str(X)
				tile_filename = X_dir + '/' + str(Y) + '.geojson'
				if os.path.isfile(tile_filename) == True:
					print "Tile has been done"
				else:
					print "Tile in progress"

					# Bounds of the tile
					N_tile, W_tile = num2deg(X, Y, zoom_level)
					S_tile, E_tile = num2deg(X + 1, Y + 1, zoom_level)

					# Tile size in degrees
					tile_width = 360 / math.pow(2, zoom_level)

					# Init the geojson file that will contain all squares
					geojson = {
							"type": "FeatureCollection",
								"features": []
								}

					# Makes the tile
					for x in range (0, squares_per_tile):
						for y in range  (0,squares_per_tile):
							# Finds the bounds of the square
							tile_height = N_tile - S_tile
							W_square = W_tile + x * (tile_width / squares_per_tile)
							E_square = W_square + tile_width / squares_per_tile
							N_square = N_tile - y * (tile_height / squares_per_tile)
							S_square = N_square - tile_height / squares_per_tile

							# Removes all records that aren't in a square around the city
							table_square = table[(table.latitude < N_square) & (table.latitude > S_square) & (table.longitude > W_square) & (table.longitude < E_square)]

							# Number of obs
							numobs = len(table_square.index)

							if numobs > 3:
								model = smf.ols(formula='total_rent ~ living_space - 1', data=table_square)
								results = model.fit()
								m = results.params.living_space
								square = {
											"type": "Feature",
										  	"geometry": {
												"type": "Polygon",
												"coordinates": [[
													[W_square, N_square],
													[W_square, S_square],
													[E_square, S_square],
													[E_square, N_square],
													[W_square, N_square]
												]]
												},
										  	"properties" : {
										  		"price_per_sqm" : m
										  	}
										  }
								geojson["features"].append(square)
							# End of square

					# Creates the dirs if required
					if not os.path.exists(zoom_dir):
						os.makedirs(zoom_dir)
					if not os.path.exists(X_dir):
						os.makedirs(X_dir)

					with open(tile_filename, 'w') as tile_file:
						json.dump(geojson, tile_file)
					# End of tile generation
		# End of city loop

	# End of zoom loop