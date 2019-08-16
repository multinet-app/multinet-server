"""Tests the db.py file in the multinet directory."""
# import pytest

from multinet import db


# @pytest.fixture
# def db():
#     """Return db instance using multinet.db.db."""
#     return multinet_db('test_db')


def test_create_workspace():
    """Test that this workspace exists after function call."""
    name = "test_workspace_131312"
    sys = db.db("_system")
    print("sys", sys)

    assert not sys.has_database(name)
    db.create_workspace(name)
    assert sys.has_database(name)
