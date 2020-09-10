"""Pytest configurations for multinet tests."""

import pytest
from uuid import uuid4
from contextlib import contextmanager
from pathlib import Path
from flask.testing import FlaskClient

from multinet import create_app
from multinet.db.models.workspace import Workspace
from multinet.db.models.user import User
from multinet.auth.util import create_login_token, encode_auth_token

from typing import Generator, Tuple


@contextmanager
def login(user: User, server: FlaskClient) -> Generator[None, None, None]:
    """
    Perform server actions under a user login.

    This is done by monkey-patching the FlaskClient `open` method, to include the
    proper auth headers. The `open` method is the underlying method used by `get`,
    `post`, `put`, etc.
    """

    # To create a user login token, we need the app context,
    # since the encoding function uses flask_secret_key
    with server.application.app_context():
        login_token = create_login_token(user.multinet.session)
        encoded_login_token = encode_auth_token(login_token)

    default_open = server.open

    def logged_in_open(self, *args, **kwargs):
        return default_open(
            self,
            *args,
            **kwargs,
            headers={"Authorization": f"Bearer {encoded_login_token}"},
        )

    # Ignore flake8, since it complains about the monkey-patching
    server.open = logged_in_open  # noqa T484
    yield None
    server.open = default_open  # noqa T484


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
def managed_user():
    """
    Create a user, and yield that user.

    On teardown, deletes the user.
    """
    user = User.register(
        family_name="test",
        given_name="test",
        name="test test",
        picture="",
        email="test@test.test",
        sub=uuid4().hex,
    )

    yield user

    user.delete()


@pytest.fixture
def generated_workspace(managed_user) -> Workspace:
    """Create a workspace, and yield the name of the workspace."""
    workspace_name = uuid4().hex
    return Workspace.create(workspace_name, managed_user)


@pytest.fixture
def managed_workspace(generated_workspace: Workspace):
    """
    Create a workspace, and yield the name of the workspace.

    On teardown, deletes the workspace.
    """
    yield generated_workspace
    generated_workspace.delete()


@pytest.fixture
def populated_workspace(
    managed_workspace, data_directory, server, managed_user
) -> Tuple[Workspace, str, str, str]:
    """
    Populate a workspace with some data.

    Returns a Nested Tuple of the form:
    `(workspace_name: str, graph: str, node_table: str, edge_table: str)`

    """
    with open(Path(data_directory) / "miserables.json") as miserables:
        data = miserables.read()

    with login(managed_user, server):
        resp = server.post(
            f"/api/d3_json/{managed_workspace.name}/miserables", data=data
        )

    assert resp.status_code == 200

    return (managed_workspace, "miserables", "miserables_nodes", "miserables_links")
