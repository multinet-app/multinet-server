"""Utilities for validating tabular data for upload to Multinet."""

import re
from typing import Set, MutableMapping, Sequence, List

from multinet.validation import ValidationFailure, DuplicateKey, UnsupportedTable


class InvalidRow(ValidationFailure):
    """Invalid syntax in a CSV file."""

    row: int
    columns: List[str]


class KeyFieldAlreadyExists(ValidationFailure):
    """CSV file has both existing _key field and specified key field."""

    key: str


class KeyFieldDoesNotExist(ValidationFailure):
    """The specified key field does not exist."""

    key: str


class MissingBody(ValidationFailure):
    """Missing body in a CSV file."""


def is_edge_table(rows: Sequence[MutableMapping]) -> bool:
    """Determine if this table should be treated as an edge table."""
    fieldnames = rows[0].keys()
    return "_from" in fieldnames and "_to" in fieldnames


def is_node_table(rows: Sequence[MutableMapping], key_field: str) -> bool:
    """Determine if this table should be treated as a node table."""
    fieldnames = rows[0].keys()
    return key_field != "_key" or "_key" in fieldnames


def validate_edge_table(rows: Sequence[MutableMapping]) -> List[ValidationFailure]:
    """Validate that the given table is a valid edge table."""
    validation_errors: List[ValidationFailure] = []

    # Checks that a cell has the form table_name/key
    valid_cell = re.compile("[^/]+/[^/]+")

    for i, row in enumerate(rows):
        fields: List[str] = []
        if not valid_cell.match(row["_from"]):
            fields.append("_from")
        if not valid_cell.match(row["_to"]):
            fields.append("_to")

        if fields:
            # i+2 -> +1 for index offset, +1 due to header row
            validation_errors.append(InvalidRow(columns=fields, row=i + 2))

    return validation_errors


def validate_node_table(
    rows: Sequence[MutableMapping], key_field: str, overwrite: bool
) -> List[ValidationFailure]:
    """Validate that the given table is a valid node table."""
    fieldnames = rows[0].keys()
    validation_errors: List[ValidationFailure] = []

    if key_field != "_key" and key_field not in fieldnames:
        validation_errors.append(KeyFieldDoesNotExist(key=key_field))

    elif "_key" in fieldnames and key_field != "_key" and not overwrite:
        validation_errors.append(KeyFieldAlreadyExists(key=key_field))
    else:
        keys = (row[key_field] for row in rows)
        unique_keys: Set[str] = set()
        for key in keys:
            if key in unique_keys:
                validation_errors.append(DuplicateKey(key=key))
            else:
                unique_keys.add(key)

    return validation_errors


def validate_csv(
    rows: Sequence[MutableMapping], key_field: str, overwrite: bool
) -> List[ValidationFailure]:
    """Perform any necessary CSV validation, and return appropriate errors."""
    if not rows:
        return [MissingBody()]

    if is_edge_table(rows):
        return validate_edge_table(rows)
    elif is_node_table(rows, key_field):
        return validate_node_table(rows, key_field, overwrite)
    else:
        return [UnsupportedTable()]
