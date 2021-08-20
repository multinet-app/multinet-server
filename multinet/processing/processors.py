"""Functions that process raw table entries."""
import json
from dateutil import parser as dateutilparser
from datetime import datetime

# Import types
from typing import Optional, Union


def process_boolean_entry(entry: str) -> bool:
    """Try to determine base format of boolean so it can be converted properly."""

    def from_int(x: str) -> Optional[bool]:
        if x == "0" or x == "1":
            return bool(int(x))
        return None

    def from_json_bool(x: str) -> Optional[bool]:
        if x == "true" or x == "false":
            return json.loads(x)
        return None

    def from_yaml_bool(x: str) -> Optional[bool]:
        if x == "no" or x == "off":
            return False
        if x == "yes" or x == "on":
            return True

        return None

    def cast_col_entry(x: str) -> bool:
        casters = [from_int, from_json_bool, from_yaml_bool]
        for caster in casters:
            cast_row = caster(x)
            if cast_row is not None:
                return cast_row

        raise ValueError

    return cast_col_entry(entry)


def process_date_entry(entry: str) -> str:
    """Try to read a date as an ISO 8601 string or unix timestamp."""
    try:
        # Raises ValueError is entry is not a float/int
        # Raises ValueError if the number is out of range
        return datetime.fromtimestamp(float(entry)).isoformat()
    except ValueError:
        # Raises ValueError if it cannot parse the string into a datetime object
        return dateutilparser.parse(entry).isoformat()


def process_number_entry(entry: str) -> Union[int, float]:
    """Try to read a number from a given string."""
    try:
        return int(entry)
    except ValueError:
        return float(entry)
