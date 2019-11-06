"""Tests functions in the CSV Uploader Flask Blueprint."""
import json
import os
import pytest

from multinet.errors import ValidationFailed
from multinet.uploaders.d3_json import validate_d3_json

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def test_validate_d3_json():
    """Tests the validate_csv function."""
    # Arrange: Set file paths
    good_file = os.path.join(TEST_DATA_DIR, "miserables.json")
    duplicated_nodes = os.path.join(TEST_DATA_DIR, "miserables_duplicate_nodes.json")
    duplicated_links = os.path.join(TEST_DATA_DIR, "miserables_duplicate_links.json")
    incon_keys = os.path.join(TEST_DATA_DIR, "miserables_inconsistent_link_keys.json")
    inval_keys = os.path.join(TEST_DATA_DIR, "miserables_invalid_link_keys.json")

    # Arrange: Import the les miserables datasets
    with open(good_file) as f:
        good_data = json.load(f)
    with open(duplicated_nodes) as f:
        dup_node_data = json.load(f)
    with open(duplicated_links) as f:
        dup_link_data = json.load(f)
    with open(incon_keys) as f:
        incon_keys = json.load(f)
    with open(inval_keys) as f:
        inval_keys = json.load(f)

    # Act: Test good data (expect no issues, throwing an error here will fail test)
    validate_d3_json(good_data)

    # Act + Assert: Test bad data and assert that there should be errors
    with pytest.raises(ValidationFailed) as v_error:
        validate_d3_json(dup_node_data)
    assert {"error": "node_duplicates"} == v_error.value.errors[0]

    with pytest.raises(ValidationFailed) as v_error:
        validate_d3_json(dup_link_data)
    assert {"error": "link_duplicates"} == v_error.value.errors[0]

    with pytest.raises(ValidationFailed) as v_error:
        validate_d3_json(incon_keys)
    assert {"error": "inconsistent_link_keys"} == v_error.value.errors[0]

    with pytest.raises(ValidationFailed) as v_error:
        validate_d3_json(inval_keys)
    assert {"error": "invalid_link_keys"} == v_error.value.errors[0]
