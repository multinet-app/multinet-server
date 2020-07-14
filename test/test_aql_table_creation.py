"""Tests for creating a table from an AQL query."""


def test_malformed_aql(managed_workspace, server):
    """Test that invalid/malformed AQL results in an error."""
    table_name = "malformed_table"
    malformed_aql = "FOR members RETURN member"
    malformed_aql_error = "unexpected RETURN declaration"

    resp = server.post(
        f"/api/workspaces/{managed_workspace}/tables",
        data=malformed_aql,
        query_string={"table": table_name},
    )

    assert resp.status_code == 400
    assert malformed_aql_error in resp.data.decode()


def test_mutating_aql(populated_workspace, server):
    """Test that an AQL query which updates documents fails."""
    workspace, _, node_table, _ = populated_workspace

    mutating_aql = f"FOR thing in {node_table} UPDATE thing in {node_table}"
    mutating_aql_error = "AQL: read only"

    new_table_name = "mutating_table"
    resp = server.post(
        f"/api/workspaces/{workspace}/tables",
        data=mutating_aql,
        query_string={"table": new_table_name},
    )

    assert resp.status_code == 400
    assert mutating_aql_error in resp.data.decode()


def test_existing_table(populated_workspace, server):
    """Test that attempt to create a table with an existing name fails."""
    workspace, _, node_table, _ = populated_workspace

    aql = f"FOR thing in {node_table} RETURN thing"

    resp = server.post(
        f"/api/workspaces/{workspace}/tables",
        data=aql,
        query_string={"table": node_table},
    )

    assert resp.status_code == 409
    assert resp.data.decode() == node_table


def test_create_node_table(populated_workspace, server):
    """Test that creating a node table succeeds."""
    workspace, _, node_table, edge_table = populated_workspace

    aql = f"FOR doc in {node_table} RETURN doc"
    new_table_name = "new_table"

    resp = server.post(
        f"/api/workspaces/{workspace}/tables",
        data=aql,
        query_string={"table": new_table_name},
    )

    assert resp.status_code == 200
    assert resp.data.decode() == new_table_name


def test_create_edge_table(populated_workspace, server):
    """Test that creating an edge table succeeds."""
    workspace, _, node_table, edge_table = populated_workspace

    aql = f"FOR doc in {edge_table} RETURN doc"
    new_table_name = "new_table"

    resp = server.post(
        f"/api/workspaces/{workspace}/tables",
        data=aql,
        query_string={"table": new_table_name},
    )

    assert resp.status_code == 200
    assert resp.data.decode() == new_table_name


def test_unsupported_table(populated_workspace, server):
    """Test that creating a non edge/node table results in an error."""
    workspace, _, node_table, edge_table = populated_workspace

    aql = f"FOR doc in {edge_table} RETURN {{ name: 'something' }}"
    new_table_name = "new_table"

    resp = server.post(
        f"/api/workspaces/{workspace}/tables",
        data=aql,
        query_string={"table": new_table_name},
    )

    error_types = {error["type"] for error in resp.json["errors"]}

    assert resp.status_code == 400
    assert "UnsupportedTable" in error_types
