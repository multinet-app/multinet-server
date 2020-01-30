#!/bin/bash

# Consult the lockfile first.
if [ -e server.pid ]; then
    echo "Client already running" >/dev/stderr
    exit 1
fi

# Gets the absolute filepath
realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

# Get the env vars
FILE_PATH=$(dirname $(realpath "$0"))
source $FILE_PATH/../../.env.test

nohup yarn serve --port ${CLIENT_SERVE_PORT} >server.out &
echo $! >server.pid

# Loop until the client is up.
started=0
count=0

echo -n "waiting for client to come up"
while [ ${started} = 0 ] && [ ${count} -lt 60 ]; do
    headers=$(curl -s -I --max-time 0.5 http://localhost:${CLIENT_SERVE_PORT}/api/workspaces)
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