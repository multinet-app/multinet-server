"""Tests functions in the CSV Uploader Flask Blueprint."""
import json
import os
from collections import OrderedDict

from multinet.util import data_path_test
from multinet.uploaders.d3_json import validate_d3_json

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def test_validate_d3_json():
    """Tests the validate_csv function."""
    # Arrange: Import the les miserables datasets with and without errors
    with open(data_path_test("miserables.json")) as f:
        good_data = json.load(f, object_pairs_hook=OrderedDict)
    with open(data_path_test("miserables_duplicate_nodes.json")) as f:
        dup_node_data = json.load(f, object_pairs_hook=OrderedDict)
    with open(data_path_test("miserables_inconsistent_link_keys.json")) as f:
        incon_keys = json.load(f, object_pairs_hook=OrderedDict)
    with open(data_path_test("miserables_invalid_link_keys.json")) as f:
        inval_keys = json.load(f, object_pairs_hook=OrderedDict)

    # Act: Test all the data files and save their outcomes
    outcome1 = validate_d3_json(good_data)
    outcome2 = validate_d3_json(dup_node_data)
    outcome3 = validate_d3_json(incon_keys)
    outcome4 = validate_d3_json(inval_keys)

    # Assert: Check the outcomes against what we expect
    assert len(outcome1) == 0

    assert len(outcome2) == 1
    assert outcome2[0] == {"error": "node_duplicates"}

    assert len(outcome3) == 1
    assert outcome3[0] == {"error": "inconsistent_link_keys"}

    assert len(outcome4) == 2
    assert outcome4[0] == {"error": "invalid_link_keys"}
    assert outcome4[1] == {"error": "inconsistent_link_keys"}
