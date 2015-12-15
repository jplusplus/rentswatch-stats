#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import csv as csv
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import matplotlib.image as image
import pylab
from PIL import Image
import urllib2
import urllib
import json
from math import radians, cos, sin, asin, sqrt, ceil

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

cities = [
	{
		"name": "Berlin",
		"OSM_str" : "U %s, %s",
		"font": "TransitFront",
		"lines": [
			{
				"name": "U2",
				"color": "#ff3300",
				"stations": [
					{"name": "Theodor-Heuss-Platz"},
					{"name": "Kaiserdamm"},
					{"name": "Sophie-Charlotte-Platz"},
					{"name": "Bismarckstraße"},
					{"name": "Deutsche Oper"},
					{"name": "Ernst-Reuter-Platz"},
					{"name": "Zoologischer Garten"},
					{"name": "Wittenbergplatz"},
					{"name": "Nollendorfplatz"},
					{"name": "Bülowstraße"},
					{"name": "Gleisdreieck"},
					{"name": "Mendelssohn-Bartholdy-Park"},
					{"name": "Potsdamer Platz"},
					{"name": "Mohrenstraße"},
					{"name": "Stadtmitte"},
					{"name": "Hausvogteiplatz"},
					{"name": "Spittelmarkt"},
					{"name": "Märkisches Museum"},
					{"name": "Klosterstraße"},
					{"name": "Alexanderplatz"},
					{"name": "Rosa-Luxemburg-Platz"},
					{"name": "Senefelderplatz"},
					{"name": "Eberswalder Straße"},
					{"name": "Schönhauser Allee"},
					{"name": "Vinetastraße"},
					{"name": "Pankow"}
				]
			},{
				"name": "U8",
				"color": "#0a3c85",
				"stations": [
					{"name": "Wittenau"},
					{"name": "Rathaus Reinickendorf"},
					{"name": "Karl-Bonhoeffer-Nervenklinik"},
					{"name": "Lindauer Allee"},
					{"name": "Paracelsus-Bad"},
					{"name": "Residenzstraße"},
					{"name": "Franz-Neumann-Platz"},
					{"name": "Osloer Straße"},
					{"name": "Pankstraße"},
					{"name": "Gesundbrunnen"},
					{"name": "Voltastraße"},
					{"name": "Bernauer Straße"},
					{"name": "Rosenthaler Platz"},
					{"name": "Weinmeisterstraße"},
					{"name": "Alexanderplatz"},
					{"name": "Jannowitzbrücke"},
					{"name": "Heinrich-Heine-Straße"},
					{"name": "Moritzplatz"},
					{"name": "Kottbusser Tor"},
					{"name": "Schönleinstraße"},
					{"name": "Hermannplatz"},
					{"name": "Boddinstraße"},
					{"name": "Leinestraße"},
					{"name": "Hermannstraße"}
				]
			}
			,{
				"name": "U5",
				"color": "#672f17",
				"stations": [
					{"name": "Alexanderplatz"},
					{"name": "Schillingstraße"},
					{"name": "Strausberger Platz"},
					{"name": "Weberwiese"},
					{"name": "Frankfurter Tor"},
					{"name": "Samariterstraße"},
					{"name": "Frankfurter Allee"},
					{"name": "Magdalenenstraße"},
					{"name": "Lichtenberg"},
					{"name": "Friedrichsfelde"},
					{"name": "Tierpark"},
					{"name": "Biesdorf-Süd"},
					{"name": "Elsterwerdaer Platz"},
					{"name": "Wuhletal"},
					{"name": "Kaulsdorf-Nord"},
					{"name": "Neue Grottkauer Straße"},
					{"name": "Cottbusser Platz"},
					{"name": "Hellersdorf"},
					{"name": "Louis-Lewin-Straße"},
					{"name": "Hönow"}
				]
			},
			{
				"name": "U1",
				"color": "#55a822",
				"stations": [
					{"name": "Uhlandstraße"},
					{"name": "Kurfürstendamm"},
					{"name": "Wittenbergplatz"},
					{"name": "Nollendorfplatz"},
					{"name": "Kurfürstenstraße"},
					{"name": "Gleisdreieck"},
					{"name": "Möckernbrücke"},
					{"name": "Hallesches Tor"},
					{"name": "Prinzenstraße"},
					{"name": "Kottbusser Tor"},
					{"name": "Görlitzer Bahnhof"},
					{"name": "Schlesisches Tor"},
					{"name": "Warschauer Straße"}
				]
			}
		]
	}
]

# Save header
Header = data[0]

# Remove header from data
data.pop(0)

# Organize the data in a table
table = pd.DataFrame(data, columns=Header)

# Removes values where price_per_sqm is NULL

table = table[table.price_per_sqm != "NULL"]

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

# Remove bogus values
table = table[table.price_per_sqm > 3]
table = table[table.price_per_sqm < 70]

# Prepares the CSV with the data

csv = "city,line,station,price_per_sqm_reg,sdt_error,numobs\n"

