"""Tests functions in the CSV Uploader Flask Blueprint."""
import json
import os
import pytest

from multinet.errors import ValidationFailed
from multinet.uploaders.d3_json import validate_d3_json

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def test_validate_d3_json():
    """Tests the validate_csv function."""
    good_file = os.path.join(TEST_DATA_DIR, "miserables.json")

    # Import the les miserables dataset
    data = json.load(good_file)

    assert "5" in data

    with pytest.raises(ValidationFailed) as v_error:
        validate_d3_json()
    v_error.value.errors[0]
