"""Tests that ensure fixtures act properly."""

from multinet.user import MULTINET_COOKIE


def test_generated_workspace(handled_workspace, handled_user, server):
    """Test that a generated workspace exists when querying the API."""

    with server.session_transaction() as session:
        session[MULTINET_COOKIE] = handled_user.multinet.session

    resp = server.get(f"/api/workspaces/{handled_workspace}")
    assert resp.status_code == 200


def test_populated_workspace(populated_workspace, handled_user, server):
    """Test that the populated workspace has a graph, an edge and node table."""
    workspace, graphs, *tables = populated_workspace

    with server.session_transaction() as session:
        session[MULTINET_COOKIE] = handled_user.multinet.session

    # Graphs
    resp = server.get(f"/api/workspaces/{workspace}/graphs")
    assert resp.status_code == 200

    graphs = resp.json
    assert len(graphs) == 1
    assert graphs[0] == "miserables"

    # Tables
    resp = server.get(f"/api/workspaces/{workspace}/tables")
    assert resp.status_code == 200

    tables = resp.json
    assert len(tables) == 2
    assert "miserables_nodes" in tables
    assert "miserables_links" in tables
