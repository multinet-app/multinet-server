#!/bin/sh
set -e

# Data and headers taken from https://openflights.org/data.html

# Fetch airport data file.
curl -O https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat

# Fetch route data file.
curl -O https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat

# Stitch headers onto the two files.
echo "_key,name,city,country,IATA,ICAO,latitude,longitude,altitude,timezone,DST,tz database time,type,source" | cat - airports.dat >airports.csv
echo "airline,airline ID,source airport,_from,destination airport,_to,codeshare,stops,equipment" | cat - routes.dat >routes_incomplete.csv

# Repair the airport ID field in the routes file.
python process.py airports.csv <routes_incomplete.csv >routes.csv
