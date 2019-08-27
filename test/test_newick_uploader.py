"""Tests functions in the Neick Uploader Flask Blueprint."""
import newick
import os

from multinet.uploaders.newick import validate_newick, decode_data

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def test_validate_newick():
    """Tests the validate_csv function."""
    duplicate_keys_file_path = os.path.join(
        TEST_DATA_DIR, "basic_newick_duplicates.tree"
    )

    # Test duplicate keys
    with open(duplicate_keys_file_path) as test_file:
        test_file = test_file.read()

    body = newick.loads(test_file)
    validation_resp = validate_newick(body)
    assert "errors" in validation_resp.keys()

    # Test unicode decode errors
    test_data = (
        b"\xff\xfe(\x00B\x00,\x00(\x00A\x00,"
        b"\x00C\x00,\x00E\x00)\x00,\x00D\x00)\x00;\x00\n\x00"
    )
    decoded_data = decode_data(test_data)
    assert decoded_data is None