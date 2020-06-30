"""Tests that ensure fixtures act properly."""


def test_generated_workspace(managed_workspace, managed_user, server):
    """Test that a generated workspace exists when querying the API."""

    with managed_user.login(server):
        resp = server.get(f"/api/workspaces/{managed_workspace}")
        assert resp.status_code == 200


def test_user_context(managed_workspace, managed_user, server):
    """Test that the user context properly controls login."""
    with managed_user.login(server):
        resp = server.get(f"/api/workspaces/{managed_workspace}/tables")
        assert resp.status_code == 200

    resp = server.get(f"/api/workspaces/{managed_workspace}/tables")
    assert resp.status_code == 401
