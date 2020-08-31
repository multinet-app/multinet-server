"""Test that workspace operations act like we expect them to."""
from uuid import uuid4
from multinet.db import workspace_mapping
from multinet.db.models.workspace import Workspace


def test_present_workspace(managed_workspace):
    """Test that workspace caching works as expected on present workspaces."""

    # Assert that the cached response matches the actual response
    assert workspace_mapping.__wrapped__(managed_workspace.name) == workspace_mapping(
        managed_workspace.name
    )
    workspace_mapping.cache_clear()

    first_resp = workspace_mapping(managed_workspace.name)
    second_resp = workspace_mapping(managed_workspace.name)

    # Assert that cached response is idempotent
    assert first_resp == second_resp


def test_absent_workspace():
    """Test that workspace caching works as expected on absent workspaces."""

    # Test that random workspace doesn't exist
    assert workspace_mapping.__wrapped__(uuid4().hex) is None
    workspace_mapping.cache_clear()

    workspace_name = uuid4().hex
    first_resp = workspace_mapping(workspace_name)
    second_resp = workspace_mapping(workspace_name)

    # Test that fake workspace doesn't exist,
    # and that calls are idempotent
    assert first_resp is None
    assert second_resp is None


def test_workspace_create(managed_user):
    """Test that creating a workspace doesn't result in invalid caching."""
    workspace_name = uuid4().hex

    pre_create = workspace_mapping(workspace_name)
    workspace = Workspace.create(workspace_name, managed_user)

    post_create = workspace_mapping(workspace_name)
    post_create_exists = Workspace.exists(workspace_name)

    # Teardown
    workspace.delete()

    # Asserts
    assert pre_create is None
    assert post_create is not None
    assert post_create_exists


def test_workspace_delete(generated_workspace):
    """Tests that deleting a workspace doesn't result in invalid caching."""

    pre_delete = workspace_mapping(generated_workspace.name)
    generated_workspace.delete()

    post_delete = workspace_mapping(generated_workspace.name)
    exists_post_delete = Workspace.exists(generated_workspace.name)

    # Asserts
    assert pre_delete is not None
    assert post_delete is None
    assert not exists_post_delete


def test_workspace_rename(generated_workspace):
    """Test that renaming a workspace doesn't result in invalid caching."""
    new_workspace_name = uuid4().hex
    old_workspace_name = generated_workspace.name
    pre_rename = workspace_mapping(old_workspace_name)

    generated_workspace.rename(new_workspace_name)

    post_rename_old = workspace_mapping(old_workspace_name)
    post_rename_new = workspace_mapping(new_workspace_name)

    new_exists = Workspace.exists(new_workspace_name)
    old_exists = Workspace.exists(old_workspace_name)

    # Teardown
    generated_workspace.delete()

    # Asserts
    assert pre_rename is not None
    assert post_rename_old is None
    assert post_rename_new is not None

    assert new_exists
    assert not old_exists
