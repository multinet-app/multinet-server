#! /bin/bash

cat /etc/letsencrypt/live/SERVER_NAME/fullchain.pem /etc/letsencrypt/live/SERVER_NAME/privkey.pem > /home/ubuntu/server.pem
chmod 644 /home/ubuntu/server.pem

systemctl restart arangodb3
