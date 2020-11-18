"""Utilities for dealing with metadata."""

import json
from dateutil import parser as dateutilparser
from datetime import datetime

from multinet.validation import (
    ValidationFailure,
    IncompatibleMetadata,
    MetadataColumnKeyNotFound,
)
from multinet.types import TableMetadata

# Import types
from typing import Any, Callable, List, Dict, Tuple, Optional, Union

EntryProcessingFunction = Callable[[str], Any]


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

    if entry.isdigit():
        # Raises ValueError if the number is out of range
        return datetime.fromtimestamp(int(entry)).isoformat()

    # Raises ValueError if it cannot parse the string into a datetime object
    return dateutilparser.parse(entry).isoformat()


def process_number_entry(entry: str) -> Union[int, float]:
    """Try to read a number from a given string."""
    return int(entry) if entry.isdigit() else float(entry)


# Maps types to the functions responsible for processing their entries
entry_processing_dict: Dict[str, EntryProcessingFunction] = {
    "number": process_number_entry,
    "boolean": process_boolean_entry,
    "date": process_date_entry,
}


def process_row(
    row_index: int, init_row: Dict[str, str], metadata: TableMetadata
) -> Tuple[Dict[str, Any], List[ValidationFailure]]:
    """Process a single row, returning the processed row, and any errors."""
    validation_errors: List[ValidationFailure] = []

    # Copy row
    row: Dict[str, Any] = dict(init_row)

    for col in metadata.columns:
        entry = row.get(col.key)

        # If any of the following conditions are met, skip processing the entry
        if entry is None:
            validation_errors.append(MetadataColumnKeyNotFound(key=col.key))
            continue

        process_entry = entry_processing_dict.get(col.type)
        if process_entry is None:
            continue

        # Attempt normal entry processing
        try:
            # If the entry is an empty string, replace with None (null)
            processed_entry = process_entry(entry) if entry else None

            # Processing successful, update row entry with its new value
            row[col.key] = processed_entry
        except ValueError:
            # Error in processing entry. Add error, leave entry unchanged
            validation_errors.append(
                IncompatibleMetadata(
                    message=f"Cannot convert entry '{entry}' to type: {col.type}",
                    row=row_index,
                    column=col.key,
                )
            )

    return (row, validation_errors)


def process_rows_with_metadata(
    initial_rows: List[Dict[str, str]], metadata: TableMetadata
) -> Tuple[List[Dict[str, Any]], List[ValidationFailure]]:
    """Perform any processing of table rows with the supplied metadata."""
    if not len(metadata.columns) or not len(initial_rows):
        return (initial_rows, [])

    rows = []
    validation_errors: List[ValidationFailure] = []

    for i, init_row in enumerate(initial_rows):
        row, errors = process_row(i, init_row, metadata)

        rows.append(row)
        validation_errors.extend(errors)

    return (rows, validation_errors)
