"""Tests for permissions infrastructure."""

import conftest


def test_require_reader(server, managed_workspace, managed_user):
    """Test the `require_reader` decorator."""
    with conftest.login(managed_user, server):
        resp = server.get(f"/api/workspaces/{managed_workspace.name}/permissions")

    assert resp.status_code == 200
    assert resp.json["owner"]["sub"] == managed_user.sub


# Corresponding login test is in test_meta
def test_logout(server, managed_workspace, managed_user):
    """Test that logout works properly."""

    with conftest.login(managed_user, server):
        resp = server.get(f"/api/user/logout")
        assert resp.status_code == 200

        resp = server.get(f"/api/workspaces/{managed_workspace.name}/permissions")
        assert resp.status_code == 401