for city in cities:

	for line in city["lines"]:

		# Creates the figure
		hfont = {'fontname':city["font"].encode("ascii")}
		figure = plt.figure(1, figsize=(14, 6))
		ax = figure.add_subplot(111)
		floor_y = 999

		# X axis increment
		horiz_distance = 0

		for station in line["stations"]:

			# Finds the coordinates of the station
			station_str = city["OSM_str"] % (station["name"], city["name"])
			print "Geocoding %s..." % station_str
			url = 'http://nominatim.openstreetmap.org/search/?q=%s&format=json&limit=1' % urllib.quote_plus(station_str)
			response = urllib2.urlopen(url)
			city_data = json.loads(response.read())
			station_lat = float(city_data[0]['lat'])
			station_lng = float(city_data[0]['lon'])

			# We'll take all ads within 400m of the station
			station_radius = .5

			# Approximate calculations from http://stackoverflow.com/a/1253545
			N_lat = station_lat + station_radius / 110.574
			S_lat = station_lat - station_radius / 110.574
			W_lng = station_lng - station_radius / (111.320 * cos(radians(station_lat)))
			E_lng = station_lng + station_radius / (111.320 * cos(radians(station_lat)))

			# Removes all records that aren't in a square around the city
			table_station = table[(table.latitude < N_lat) & (table.latitude > S_lat) & (table.longitude > W_lng) & (table.longitude < E_lng)]

			# Calculates distance from station
			table_station.dist = pd.Series(0, index=table_station.index)
			table_station.dist = table_station.apply(haversine, args=(station_lng, station_lat), axis=1)

			# Keeps data near station
			table_station = table_station[table_station.dist <= station_radius]

			# Number of obs
			numobs = len(table_station.index)

			# Increments X axis
			horiz_distance += 30
			station["horiz_distance"] = horiz_distance

			if numobs > 3:
				model = smf.ols(formula='total_rent ~ living_space - 1', data=table_station)
				results = model.fit()
				m = results.params.living_space
				se = results.bse.living_space
				am = table_station['price_per_sqm'].mean()
				station["m"] = m
				# Living space for €700
				station["price"] = (1/m) * 700
				# Makes sure the labels are shown under the graph
				if station["price"] < floor_y:
					floor_y = station["price"]
			else:
				m = "n/a"
				se = "n/a"
				am = "n/a"
				station["m"] = m
				station["price"] = "no data"

			csv += '"' + city["name"] + '",'
			csv += '"' + line["name"] + '",'
			csv += '"' + station["name"] + '",'
			csv += str(m) + ","
			csv += str(se) + ","
			csv += str(numobs) + "\n"

		# Rearranges the data to fit a df
		line["x"] = []
		line["y"] = []
		line["floor_y"] = []
		last_price = 0
		for station in line["stations"]:
			line["x"].append(station["horiz_distance"])
			line["floor_y"].append(floor_y - 3)
			if station["price"] != "no data":
				line["y"].append(station["price"])
				last_price = station["price"]
			# If no data for station, take price of last station
			else:
				line["y"].append(last_price)
				station["price"] = last_price

		# Adds gridlines
		ax.axes.get_xaxis().set_visible(False)
		major_ticks = np.arange(int(ceil(floor_y / 10.0)) * 10, 101, 10) 
		ax.set_yticks(major_ticks)
		plt.yticks(color="#999999", **hfont)
		ax.tick_params(axis='y', colors='#dddddd')
		plt.grid(axis='y', b=True, which='major', color='#dddddd',linestyle='-')

		# Makes the graph
		lines = plt.plot(line["x"], line["y"], zorder=10)
		plt.setp(
			lines, 
			color=line["color"], 
			linewidth=5, 
			marker="s", 
			mfc= line["color"],
			ms=8,
			mew=0)

		for station in line["stations"]:
			station_name_details = station["name"].decode("utf-8") + ": "
			if station["m"] != "n/a":
				station_name_details += str(round(station["price"],0))[:-2] + " sqm".decode("utf-8")
			else:
				station_name_details += "no data"
			ax.annotate(
				station_name_details, 
				xy= (station["horiz_distance"], station["price"]),
				xytext=(station["horiz_distance"] - 5, floor_y - 6),
				rotation=-35,
				alpha=1,
				fontsize=12,ha="left", va="top",
				**hfont
			)

		# Makes sure the chart is big enough for the labels
		plt.ylim(ymin=floor_y - 30)
		plt.xlim(xmax=horiz_distance + 60)

		# Adds a line above the stations' names
		base_line = plt.plot(line["x"], line["floor_y"])
		plt.setp(
			base_line, 
			color="#dddddd", 
			linewidth=4, 
			marker="o", 
			mfc= "#333333",
			ms=4,
			mew=0)

		# Removes everything but the ticks
		ax.spines['right'].set_color('none')
		ax.spines['top'].set_color('none')
		ax.spines['bottom'].set_color('none')
		ax.spines['left'].set_color('none')

		# Adds title
		plt.title("How many square meters a 700-euro rent gets you along the ".decode("utf-8") + line["name"].capitalize() + "\n", **hfont)

		# Saves image
		pylab.savefig('analyses/u_bahn_linien/graph-'+ city["name"] + line["name"] +'.png', bbox_inches='tight',dpi=80)
		plt.close(figure)

# Saves CSV
f = open("analyses/u_bahn_linien/table.csv", "w")
f.write(csv)
f.close()
