.. _multinet-girder:

===============
multinet-girder
===============
A Girder plugin proof-of-concept for a MultiNet API / web application

.. highlight:: sh

Installation
============

Set Up Multinet/Girder
----------------------

1. Clone this repository: ::

       $ git clone https://github.com/multinet-app/multinet-girder
       $ cd multinet-girder

2. Start the mongo and arango databases using docker-compose: ::

       $ docker-compose up

   NOTE: macOS users may encounter errors in this step regarding
   filemounts denied to the Docker process; to solve this issue, create two
   directories somewhere, e.g.::

       $ mkdir -p ~/.local/multinet/mongo
       $ mkdir -p ~/.local/multinet/arango

   and then launch the Docker container using::

       $ MONGO_DATA=~/.local/multinet/mongo ARANGO_DATA=~/.local/multinet/arango
       docker-compose up -d

3. Use pipenv to create a virtual environment and install the dependencies: ::

       $ pipenv install

4. Build the Girder web client: ::

       $ pipenv run girder-build

5. Start the Multinet server: ::

       $ yarn start:server

6. Open the Multinet Girder application and register a user (which will become
   an admin user) at http://localhost:9090.

A Note on Passwords
~~~~~~~~~~~~~~~~~~~

When the Arango database is launched for the first time in Step 2 above, if the
Arango data directory does not exist it will be created and populated with
required startup data, including a password. The default password is
``letmein``, but it can be set to something different through the
``ARANGO_PASSWORD`` environment variable.

When the Multinet server is started in Step 5, it will operate using the default
password to communicate with Arango. Therefore, if you launched Arango using a
custom password, you should launch the server with that same password, also via
an ``ARANGO_PASSWORD`` environment variable.

To illustrate, if the Step 2 invocation looks like::

    $ ARANGO_PASSWORD=hunter2 docker-compose up

then the corresponding command to launch the server in Step 5 will look like::

    $ ARANGO_PASSWORD=hunter2 yarn start:server

Run Sample Client
-----------------

1. Move into the client code directory: ::

   $ cd client

2. Install dependencies: ::

   $ yarn install

3. Serve the application: ::

   $ yarn serve

4. Visit the sample client by opening the displayed URL (the Vue builder will
   choose an open port and show you).
