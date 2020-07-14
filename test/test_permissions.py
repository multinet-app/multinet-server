"""Tests for permissions infrastructure."""

from multinet.user import MULTINET_COOKIE


def test_require_reader(server, handled_workspace, handled_user):
    """Test the `require_reader` decorator."""
    with server.session_transaction() as session:
        session[MULTINET_COOKIE] = handled_user.multinet.session

    resp = server.get(f"/api/workspaces/{handled_workspace}")
    assert resp.status_code == 200
    assert resp.json["permissions"]["owner"] == handled_user.sub
