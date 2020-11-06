"""Utilities for validating tabular data for upload to Multinet."""

import re
from typing import Set, MutableMapping, Sequence, List

from multinet.errors import ValidationFailed
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


def validate_edge_table(rows: Sequence[MutableMapping]) -> None:
    """Validate that the given table is a valid edge table."""
    data_errors: List[ValidationFailure] = []

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
            data_errors.append(InvalidRow(columns=fields, row=i + 2))

    if len(data_errors) > 0:
        raise ValidationFailed(data_errors)


def validate_node_table(
    rows: Sequence[MutableMapping], key_field: str, overwrite: bool
) -> None:
    """Validate that the given table is a valid node table."""
    fieldnames = rows[0].keys()
    data_errors: List[ValidationFailure] = []

    if key_field != "_key" and key_field not in fieldnames:
        data_errors.append(KeyFieldDoesNotExist(key=key_field))
        raise ValidationFailed(data_errors)

    if "_key" in fieldnames and key_field != "_key" and not overwrite:
        data_errors.append(KeyFieldAlreadyExists(key=key_field))
        raise ValidationFailed(data_errors)

    keys = (row[key_field] for row in rows)
    unique_keys: Set[str] = set()
    for key in keys:
        if key in unique_keys:
            data_errors.append(DuplicateKey(key=key))
        else:
            unique_keys.add(key)

    if len(data_errors) > 0:
        raise ValidationFailed(data_errors)


def validate_csv(
    rows: Sequence[MutableMapping], key_field: str, overwrite: bool
) -> None:
    """Perform any necessary CSV validation, and return appropriate errors."""
    if not rows:
        raise ValidationFailed([MissingBody()])

    if is_edge_table(rows):
        validate_edge_table(rows)
    elif is_node_table(rows, key_field):
        validate_node_table(rows, key_field, overwrite)
    else:
        raise ValidationFailed([UnsupportedTable()])
