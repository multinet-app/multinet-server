"""Tests that ensure fixtures act properly."""


def test_generated_workspace(handled_workspace, server):
    """Test that a generated workspace exists when querying the API."""
    resp = server.get(f"/api/workspaces/{handled_workspace}")
    assert resp.status_code == 200


def test_populated_workspace(populated_workspace, server):
    """Test that the populated workspace has a graph, an edge and node table."""
    workspace, graphs, *tables = populated_workspace

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
