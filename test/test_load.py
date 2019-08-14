"""This module tests the functions contained within multinet/db.py."""
import pytest


@pytest.mark.plugin("multinet")
def test_true(server):
    """Tests that reality is still what it seems."""
    assert "multinet" == "multinet"
