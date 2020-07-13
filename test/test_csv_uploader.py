"""Tests functions in the CSV Uploader Flask Blueprint."""
import csv
from io import StringIO
import os
import pytest

from multinet.errors import ValidationFailed, DecodeFailed
from multinet.uploaders.csv import (
    validate_csv,
    decode_data,
    InvalidRow,
    KeyFieldAlreadyExists,
    KeyFieldDoesNotExist,
)
from multinet.validation import DuplicateKey, UnsupportedTable

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def read_csv(filename: str):
    """Read in CSV files."""
    file_path = os.path.join(TEST_DATA_DIR, filename)
    with open(file_path) as path_file:
        return list(csv.DictReader(StringIO(path_file.read())))


def test_edge_table_with_key_field(
    server, managed_workspace, managed_user, data_directory
):
    """Test that an edge table with a key field is recognized as an edge table."""
    with open(data_directory / "membership_with_keys.csv") as csv_file:
        request_body = csv_file.read()

    table_name = "membership_with_keys"
    with managed_user.login(server):
        resp = server.post(
            f"/api/csv/{managed_workspace}/{table_name}", data=request_body
        )
        assert resp.status_code == 200

        edge_table_resp = server.get(
            f"/api/workspaces/{managed_workspace}/tables", query_string={"type": "edge"}
        )
        node_table_resp = server.get(
            f"/api/workspaces/{managed_workspace}/tables", query_string={"type": "node"}
        )

    assert edge_table_resp.status_code == 200
    assert table_name in edge_table_resp.json

    assert node_table_resp.status_code == 200
    assert table_name not in node_table_resp.json


def test_missing_key_field():
    """Test that missing key fields are handled properly."""
    rows = read_csv("startrek_no_key_field.csv")

    correct = UnsupportedTable().asdict()
    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows, key_field="_key", overwrite=False)

    validation_resp = v_error.value.errors
    assert len(validation_resp) == 1
    assert validation_resp[0] == correct


def test_invalid_key_field():
    """Test that specifying a missing key field results in an error."""
    rows = read_csv("startrek.csv")
    invalid_key = "invalid"

    correct = KeyFieldDoesNotExist(key=invalid_key).asdict()
    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows, key_field=invalid_key, overwrite=False)

    validation_resp = v_error.value.errors
    assert len(validation_resp) == 1
    assert validation_resp[0] == correct


def test_key_field_already_exists_a():
    """
    Test that specifying a key when one already exists results in an error.

    (overwrite = False)
    """
    rows = read_csv("startrek.csv")
    key_field = "name"

    correct = KeyFieldAlreadyExists(key=key_field).asdict()
    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows, key_field=key_field, overwrite=False)

    validation_resp = v_error.value.errors
    assert len(validation_resp) == 1
    assert validation_resp[0] == correct


def test_key_field_already_exists_b():
    """
    Test that specifying a key when one already exists doesn't result in an error.

    (overwrite = True).
    """
    rows = read_csv("startrek.csv")
    validate_csv(rows, key_field="name", overwrite=True)


def test_duplicate_keys():
    """Test that duplicate keys are handled properly."""
    rows = read_csv("clubs_invalid_duplicate_keys.csv")
    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows, key_field="_key", overwrite=False)

    validation_resp = v_error.value.errors
    correct = [err.asdict() for err in [DuplicateKey(key="2"), DuplicateKey(key="5")]]
    assert all(err in validation_resp for err in correct)


def test_invalid_headers():
    """Test that invalid headers are handled properly."""
    rows = read_csv("membership_invalid_syntax.csv")
    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows, key_field="_key", overwrite=False)

    validation_resp = v_error.value.errors
    correct = [
        err.asdict()
        for err in [
            InvalidRow(row=3, fields=["_from"]),
            InvalidRow(row=4, fields=["_to"]),
            InvalidRow(row=5, fields=["_from", "_to"]),
        ]
    ]
    assert all(err in validation_resp for err in correct)


def test_decode_failed():
    """Test that the DecodeFailed validation error is raised."""
    test_data = b"\xff\xfe_\x00k\x00e\x00y\x00,\x00n\x00a\x00m\x00e\x00\n"
    pytest.raises(DecodeFailed, decode_data, test_data)
