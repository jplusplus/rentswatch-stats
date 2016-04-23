import csv as csv
import re

def convert_in_meters(string, separator):
	if (separator in string):
		feet = string.split(separator)[0]
		inches = string.split(separator)[1]
		
		inches = inches.replace(" ", "")
		if inches != "" and inches is not None:
			inches = float(inches) * 0.025
		else:
			inches = 0
		return float(feet) * 0.305 + inches

	else:
		feet = string
		return float(feet)

def convert_in_sqm(string):
	return float(string) * 0.092903
	

patterns = [
	{
		# Looks for rooms in feet under the format 5'10" x 3'1"
		"format_finder_expression": "\d{1,2}'[ ]*\d{1,2}\" x \d{1,2}'[ ]*\d{1,2}\"",
		"expression": "(\d{1,2}'[ ]*\d{0,2})(?:\")*(?: max)* x (\d{1,2}'[ ]*\d{0,2})(?:\")*",
		"expect" : "several" # several rooms to add up
	},
	{
		# Looks for rooms in feet under the format 10'2 x 9'3
		"format_finder_expression": "\d{1,2}'\d{1,2} x \d{1,2}'\d{1,2}(?!\")",
		"expression": "(\d{1,2}'\d{0,2})(?: max)* x (\d{1,2}'\d{0,2})",
		"expect" : "several"
	},
	{
		# Looks for "646 sq. Ft."
		"format_finder_expression": "sq\. ft\.",
		"expression": "(\d{3,4})[ ]*sq\. ft\.",
		"expect": "one"
	}
]

readdata = csv.reader(open("data/20160423/desc.csv"))

data = []

total = bogus = ok = 0

for row in readdata:
	desc = row[35]
	no_rooms = row[25]
	rent = row[7]
	line_id = row[0]
	total += 1

	# Removes conversions in meters of the format " (3.81m)"
	expression_to_remove = "( \(\d{1,2}.\d{1,2}m\))"
	q = re.compile(expression_to_remove)
	for match in q.finditer(desc):
		desc = desc.replace(match.group(1), "")

	# lower cases
	desc = desc.lower()

	for pattern in patterns:
		format_finder_expression = pattern["format_finder_expression"]
	
		if (re.search(format_finder_expression, desc) is not None):

			expression = pattern["expression"]
			p = re.compile(expression)

			living_space = 0
			
			if pattern["expect"] == "one":
				match = re.search(expression, desc)
				living_space = convert_in_sqm(match.group(1))

			elif pattern["expect"] == "several":
				for match in p.finditer(desc):
					living_space += convert_in_meters(match.group(1), "'") *  convert_in_meters(match.group(2), "'")

			if (no_rooms != "NULL" and no_rooms != "None"):
				if living_space/float(no_rooms) < 10 or living_space/float(no_rooms) > 40:
					# print line_id, living_space, no_rooms, living_space/float(no_rooms)
					bogus += 1
				else:
					ok += 1
			break # No need to try other patterns
	

print total, bogus, ok