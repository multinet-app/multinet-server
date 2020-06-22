"""Pytest configurations for multinet tests."""

import pytest
from uuid import uuid4

from multinet import create_app
from multinet.db import create_workspace, delete_workspace


@pytest.fixture
def app():
    """Yield a testing app."""
    app = create_app({"TESTING": True})
    yield app


@pytest.fixture
def server(app):
    """Return a test client to `app`."""
    client = app.test_client()
    return client


@pytest.fixture
def generated_workspace():
    """Create a workspace, and yield the name of the workspace."""

    workspace_name = uuid4().hex

    create_workspace(workspace_name)
    return workspace_name


@pytest.fixture
def handled_workspace(generated_workspace):
    """
    Create a workspace, and yield the name of the workspace.

    On teardown, deletes the workspace.
    """
    yield generated_workspace

    delete_workspace(generated_workspace)
