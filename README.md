# multinet-girder
A Girder plugin proof-of-concept for a MultiNet API / web application

## Installation

### Set Up Girder
1. Clone this repository: `git clone
https://github.com/multinet-app/multinet-girder; cd multinet-girder`
2. Start the mongo and arango databases using docker-compose:
   `MULTINET_ROOT_PASSWORD=yourSecretPassword docker-compose up -d` NOTE: macOS
   users may encounter errors in this step regarding filemounts denied to the
   Docker process; to solve this issue, create two directories somewhere (e.g.
   `mkdir -p ~/.local/multinet/mongo`, `mkdir -p ~/.local/multinet/arango`), and
   launch the Docker container using `MULTINET_ROOT_PASSWORD=yourSecretPassword
   MONGO_DATA=~/.local/multinet/mongo ARANGO_DATA=~/.local/multinet/arango
   docker-compose up -d`.
3. Use pipenv to create a virtual environment and install the dependencies: `pipenv install`
4. Start the pipenv shell to set up girder and run the websever: `pipenv shell`
5. Build the Girder web client: `girder build`
6. Serve the Girder client: `MULTINET_ROOT_PASSWORD=yourSecretPassword girder serve --database
   mongodb://localhost:27017/multinet --port 9090`
7. Open the Girder client and register a user (which will become an admin user):
http://localhost:9090
8. Click on "Admin Console" in the left sidebar, then "Plugins", then activte
   the MultiNet plugin, then click the Restart button and wait for the page to
   reload.

### Run Sample Client
1. Move into the client code directory: `cd client`
2. Install dependencies: `yarn install`
3. Serve the application: `yarn serve`
4. Visit the sample client by opening the displayed URL (the Vue builder will
   choose an open port and show you).
