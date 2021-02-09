#! /bin/bash

# This file is here (and not as ansible steps), because it must run on each cert renew,
# not just every ansible provisioning.

cat /etc/letsencrypt/live/SERVER_NAME/fullchain.pem /etc/letsencrypt/live/SERVER_NAME/privkey.pem > /home/ubuntu/server.pem
chmod 644 /home/ubuntu/server.pem

systemctl restart arangodb3
