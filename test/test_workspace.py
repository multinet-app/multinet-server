"""Test that workspace operations act like we expect them to."""
from uuid import uuid4
from multinet.db import (
    create_workspace,
    delete_workspace,
    rename_workspace,
    workspace_exists,
)


def test_workspace_create_and_delete():
    """Tests that creating a workspace doesn't result in invalid caching."""
    workspace_name = uuid4().hex

    create_workspace(workspace_name)
    exists_after_create = workspace_exists(workspace_name)

    # Teardown
    delete_workspace(workspace_name)
    exists_after_delete = workspace_exists(workspace_name)

    assert exists_after_create
    assert not exists_after_delete


def test_workspace_rename():
    """Test that renaming a workspace doesn't result in invalid caching."""
    workspace_name_a = uuid4().hex
    workspace_name_b = uuid4().hex
    create_workspace(workspace_name_a)
    rename_workspace(workspace_name_a, workspace_name_b)

    new_exists = workspace_exists(workspace_name_b)
    old_exists = workspace_exists(workspace_name_a)

    # Teardown
    delete_workspace(workspace_name_b)

    assert new_exists
    assert not old_exists
