multinet-girder
=================
A Girder plugin proof-of-concept for a MultiNet API / web application

Installation
=================

Set Up Multinet/Girder
^^^^^^^^^^^^^^^^^^^^^^
1. Clone this repository: ``git clone
   https://github.com/multinet-app/multinet-girder; cd multinet-girder``.
2. Start the mongo and arango databases using docker-compose:
   ``MULTINET_ROOT_PASSWORD=yourSecretPassword docker-compose up -d``.  NOTE:
   macOS users may encounter errors in this step regarding filemounts denied to
   the Docker process; to solve this issue, create two directories somewhere
   (e.g. ``mkdir -p ~/.local/multinet/mongo``, ``mkdir -p
   ~/.local/multinet/arango``), launch the Docker container using
   ``MULTINET_APP_PASSWORD=yourSecretPassword MONGO_DATA=~/.local/multinet/mongo
   ARANGO_DATA=~/.local/multinet/arango docker-compose up -d``.
3. Use pipenv to create a virtual environment and install the dependencies:
   ``pipenv install``.
4. Build the Girder web client: ``pipenv run girder build``.
5. Start the Multinet server: ``MULTINET_APP_PASSWORD=yourSecretPassword yarn
   start:server``.
6. Open the Multinet Girder application and register a user (which will become
   an admin user): http://localhost:9090.

Run Sample Client
^^^^^^^^^^^^^^^^^
1. Move into the client code directory: ``cd client``.
2. Install dependencies: ``yarn install``.
3. Serve the application: ``yarn serve``.
4. Visit the sample client by opening the displayed URL (the Vue builder will
   choose an open port and show you).
