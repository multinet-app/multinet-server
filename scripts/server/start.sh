#!/bin/bash

# Consult the lockfile first.
if [ -e server.pid ]; then
    echo "Server already running" >/dev/stderr
    exit 1
fi

# Gets the absolute filepath
realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

# Get the env vars
FILE_PATH=$(dirname $(realpath "$0"))
source $FILE_PATH/../../.env.test

# Launch the server in the background.
nohup pipenv run serve >server.out &
echo $! >server.pid

# Start the Arango database in the background with a clean data directory.
docker-compose -p testing up -d

# Loop until the server is up.
started=0
count=0

echo -n "waiting for server to come up"
while [ ${started} = 0 ] && [ ${count} -lt 30 ]; do
    headers=$(curl -s -I http://localhost:$FLASK_SERVE_PORT/api/workspaces)
    curl_status=$?

    if [ ${curl_status} = 0 ]; then
        result=$(echo ${headers} | head -1 | grep 200)
        good=$?
        if [ ${good} = 0 ]; then
            started=1
        fi
    fi

    sleep 1
    count=$(expr ${count} + 1)
    echo -n .
done

if [ ${started} = 1 ]; then
    true
else
    false
fi
