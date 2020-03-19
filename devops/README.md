# multinet-server/devops

The `arangodb.yml` Ansible playbook in this directory installs and configures
ArangoDB on an Ubuntu server. It does the following:
- installs ArangoDB
- sets a default password (this will be configurable in the future; see
  https://github.com/multinet-app/multinet-server/issues/348)
- configures it to listen on all interfaces
- starts the service

To run it via ssh, run a command such as the following:

```
ansible-playbook -i <target-hostname>, arangodb.yml --ssh-extra-args="-i <identify.pem>"
```
