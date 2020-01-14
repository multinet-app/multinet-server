"""Tests functions in the CSV Uploader Flask Blueprint."""
import csv
from io import StringIO
import os
import pytest

from multinet.errors import ValidationFailed, DecodeFailed
from multinet.uploaders.csv import validate_csv, decode_data
from multinet.types import BasicError

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

    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows)

    validation_resp = v_error.value.errors[0]
    correct = BasicError(type="csv_duplicate_keys", body=["2", "5"])
    assert validation_resp["type"] == correct["type"]
    assert sorted(validation_resp["body"]) == sorted(correct["body"])

    # Test invalid syntax
    with open(invalid_headers_file_path) as test_file:
        test_file = test_file.read()

    rows = list(csv.DictReader(StringIO(test_file)))
    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows)

    validation_resp = v_error.value.errors[0]
    invalid_rows = [x["row"] for x in validation_resp["body"]]
    assert 3 in invalid_rows
    assert 4 in invalid_rows
    assert 5 in invalid_rows

    # Test unicode decode errors
    test_data = b"\xff\xfe_\x00k\x00e\x00y\x00,\x00n\x00a\x00m\x00e\x00\n"
    pytest.raises(DecodeFailed, decode_data, test_data)
