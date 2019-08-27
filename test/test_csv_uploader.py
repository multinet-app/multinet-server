"""Tests functions in the CSV Uploader Flask Blueprint."""
import csv
from io import StringIO
import os

from multinet.uploaders.csv import validate_csv, decode_data

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def test_validate_csv():
    """Tests the validate_csv function."""
    duplicate_keys_file_path = os.path.join(
        TEST_DATA_DIR, "clubs_invalid_duplicate_keys.csv"
    )

    invalid_headers_file_path = os.path.join(
        TEST_DATA_DIR, "membership_invalid_syntax.csv"
    )

    # Test duplicate keys
    with open(duplicate_keys_file_path) as test_file:
        test_file = test_file.read()

    rows = list(csv.DictReader(StringIO(test_file)))
    validation_resp = validate_csv(rows)
    assert "errors" in validation_resp.keys()
    duplicate_keys = [
        error["detail"]
        for error in validation_resp["errors"]
        if (error["error"] == "duplicate")
    ][0]
    assert "5" in duplicate_keys
    assert "2" in duplicate_keys

    # Test invalid syntax
    with open(invalid_headers_file_path) as test_file:
        test_file = test_file.read()

    rows = list(csv.DictReader(StringIO(test_file)))
    validation_resp = validate_csv(rows)
    invalid_rows = [
        x["row"]
        for x in [
            error for error in validation_resp["errors"] if (error["error"] == "syntax")
        ][0]["detail"]
    ]
    assert "errors" in validation_resp.keys()
    assert 3 in invalid_rows
    assert 4 in invalid_rows
    assert 5 in invalid_rows

    # Test unicode decode errors
    test_data = b"\xff\xfe_\x00k\x00e\x00y\x00,\x00n\x00a\x00m\x00e\x00\n"
    decoded_data = decode_data(test_data)
    assert decoded_data is None
