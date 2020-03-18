# multinet-server

This is the server component for the Multinet project. It is a Flask application
that serves the Multinet REST API.

## Quick Start

To get the server up and running in dev mode:

1. Ensure that you have Python 3.7 and Pipenv installed on your system.
2. Check out this repository and move into it (e.g., `cd multinet-server`).
3. Copy the `.env.default` file to `.env`: `cp .env.default .env` (or if you
   prefer, create a symlink: `ln -s .env.default .env`).
4. Install the Pipenv dependencies: `pipenv install`.
5. Activate the virtual environment: `pipenv shell`.
6. Run the server application: `pipenv run serve`.
7. Visit http://localhost:5000 to ensure that the server is working.

For further details, including how to set up the ArangoDB server and the
Multinet client and visualization applications, please see the [full
documentation](https://multinet-app.readthedocs.io).
