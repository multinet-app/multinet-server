# multinet-server/devops

The `arangodb.yml` Ansible playbook in this directory installs and configures
ArangoDB on an Ubuntu server. It does the following:
- installs ArangoDB
- sets a default password (TODO: make this password configurable)
- configures it to listen on all interfaces
- starts the service

To run it via ssh, run a command such as the following:

```
ansible-playbook -i <target-hostname>, arangodb.yml --ssh-extra-args="-i <identify.pem>"
```
