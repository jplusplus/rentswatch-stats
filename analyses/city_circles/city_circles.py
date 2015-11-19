#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import csv as csv
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
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

readdata = csv.reader(open("data/20151113/ads.csv"))

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

cities = ["Place de la République, Paris", 
		  "Avenue Hoche, Paris", 
		  "Porte de Pantin, Paris", 
		  "Père-Lachaise, Paris", 
		  "Quartier Latin, Paris", 
		  "La Courneuve - Aubervilliers, France",
		  "Saint-Denis RER, France",
		  "Gare de Noisy-le-sec, France",
		  "Vitry-sur-Seine RER, France",
		  "Rosenthaler Platz, Berlin", 
		  "Savignyplatz, Berlin",
		  "Monbijouplatz, Berlin",
		  "Paul-Lincke Ufer, Berlin",
		  "Kollwitzplatz, Berlin",
		  "Frankfurter Tor, Berlin",
		  "Dahlem-Dorf, Berlin",
		  "Bhf Lichtenberg, Berlin"]

# Prepares the CSV with the data

csv = "city, price_per_sqm_reg, price_per_sqm_avg, std_err, num_obs, lat, lng\n"

for city in cities:

	# Finds the coordinates of the city center
	url = 'http://nominatim.openstreetmap.org/search/?q=%s&format=json&limit=1' % urllib.quote_plus(city)
	response = urllib2.urlopen(url)
	city_data = json.loads(response.read())
	center_lat = float(city_data[0]['lat'])
	center_lng = float(city_data[0]['lon'])

	# Size of the radius we need in km
	city_radius = 1.5

	# Approximate calculations from http://stackoverflow.com/a/1253545
	N_lat = center_lat + city_radius / 110.574
	S_lat = center_lat - city_radius / 110.574
	W_lng = center_lng - city_radius / (111.320 * cos(radians(center_lat)))
	E_lng = center_lng + city_radius / (111.320 * cos(radians(center_lat)))

	# Removes all records that aren't in a square around the city
	table_city = table[(table.latitude < N_lat) & (table.latitude > S_lat) & (table.longitude > W_lng) & (table.longitude < E_lng)]

	# Calculates distance from city center
	table_city.dist = pd.Series(0, index=table_city.index)
	table_city.dist = table_city.apply(haversine, args=(center_lng, center_lat), axis=1)

	# Keeps only data within 15km of city center
	table_city = table_city[table_city.dist < city_radius]

	# Number of obs
	numobs = len(table_city.index)

	# Prints the summary to the console
	print "\n" + city + "\n=============\n"

	if numobs > 3:
		model = smf.ols(formula='total_rent ~ living_space - 1', data=table_city)
		results = model.fit()
		print results.summary()
		m = results.params.living_space

		# Appends data to CSV
		csv += '"' + city + '",'
		csv += str(m) + ',' 
		csv += str(table_city['price_per_sqm'].mean()) + ','
		csv += str(results.bse.living_space) + ','
		csv += str(numobs) + ','
		csv += str(center_lat) + ','
		csv += str(center_lng)
		csv +='\n'
	else:
		csv += '"' + city + '", n/a,n/a,n/a,' + str(numobs) + ',' + str(center_lat) + ',' + str(center_lng) + '\n'

# Saves CSV
f = open("analyses/city_circles/table.csv", "w")
f.write(csv)
f.close()