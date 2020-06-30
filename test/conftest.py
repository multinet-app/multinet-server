"""Pytest configurations for multinet tests."""

import pytest
import dacite
from uuid import uuid4
from dataclasses import asdict, dataclass
from contextlib import contextmanager

from multinet import create_app
from multinet.db import create_workspace, delete_workspace
from multinet.user import (
    register_user,
    set_user_cookie,
    user_collection,
    UserInfo,
    User,
    MULTINET_COOKIE,
)

from typing import Generator


@dataclass
class ContextUser(User):
    """Inherits User to provide testing login context."""

    @contextmanager
    def login(self, server) -> Generator[None, None, None]:
        """Ensure the user is logged in during this context."""
        with server.session_transaction() as session:
            session[MULTINET_COOKIE] = self.multinet.session

        yield None

        with server.session_transaction() as session:
            del session[MULTINET_COOKIE]


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
def managed_user():
    """
    Create a user, and yield that user.

    On teardown, deletes the user.
    """
    user = set_user_cookie(
        register_user(
            UserInfo(
                family_name="test",
                given_name="test",
                name="test test",
                picture="",
                email="test@test.test",
                sub=uuid4().hex,
            )
        )
    )

    yield dacite.from_dict(data_class=ContextUser, data=asdict(user))

    # TODO: Once the function exists, use `delete_user` here instead
    user_collection().delete(asdict(user))


@pytest.fixture
def generated_workspace(managed_user):
    """Create a workspace, and yield the name of the workspace."""

    workspace_name = uuid4().hex

    create_workspace(workspace_name, managed_user)
    return workspace_name


@pytest.fixture
def managed_workspace(generated_workspace):
    """
    Create a workspace, and yield the name of the workspace.

    On teardown, deletes the workspace.
    """
    yield generated_workspace

    delete_workspace(generated_workspace)
