"""Tests functions in the CSV Uploader Flask Blueprint."""
import json
from collections import OrderedDict

from multinet.util import data_path
from multinet.uploaders.d3_json import (
    validate_d3_json,
    InconsistentLinkKeys,
    InvalidLinkKeys,
    NodeDuplicates,
)


def test_validate_d3_json():
    """Tests the validate_csv function."""
    # Arrange: Import the les miserables datasets with and without errors
    with open(data_path("miserables.json")) as f:
        good_data = json.load(f, object_pairs_hook=OrderedDict)
    with open(data_path("miserables_duplicate_nodes.json")) as f:
        dup_node_data = json.load(f, object_pairs_hook=OrderedDict)
    with open(data_path("miserables_inconsistent_link_keys.json")) as f:
        incon_keys = json.load(f, object_pairs_hook=OrderedDict)
    with open(data_path("miserables_invalid_link_keys.json")) as f:
        inval_keys = json.load(f, object_pairs_hook=OrderedDict)

    # Act: Test all the data files and save their outcomes
    outcome1 = validate_d3_json(good_data)
    outcome2 = validate_d3_json(dup_node_data)
    outcome3 = validate_d3_json(incon_keys)
    outcome4 = validate_d3_json(inval_keys)

    # Assert: Check the outcomes against what we expect
    assert len(outcome1) == 0

    assert len(outcome2) == 1
    assert outcome2[0] == NodeDuplicates()

    assert len(outcome3) == 1
    assert outcome3[0] == InconsistentLinkKeys()

    assert len(outcome4) == 2
    assert outcome4[0] == InvalidLinkKeys()
    assert outcome4[1] == InconsistentLinkKeys()
