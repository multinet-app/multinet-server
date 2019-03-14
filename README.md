# multinet-girder
A Girder plugin proof-of-concept for a MultNet API / web application

## Installation

### Set Up Girder
1. Clone this repository: `git clone
https://github.com/multinet-app/multinet-girder; cd multinet-girder`
2. Create and activate a Python virtual environment: `virtualenv venv; source
./venv/bin/activate`
3. Perform an editable install of the plugin package: `pip install -e multinet`
4. Build the Girder web client: `girder build`
5. Serve the Girder client: `girder serve --database
   mongodb://localhost:27017/multinet --port 9090`
6. Open the Girder client and register a user (which will become an admin user):
http://localhost:9090
7. Click on "Admin Console" in the left sidebar, then "Plugins", then activte
   the MultiNet plugin, then click the Restart button and wait for the page to
   reload.

### Run Sample Client
1. Move into the client code directory: `cd client`
2. Install dependencies: `yarn install`
3. Serve the application: `yarn serve`
4. Visit the sample client by opening the displayed URL (the Vue builder will
   choose an open port and show you).
