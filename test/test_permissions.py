"""Tests for permissions infrastructure."""

from multinet.user import MULTINET_COOKIE


def test_require_reader(server, managed_workspace, managed_user):
    """Test the `require_reader` decorator."""
    with managed_user.login(server):
        resp = server.get(f"/api/workspaces/{managed_workspace}")

    assert resp.status_code == 200
    assert resp.json["permissions"]["owner"] == managed_user.sub
