#!/bin/sh

# Consult the lockfile first.
if [ -e server.pid ]; then
    echo "Server already running" >/dev/stderr
    exit 1
fi

# Launch the server in the background.
nohup pipenv run serve &
echo $! >server.pid

# Start the Arango database in the background with a clean data directory.
ARANGO_DATA=$(readlink -f arango) ARANGO_USER=$(id -u) ARANGO_GROUP=$(id -g) docker-compose up -d
