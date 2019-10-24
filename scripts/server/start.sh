#!/bin/sh

# Consult the lockfile first.
if [ -e server.pid ]; then
    echo "Server already running" >/dev/stderr
    exit 1
fi

# Launch the server in the background.
PIPENV_DONT_LOAD_ENV=1 FLASK_APP=multinet FLASK_ENV=development FLASK_SERVE_PORT=50000 ARANGO_PORT=58529 nohup pipenv run serve >server.out &
echo $! >server.pid

# Start the Arango database in the background with a clean data directory.
ARANGO_PORT=58529 ARANGO_DATA=$(readlink -f arango) docker-compose -p testing up -d

# Loop until the server is up.
started=0
count=0

echo -n "waiting for server to come up"
while [ ${started} = 0 ] && [ ${count} -lt 30 ]; do
    headers=$(curl -s -I http://localhost:50000/api/workspaces)
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
