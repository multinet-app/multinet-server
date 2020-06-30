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


def test_populated_workspace(populated_workspace, managed_user, server):
    """Test that the populated workspace has a graph, an edge and node table."""
    workspace, graphs, *tables = populated_workspace

    with managed_user.login(server):
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
