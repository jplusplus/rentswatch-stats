#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import csv as csv
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pylab
from PIL import Image
import urllib2
import urllib
import json
from math import radians, cos, sin, asin, sqrt

# From http://stackoverflow.com/a/4913653
def haversine(x, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    lon1 = x.longitude
    lat1 = x.latitude
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

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

# Converts string vars
table[['country']] = table[['country']].astype('S32')

# Makes city lowercase
table[['city']] = table['city'].str.lower()

# Prepares tables by city
cities = [
		{
			"name": "Paris",
			"landmarks": [ 
				{"longname": "Notre-Dame de Paris, France", "shortname":"Notre-Dame"}, 
				{"longname": "Stade-de-France, Saint-Denis", "shortname":"Stade-de-France"},
				{"longname": "Tour Eiffel, Paris", "shortname":"Tour Eiffel"},
				{"longname": "Place de la Défense, Puteaux, France", "shortname":"La Défense"},
				{"longname": "78 Rue du Général Leclerc, 94270 Le Kremlin-Bicêtre, France", "shortname":"Hôpital Bicêtre"}
			]
		},{
			"name": "Berlin",
			"landmarks": [ 
				{"longname": "Berlin Gesundbrunnen", "shortname":"Gesundbrunnen"}, 
				{"longname": "Alexanderplatz, Berlin", "shortname":"Alexanderplatz"},
				{"longname": "Zoologischer Garten, Berlin", "shortname":"Zoologischer Garten"},
				{"longname": "Hermannplatz, Berlin", "shortname":"Hermannplatz"},
				{"longname": "Rathaus Steglitz, Berlin", "shortname":"Rathaus Steglitz"}
			]
		}
	]

# Prepares the CSV with the data
csv = "city, square, price_per_sqm_reg, price_per_sqm_avg, std_err, num_obs, coords\n"

for city in cities:

	# Will hold the average price per square
	city_averages = []

	# Prepares the color scale
	Blues = plt.get_cmap('Blues')

	# Finds the coordinates of the city center
	url = 'http://nominatim.openstreetmap.org/search/?q=%s&format=json&limit=1' % urllib.quote_plus(city["name"])
	response = urllib2.urlopen(url)
	city_data = json.loads(response.read())
	center_lat = float(city_data[0]['lat'])
	center_lng = float(city_data[0]['lon'])

	# Size of the radius we need in km
	city_radius = 10

	# Approximate calculations from http://stackoverflow.com/a/1253545
	N_lat = center_lat + city_radius / 110.574
	S_lat = center_lat - city_radius / 110.574
	W_lng = center_lng - city_radius / (111.320 * cos(radians(center_lat)))
	E_lng = center_lng + city_radius / (111.320 * cos(radians(center_lat)))

	# Removes all records that aren't in a square around the city
	table_city = table[(table.latitude < N_lat) & (table.latitude > S_lat) & (table.longitude > W_lng) & (table.longitude < E_lng)]

	# Fetches watermark
	im = Image.open('images/logo.png')
	height = im.size[1]
	im = np.array(im).astype(np.float) / 255

	# Creates the figure
	figure = plt.figure(1, figsize=(8, 8), dpi=80)
	ax = figure.add_subplot(111)
	plt.ylabel('longitude')
	plt.xlabel('latitude')
	plt.ylim([S_lat,N_lat])
	plt.xlim([W_lng,E_lng])

	# Width of the squares in km
	square_width = 2

	# Switch for the text in the squares
	first_square = True

	# Iterates through a grid of squares of square_width km²
	for j_lat in range (0, int((city_radius/square_width) * 2)):
		for i_lng in range (0, int((city_radius/square_width) * 2)):

			# Initiate the price per sqm
			m = None

			# Names the square, starting with A0 on the top left
			square_name = chr(i_lng + 97) + "-" + str(j_lat)

			# Computes the bounds of the square
			N_lat_square = S_lat + (city_radius * 2 - square_width * j_lat) / 110.574
			S_lat_square = N_lat_square - square_width / 110.574
			W_lng_square = E_lng - (city_radius * 2 - square_width * i_lng) / (111.320 * cos(radians(center_lat)))
			E_lng_square = W_lng_square + square_width / (111.320 * cos(radians(center_lat)))

			# Removes all records that aren't in the square
			table_square = table_city[(table_city.latitude < N_lat_square) & (table_city.latitude > S_lat_square) & (table_city.longitude > W_lng_square) & (table_city.longitude < E_lng_square)]

			# Number of obs
			numobs = len(table_square.index)

			if numobs > 3:
				model = smf.ols(formula='total_rent ~ living_space - 1', data=table_square)
				results = model.fit()
				m = results.params.living_space

				# Appends data to CSV
				csv += '"' + city["name"] + '",'
				csv += square_name + ','
				csv += str(m) + ',' 
				csv += str(table_square['price_per_sqm'].mean()) + ','
				csv += str(results.bse.living_space) + ','
				csv += str(numobs) + ','
				csv += '"'+str(N_lat_square)+','+str(W_lng_square)+'"'
				csv +='\n'
				# Color is max if rent is 40€/m²
				fill = Blues(m/40)
				city_averages.append(m)
			else:
				csv += '"' + city["name"] + '", ' + square_name + ',n/a,n/a,n/a,' + str(numobs) + '\n'
				fill = "none"

			# Adds the rectangle to the image
			ax.add_patch(
			    patches.Rectangle(
					(W_lng_square, S_lat_square),   # (x,y)
					E_lng_square - W_lng_square,    # width
					N_lat_square - S_lat_square,    # height
					facecolor=fill,		  			# color
					edgecolor="none"				#border
				)
			)

			if m is not None:
				# Adds the price to the square and "€/m²" for the first one
				if first_square == False:
					text_square = str(round(m))[:-2]
				else:
					first_square = False
					text_square = str(round(m))[:-2] + "€/m²".decode("utf-8")
				ax.annotate(
					text_square, 
					xy= (W_lng_square, S_lat_square),
					xytext=(W_lng_square, S_lat_square),
					alpha=.3,
					fontsize=10
			)


	# Finds the coordinates of the landmarks
	if "landmarks" in city:
		for landmark in city["landmarks"]:
			url = 'http://nominatim.openstreetmap.org/search/?q=%s&format=json&limit=1' % urllib.quote_plus(landmark["longname"])
			response = urllib2.urlopen(url)
			landmark_data = json.loads(response.read())
			landmark_lat = float(landmark_data[0]['lat'])
			landmark_lng = float(landmark_data[0]['lon'])

			# Places the landmark on the graph
			ax.plot(landmark_lng, landmark_lat, 'bo')
			ax.annotate(
				landmark["shortname"].decode('utf-8'), 
				xy=(landmark_lng, landmark_lat), 
				xytext=(landmark_lng + .004, landmark_lat - 0.001)
			)

	# Removes axes
	plt.axis('off')

	# Adds title
	plt.title(city["name"].capitalize() + "\nThe side of each square is " +str(square_width)+ " km. The color represents the average rent price.")

	# Makes layout more legible
	figure.tight_layout()

	# Saves image
	pylab.savefig('analyses/inequalities/graph-'+ city["name"] +'.png')

# Saves CSV
f = open("analyses/inequalities/table.csv", "w")
f.write(csv)
f.close()