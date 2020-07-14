"""Tests for permissions infrastructure."""

import conftest


def test_require_reader(server, managed_workspace, managed_user):
    """Test the `require_reader` decorator."""
    with conftest.login(managed_user, server):
        resp = server.get(f"/api/workspaces/{managed_workspace}")

    assert resp.status_code == 200
    assert resp.json["permissions"]["owner"] == managed_user.sub
