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
def test_csv_upload_with_invalid_metadata_format(
    managed_workspace, managed_user, server, data_directory
):
    """Test that uploading a CSV file with invalid json fails properly."""

    table_name = "test"
    metadata_str = "{"
    with open(data_directory / "membership_with_keys.csv") as csv_file:
        request_body = csv_file.read()

    with conftest.login(managed_user, server):
        resp = server.post(
            f"/api/csv/{managed_workspace.name}/{table_name}",
            data=request_body,
            query_string={"metadata": metadata_str},
        )

        assert resp.status_code == 400
        assert resp.json["argument"] == "metadata"
        assert resp.json["value"] == metadata_str


# NOTE: Including metadata in CSV uploads will likely be removed in a future API change
def test_csv_upload_with_compatible_metadata(
    managed_workspace, managed_user, server, data_directory
):
    """Test that uploading a CSV file with compatible metadata succeeds."""

    table_name = "test"
    metadata = {
        "columns": [
            {"key": "name", "type": "label"},
            {"key": "latitude", "type": "number"},
            {"key": "longitude", "type": "number"},
            {"key": "altitude", "type": "number"},
            {"key": "year built", "type": "date"},
        ]
    }

    with open(data_directory / "airports.csv") as csv_file:
        request_body = csv_file.read()

    with conftest.login(managed_user, server):
        resp = server.post(
            f"/api/csv/{managed_workspace.name}/{table_name}",
            data=request_body,
            query_string={"metadata": json.dumps(metadata)},
        )

        assert resp.status_code == 200

        # Assert that the table was created and metadata populated successfully
        resp = server.get(
            f"/api/workspaces/{managed_workspace.name}/tables/{table_name}/metadata"
        )

        assert resp.status_code == 200
        assert resp.json["table"] == metadata


# NOTE: Including metadata in CSV uploads will likely be removed in a future API change
def test_csv_upload_with_incompatible_metadata(
    managed_workspace, managed_user, server, data_directory
):
    """Test that uploading a CSV file with incompatible metadata returns errors."""

    table_name = "test"
    metadata = {
        "columns": [
            {"key": "name", "type": "number"},
            {"key": "longitude", "type": "boolean"},
            {"key": "city", "type": "date"},
        ]
    }

    with open(data_directory / "airports.csv") as csv_file:
        request_body = csv_file.read()

    with conftest.login(managed_user, server):
        resp = server.post(
            f"/api/csv/{managed_workspace.name}/{table_name}",
            data=request_body,
            query_string={"metadata": json.dumps(metadata)},
        )

        assert resp.status_code == 400

        # The product of the number of rows (3) and the number of incorrect columns (3)
        assert len(resp.json["errors"]) == 9
        assert all(
            error["type"] == "IncompatibleMetadata" for error in resp.json["errors"]
        )

        # Assert that the table was not created
        resp = server.get(
            f"/api/workspaces/{managed_workspace.name}/tables/{table_name}/metadata"
        )

        assert resp.status_code == 404
        assert resp.status == "404 Table Not Found"
        assert resp.data.decode() == f"{managed_workspace.name}/{table_name}"
