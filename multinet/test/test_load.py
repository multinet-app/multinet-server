import pytest


@pytest.mark.plugin('multinet')
def test_true(server):
    assert 'multinet' == 'multinet'
