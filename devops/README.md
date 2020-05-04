# multinet-server/devops

The `arangodb.yml` Ansible playbook in this directory installs and configures
ArangoDB on an Ubuntu server. It does the following:
- installs ArangoDB
- sets a password on the root account
- copies an SSL certificate to the server
- configures it to listen on all interfaces using SSL
- starts the service

To set the root account password, you can either supply it on the command line
(see below) or just let Ansible prompt you for it.

To use a wildcard SSL certificate for your domain you'll need to supply one (we use Let's Encrypt) and pass in the file path to the command.
If you're using a provider other than Let's Encrypt, you'll have to modify the playbook to work with your provider and file structure. 
If you're using Let's Encrypt, follow along with [this](https://medium.com/@saurabh6790/generate-wildcard-ssl-certificate-using-lets-encrypt-certbot-273e432794d7) 
guide to generate a wildcard certificate. This playbook assumes you have the certificate files, that they're in the default location, and that they are readable by the user running the ansible playbook.
If you don't want a ssl certificate, you'll have to modify the playbook and remove the `ssl_cert_path` env var from the command below.

To run the ansible playbook via ssh, run a command such as the following:

```
ansible-playbook arangodb.yml -i <target-hostname>, --ssh-extra-args="-i <identity.pem>" -e arangodb_root_password=<password> ssl_cert_path=<path-to-files>
```

# Vagrant

To test locally, you can use vagrant. Vagrant is a python package that is easily installed on most systems. If you need help installing it, please read the [docs](https://www.vagrantup.com/docs/installation/). Once you have Vagrant installed, you can run the vagrant file using:

```
vagrant up
```
