============
Installation
============

Set Up Multinet
---------------

1. Clone this repository: ::

       $ git clone https://github.com/multinet-app/multinet
       $ cd multinet

2. Start the Arango database using docker-compose: ::

       $ docker-compose up

   NOTE: macOS users may encounter errors in this step regarding filemounts
   denied to the Docker process; to solve this issue, create a data directory
   somewhere, e.g.::

       $ mkdir -p ~/.local/multinet/arango

   and then launch the Docker container using::

       $ ARANGO_DATA=~/.local/multinet/arango docker-compose up

3. Inspect the ``.env`` file, which contains a few useful environment variable
   declarations. The most important one at the moment is ``FLASK_SERVE_PORT``,
   which controls which local port the server will listen on for incoming
   connections. This same variable also controls how the client application
   proxies API requests so they are routed correctly to the server.

   If the port listed in this file is not free on your system, edit the value to
   an alternative port number.

4. Use pipenv to create a virtual environment and install the dependencies: ::

       $ pipenv install

5. Install the pre-commit hook: ::

       $ pipenv run pre-commit install

   This hook will run the Black formatter in check mode, as well as linting
   tests, and abort the commit if there are style errors in the code. You can
   fix these manually, or run ``black`` via ``pipenv run format`` to fix them
   automatically.

6. Start the Multinet server: ::

       $ pipenv run serve

A Note on Passwords
~~~~~~~~~~~~~~~~~~~

When the Arango database is launched for the first time in Step 2 above, if the
Arango data directory does not exist it will be created and populated with
required startup data, including a password. The default password is
``letmein``, but it can be set to something different through the
``ARANGO_PASSWORD`` environment variable.

When the Multinet server is started in Step 7, it will operate using the default
password to communicate with Arango. Therefore, if you launched Arango using a
custom password, you should launch the server with that same password, also via
an ``ARANGO_PASSWORD`` environment variable.

To illustrate, if the Step 2 invocation looks like::

    $ ARANGO_PASSWORD=hunter2 docker-compose up

then the corresponding command to launch the server in Step 5 will look like::

    $ ARANGO_PASSWORD=hunter2 yarn start:server

Run Sample Client
-----------------

1. From the top-level directory, move into the client code directory: ::

   $ cd client

2. Install dependencies: ::

   $ yarn install

3. Build and serve the application: ::

   $ yarn serve

4. Visit the sample client by opening the displayed URL (the Vue builder will
   choose an open port and show you).
