"""Test that workspace operations act like we expect them to."""
import pytest

from uuid import uuid4
from multinet.db import (
    create_workspace,
    delete_workspace,
    rename_workspace,
    workspace_exists,
    workspace_mapping,
)


@pytest.mark.skip()
def test_present_workspace(handled_workspace):
    """Test that workspace caching works as expected on present workspaces."""

    # Assert that the cached response matches the actual response
    assert workspace_mapping.__wrapped__(handled_workspace) == workspace_mapping(
        handled_workspace
    )
    workspace_mapping.cache_clear()

    first_resp = workspace_mapping(handled_workspace)
    second_resp = workspace_mapping(handled_workspace)

    # Assert that cached response is idempotent
    assert first_resp == second_resp


@pytest.mark.skip()
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


@pytest.mark.skip()
def test_workspace_create():
    """Test that creating a workspace doesn't result in invalid caching."""
    workspace_name = uuid4().hex

    pre_create = workspace_mapping(workspace_name)
    create_workspace(workspace_name)
    post_create = workspace_mapping(workspace_name)
    post_create_exists = workspace_exists(workspace_name)

    # Teardown
    delete_workspace(workspace_name)

    # Asserts
    assert pre_create is None
    assert post_create is not None
    assert post_create_exists


@pytest.mark.skip()
def test_workspace_delete(generated_workspace):
    """Tests that deleting a workspace doesn't result in invalid caching."""

    pre_delete = workspace_mapping(generated_workspace)
    delete_workspace(generated_workspace)
    post_delete = workspace_mapping(generated_workspace)
    exists_post_delete = workspace_exists(generated_workspace)

    # Asserts
    assert pre_delete is not None
    assert post_delete is None
    assert not exists_post_delete


@pytest.mark.skip()
def test_workspace_rename(generated_workspace):
    """Test that renaming a workspace doesn't result in invalid caching."""
    new_workspace_name = uuid4().hex

    pre_rename = workspace_mapping(generated_workspace)
    rename_workspace(generated_workspace, new_workspace_name)
    post_rename_old = workspace_mapping(generated_workspace)
    post_rename_new = workspace_mapping(new_workspace_name)

    new_exists = workspace_exists(new_workspace_name)
    old_exists = workspace_exists(generated_workspace)

    # Teardown
    delete_workspace(new_workspace_name)

    # Asserts
    assert pre_rename is not None
    assert post_rename_old is None
    assert post_rename_new is not None

    assert new_exists
    assert not old_exists
