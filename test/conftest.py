"""Pytest configurations for multinet tests."""

import pytest
from uuid import uuid4
from pathlib import Path

from multinet import create_app
from multinet.db import create_workspace, delete_workspace

from typing import Tuple, List


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
def data_directory() -> Path:
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"


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


@pytest.fixture
def populated_workspace(
    handled_workspace, data_directory, server
) -> Tuple[str, Tuple[List[str], List[str]]]:
    """
    Populate a workspace with some data.

    Returns a Nested Tuple of the form:
    `(workspace_name: str, (graphs: List[str], tables: List[str]))`

    """
    with open(Path(data_directory) / "miserables.json") as miserables:
        data = miserables.read()

    resp = server.post(f"/api/d3_json/{handled_workspace}/miserables", data=data)
    assert resp.status_code == 200

    return (
        handled_workspace,
        (["miserables"], ["miserables_nodes", "miserables_links"]),
    )
