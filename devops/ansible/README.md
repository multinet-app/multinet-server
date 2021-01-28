# multinet-server/devops/ansible

There are 2 ansible playbook files in this directory that work together to
install and configure ArangoDB on an Ubuntu server. The first file, `ssl.yml`
does the following:

- installs certbot
- copies a script to the renewal-hooks directory + updates the location of the ssl files
- generates the certificate files
- runs the aforementioned script (**NOTE**: it doesn't run automatically on cert
  creation, only on renewals)
- sets the cronjob for renewing the script

The second file `arangodb.yml`does the following:
- triggers the first file (`ssl.yml`)
- installs ArangoDB
- sets a password on the root account
- configures ArangoDB to listen on all interfaces using SSL
- starts the service
- ensures that there is a readonly user

To set the root account password, you can either supply it on the command line
(see below) or just let Ansible prompt you for it.

To run the ansible playbook via ssh, run a command such as the following:

```
ansible-playbook \
    arangodb.yml \
    -i <target-hostname>,\
    --ssh-extra-args="-i <identity.pem>" \
    -e \
        arangodb_root_password=<password>
        arango_readonly_password=<a-different-password>
        server_name=<server-url>
        ssl_email=<email-address>
```
