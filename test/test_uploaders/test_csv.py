"""Tests functions in the CSV Uploader Flask Blueprint."""
import csv

from multinet.uploaders.csv import validate_csv

DUPLICATE_KEYS = """
_key, name
1, a
2, b
1, c
"""


def test_validate_csv():
    """Tests the validate_csv function."""
    rows = list(csv.DictReader(DUPLICATE_KEYS))
    print(rows)
    validate_csv(rows)
