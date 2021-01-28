#!/bin/sh
set -e

# Data taken from the VDL account

# Fetch raw CSV file.
curl -O https://raw.githubusercontent.com/visdesignlab/mvnv-study/master/data/raw/Eurovis2019Network.json

# Process the raw file into Multinet CSVs.
python process.py < Eurovis2019Network.json
