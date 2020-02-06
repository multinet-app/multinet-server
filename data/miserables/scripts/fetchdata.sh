#!/bin/sh
set -e

# Les Miserable dataset, taken from d3-plugins GitHub repository.

# Retrieve the raw JSON data.
curl -O https://raw.githubusercontent.com/d3/d3-plugins/master/graph/data/miserables.json

# Process it into Multinet CSV files.
python process.py <miserables.json
