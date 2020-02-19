"""Tests functions in the CSV Uploader Flask Blueprint."""
import csv
import os
import pytest
from io import StringIO

from multinet.util import TEST_DATA_DIR
from multinet.errors import ValidationFailed, DecodeFailed
from multinet.uploaders.csv import validate_csv, decode_data, InvalidRow
from multinet.validation import DuplicateKey


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
    assert all(err in validation_resp for err in correct)

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
            InvalidRow(row=3, fields=["_from"]),
            InvalidRow(row=4, fields=["_to"]),
            InvalidRow(row=5, fields=["_from", "_to"]),
        ]
    ]
    assert all(err in validation_resp for err in correct)

    # Test unicode decode errors
    test_data = b"\xff\xfe_\x00k\x00e\x00y\x00,\x00n\x00a\x00m\x00e\x00\n"
    pytest.raises(DecodeFailed, decode_data, test_data)
