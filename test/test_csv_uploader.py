"""Tests functions in the CSV Uploader Flask Blueprint."""
import csv
from io import StringIO
import os
import pytest

from multinet.errors import ValidationFailed, DecodeFailed
from multinet.uploaders.csv import validate_csv, decode_data, CSVInvalidRow
from multinet.validation import DuplicateKey

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

    validation_resp = v_error.value.errors
    correct = [err.asdict() for err in [DuplicateKey(key="2"), DuplicateKey(key="5")]]
    assert all([err in validation_resp for err in correct])

    # Test invalid syntax
    with open(invalid_headers_file_path) as test_file:
        test_file = test_file.read()

    rows = list(csv.DictReader(StringIO(test_file)))
    with pytest.raises(ValidationFailed) as v_error:
        validate_csv(rows)

    validation_resp = v_error.value.errors
    correct = [
        err.asdict()
        for err in [
            CSVInvalidRow(row=3, fields=["_from"]),
            CSVInvalidRow(row=4, fields=["_to"]),
            CSVInvalidRow(row=5, fields=["_from", "_to"]),
        ]
    ]
    assert all([err in validation_resp for err in correct])

    # Test unicode decode errors
    test_data = b"\xff\xfe_\x00k\x00e\x00y\x00,\x00n\x00a\x00m\x00e\x00\n"
    pytest.raises(DecodeFailed, decode_data, test_data)
