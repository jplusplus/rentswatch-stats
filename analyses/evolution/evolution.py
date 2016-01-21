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
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import time
from math import radians, cos, sin, asin, sqrt, ceil

# From http://stackoverflow.com/a/4913653
def haversine(x, lon2, lat2):
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

# Parse the file in a df
df = pd.read_csv('data/20160121/ad.csv', parse_dates=True)

# Removes values where price_per_sqm or lat is NULL

df = df[np.isfinite(df['price_per_sqm'])]
df = df[np.isfinite(df['latitude'])]
df = df[np.isfinite(df['longitude'])]

# Converts price, area and price_per_sqm to float

df[['total_rent']] = df[['total_rent']].astype(float)
df[['living_space']] = df[['living_space']].astype(float)
df[['price_per_sqm']] = df[['price_per_sqm']].astype(float)
df[['latitude']] = df[['latitude']].astype(float)
df[['longitude']] = df[['longitude']].astype(float)
df[['created_at']] = pd.to_datetime(df['created_at'])

# removes bogus ads

df = df[(df.price_per_sqm < 50) & (df.price_per_sqm > 1)]

# Prepares tables by city

cities = [
		  {
		  	"list": ["Berlin",
				  	 "U Rathaus Neukölln, Berlin",
				  	 "U Osloerstraße, Berlin",
				  	 "U Weinmeisterstraße, Berlin",
				  	 "Bersarin Platz, Berlin",
				  	 "Savignyplatz, Berlin"],
			"bounds": [8,18]
		  },
		  {
		  "list": ["Paris",
				   "Place de la République, Paris",
				   "Montparnasse, Paris",
				   "Place Gambetta, Paris",
				   "Place Saint-Michel, Paris",
				   "M Sablons, Neuilly"],
		  "bounds": [20,37]
		  }
		 ]
# Bounds of the time period

start_date = datetime(2015, 8, 1)
end_date = datetime.now()

for city in cities:

	city_counter = 0

	# Creates the figure
	figure = plt.figure(1, figsize=(6, 6))

	for hood in city["list"]:

		# Finds the coordinates of the city center
		url = 'http://nominatim.openstreetmap.org/search/?q=%s&format=json&limit=1' % urllib.quote_plus(hood)
		response = urllib2.urlopen(url)
		city_data = json.loads(response.read())
		center_lat = float(city_data[0]['lat'])
		center_lng = float(city_data[0]['lon'])

		# Size of the radius we need in km
		city_radius = 2 if ' ' in hood else 10

		# Approximate calculations from http://stackoverflow.com/a/1253545
		N_lat = center_lat + city_radius / 110.574
		S_lat = center_lat - city_radius / 110.574
		W_lng = center_lng - city_radius / (111.320 * cos(radians(center_lat)))
		E_lng = center_lng + city_radius / (111.320 * cos(radians(center_lat)))

		# Removes all records that aren't in a square around the city
		df_city = df[(df.latitude < N_lat) & (df.latitude > S_lat) & (df.longitude > W_lng) & (df.longitude < E_lng)]

		# Calculates distance from city center
		df_city.dist = pd.Series(0, index=df_city.index)
		df_city.dist = df_city.apply(haversine, args=(center_lng, center_lat), axis=1)

		# Keeps only data within 15km of city center
		df_city = df_city[df_city.dist < city_radius]

		dates_city = []
		rent_city = []
		rent_city_upper = []
		rent_city_lower = []

		for dt in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date):
			
			df_city_dates = df_city[(df_city.created_at > dt) & (df_city.created_at < dt + relativedelta(months=1))]
			numobs = len(df_city_dates.index)
			if numobs > 3:
					model = smf.ols(formula='total_rent ~ living_space - 1', data=df_city_dates)
					results = model.fit()
					m = results.params.living_space
					se = results.bse.living_space
					am = df_city_dates['price_per_sqm'].mean()
					rent_city.append(m)
					rent_city_upper.append(m+1.96*se)
					rent_city_lower.append(m-1.96*se)
			else: m = None
			dates_city.append(dt.strftime("%b %y"))
			print hood, dt, numobs, m

		# Adds subplot
		ax = plt.subplot(ceil(len(city["list"]) / 2),2,city_counter+1)
		x = np.arange(0, len(dates_city), 1)
		lines = plt.plot(rent_city)
		plt.xticks(x, dates_city,fontsize=8)
		plt.yticks(fontsize=8)
		plt.ylim(ymin=city["bounds"][0])
		plt.ylim(ymax=city["bounds"][1])
		ax.fill_between(x, rent_city_upper, rent_city_lower, color='grey', alpha='0.1')
		ax.set_title(hood.decode("utf-8") + " (n=" +  str(len(df_city.index)) + ")",fontsize=10)

		city_counter+=1

	# Makes layout more legible
	figure.tight_layout()
	# Saves image
	pylab.savefig('analyses/evolution/graph-%s.png' % city["list"][0],dpi=80)
	plt.close(figure)