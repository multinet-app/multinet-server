# multinet-server/devops

The `arangodb.yml` Ansible playbook in this directory installs and configures
ArangoDB on an Ubuntu server. It does the following:
- installs ArangoDB
- sets a password on the root account
- configures it to listen on all interfaces
- starts the service

To set the root account password, you can either supply it on the command line
(see below) or just let Ansible prompt you for it.

To run it via ssh, run a command such as the following:

```
ansible-playbook arangodb.yml -i <target-hostname>, --ssh-extra-args="-i <identity.pem>" -e arangodb_root_password=<password>
```
