#! /bin/bash

cat /etc/letsencrypt/live/multinet.app/fullchain.pem /etc/letsencrypt/live/multinet.app/privkey.pem > /etc/letsencrypt/live/multinet.app/server.pem
cp /etc/letsencrypt/live/multinet.app/server.pem /home/ubuntu/server.pem
chmod 644 /home/ubuntu/server.pem

systemctl restart arangodb3
