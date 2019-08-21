=======
Testing
=======

Tests
-----

Multinet uses `pytest <https://docs.pytest.org/en/latest/>`_ for testing.
To run these tests, run the following command: ::

    $ pipenv run test


Coverage
--------

To run coverage (also through pytest), run the following command: ::

    $ pipenv run coverage

Linting
-------

Multinet uses `flake8 <http://flake8.pycqa.org/en/latest/>`_ for linting.
To run this manually, type the following command: ::

    $ pipenv run lint

Formatting
----------

Multinet uses `black <https://black.readthedocs.io/en/stable/>`_ for code formatting.
To run this formatting, run the following command: ::

    $ pipenv run format
