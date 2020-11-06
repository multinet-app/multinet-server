"""Testing operations on metadata."""
import conftest
import pytest
import json


def test_set_valid_table_metadata(populated_workspace, managed_user, server):
    """Test that setting valid metadata succeeds."""
    workspace, _, node_table, _ = populated_workspace
    metadata = {"columns": [{"key": "test", "type": "label"}]}

    with conftest.login(managed_user, server):
        resp = server.put(
            f"/api/workspaces/{workspace.name}/tables/{node_table}/metadata",
            json=metadata,
        )

        assert resp.status_code == 200
        assert resp.json["table"] == metadata


@pytest.mark.parametrize(
    "metadata, expected",
    [
        ({"columns": [{"key": "test", "type": "invalid"}]}, 400),
        ({"columns": [{"foo": "bar"}]}, 400),
        ({"foo": "bar"}, 200),
    ],
)
def test_set_invalid_table_metadata(
    populated_workspace, managed_user, server, metadata, expected
):
    """Test that setting invalid metadata fails."""
    workspace, _, node_table, _ = populated_workspace

    with conftest.login(managed_user, server):
        resp = server.put(
            f"/api/workspaces/{workspace.name}/tables/{node_table}/metadata",
            json=metadata,
        )
        assert resp.status_code == expected


# NOTE: Including metadata in CSV uploads will likely be removed in a future API change
def test_csv_upload_with_metadata(
    managed_workspace, managed_user, server, data_directory
):
    """Test that uploading a CSV file with metadata succeeds."""

    table_name = "test"
    metadata = {"columns": [{"key": "test", "type": "label"}]}

    with open(data_directory / "membership_with_keys.csv") as csv_file:
        request_body = csv_file.read()

    with conftest.login(managed_user, server):
        resp = server.post(
            f"/api/csv/{managed_workspace.name}/{table_name}",
            data=request_body,
            query_string={"metadata": json.dumps(metadata)},
        )

        assert resp.status_code == 200

        resp = server.get(
            f"/api/workspaces/{managed_workspace.name}/tables/{table_name}/metadata"
        )

        assert resp.status_code == 200
        assert resp.json["table"] == metadata
