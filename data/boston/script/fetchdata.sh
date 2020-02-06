#!/bin/sh
set -e

# Data taken from Kieran Healy's GitHub account, and originally from David
# Hackett Fischer's _Paul Revere's Ride_.

# Fetch raw CSV file.
curl -O https://raw.githubusercontent.com/kjhealy/revere/master/data/PaulRevereAppD.csv

# Process the raw file into Multinet CSVs.
python table2csv.py <PaulRevereAppD.csv
