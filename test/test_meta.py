"""Tests that ensure fixtures act properly."""

from multinet.user import MULTINET_COOKIE


def test_generated_workspace(managed_workspace, managed_user, server):
    """Test that a generated workspace exists when querying the API."""

    with server.session_transaction() as session:
        session[MULTINET_COOKIE] = managed_user.multinet.session

    resp = server.get(f"/api/workspaces/{managed_workspace}")
    assert resp.status_code == 200
