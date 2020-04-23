"""Test that workspace operations act like we expect them to."""
import pytest

from uuid import uuid4
from multinet.db import (
    create_workspace,
    delete_workspace,
    rename_workspace,
    workspace_exists,
)


@pytest.fixture
def workspace():
    """
    Create a workspace, and yield the name of the workspace.

    On teardown, deletes the workspace.
    """

    workspace_name = uuid4().hex
    create_workspace(workspace_name)
    yield workspace_name
    delete_workspace(workspace_name)


def test_workspace_create(workspace):
    """Test that creating a workspace doesn't result in invalid caching."""
    assert workspace_exists(workspace)


def test_workspace_delete(workspace):
    """Tests that deleting a workspace doesn't result in invalid caching."""

    delete_workspace(workspace)
    exists = workspace_exists(workspace)

    # Restore workspace, so the fixture can clean up
    create_workspace(workspace)

    assert not exists


def test_workspace_rename(workspace):
    """Test that renaming a workspace doesn't result in invalid caching."""
    new_workspace_name = uuid4().hex
    rename_workspace(workspace, new_workspace_name)

    new_exists = workspace_exists(new_workspace_name)
    old_exists = workspace_exists(workspace)

    # Restore workspace, so the fixture can clean up
    rename_workspace(new_workspace_name, workspace)

    assert new_exists
    assert not old_exists
