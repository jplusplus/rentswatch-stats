#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import csv as csv
import pandas as pd
import scipy.stats as sc
import matplotlib.pyplot as plt
import pylab
from PIL import Image

readdata = csv.reader(open("../data/20151113/ads.csv"))

im = Image.open('../images/logo.png')
height = im.size[1]

im = np.array(im).astype(np.float) / 255

data = []

for row in readdata:
  data.append(row)

# Save header
Header = data[0]

# Remove header from data
data.pop(0)

# Organize the data in a table
table = pd.DataFrame(data, columns=Header)

# Removes values where price_per_sqm is NULL

table = table[table.price_per_sqm != "NULL"]

# Converts price, area and price_per_sqm to float

table[['total_rent']] = table[['total_rent']].astype(float)
table[['living_space']] = table[['living_space']].astype(float)
table[['price_per_sqm']] = table[['price_per_sqm']].astype(float)

# Converts string vars

table[['country']] = table[['country']].astype('S32')

# Makes city lowercase

table[['city']] = table['city'].str.lower()

# Prepares tables by city

cities = ["berlin", "paris", "praha", "roma"]

# Draws the figure

figure = plt.figure(1, figsize=(8, 12), dpi=80)

city_counter = 0

for city in cities:

	city_counter += 1

	# Filters by city, using regex so as to match 'Berlin-Kreuzberg' or 'Paris 2eme'
	table_city = table[table.city.str.contains('^'+city)]

	# Adds subplot
	ax = plt.subplot(len(cities),1,city_counter)

	plt.ylabel('Living space in sqm')
	plt.xlabel('Price per month in EUR')
	
	plt.ylim([0,200])
	plt.xlim([0,2000])
	ax.plot(table_city['total_rent'], table_city['living_space'], 'bo', alpha=.2, ms=1)

	regressionline = sc.stats.linregress(table_city['total_rent'], table_city['living_space'])

	m = regressionline[0]
	b = regressionline[1]
	x = np.linspace(0, 3000, 100)

	price_per_sqm = round(1/m, 1)

	ax.set_title(city.capitalize() + ": " + str(price_per_sqm) + "EUR/sqm (n=" +  str(len(table_city.index)) + ")")

	ax.plot(x, m*x + b)

# Makes layout more legible
figure.tight_layout()

# Adds watermark
img = figure.figimage(im, 0, figure.bbox.ymax - height, alpha=.05)
img.set_zorder(20)

# Saves image
pylab.savefig('price_vs_area.png')