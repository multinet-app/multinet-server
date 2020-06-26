"""Tests that ensure fixtures act properly."""

from multinet.user import MULTINET_COOKIE


def test_generated_workspace(handled_workspace, handled_user, server):
    """Test that a generated workspace exists when querying the API."""

    with server.session_transaction() as session:
        session[MULTINET_COOKIE] = handled_user.multinet.session

    resp = server.get(f"/api/workspaces/{handled_workspace}")
    assert resp.status_code == 200
