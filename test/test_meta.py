"""Tests that ensure fixtures act properly."""


def test_generated_workspace(handled_workspace, server):
    """Test that a generated workspace exists when querying the API."""
    resp = server.get(f"/api/workspaces/{handled_workspace}")
    assert resp.status_code == 200
