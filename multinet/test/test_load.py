import pytest

from girder.plugin import loadedPlugins


@pytest.mark.plugin('multinet')
def test_import(server):
    assert 'multinet' in loadedPlugins()
