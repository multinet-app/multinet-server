"""Multinet uploader for CSV files."""
import csv
from flasgger import swag_from
from io import StringIO
import re

from .. import db, util
from ..errors import ValidationFailed
from ..util import decode_data
from ..types import (
    ValidationFailedError,
    CSVInvalidSyntax,
    CSVInvalidRow,
    BasicError,
    NoBodyError,
)

from flask import Blueprint, request
from flask import current_app as app

# Import types
from typing import Set, MutableMapping, Sequence, Any, List


bp = Blueprint("csv", __name__)
bp.before_request(util.require_db)


def validate_csv(rows: Sequence[MutableMapping]) -> None:
    """Perform any necessary CSV validation, and return appropriate errors."""
    data_errors: List[ValidationFailedError] = []

    fieldnames = rows[0].keys()
    if "_key" in fieldnames:
        # Node Table, check for key uniqueness
        keys = [row["_key"] for row in rows]
        unique_keys: Set[str] = set()
        duplicates = set()
        for key in keys:
            if key in unique_keys:
                duplicates.add(key)
            else:
                unique_keys.add(key)

        if len(duplicates) > 0:
            data_errors.append(
                BasicError(type="csv_duplicate_keys", body=list(duplicates))
            )

    elif "_from" in fieldnames and "_to" in fieldnames:
        # Edge Table, check that each cell has the correct format
        valid_cell = re.compile("[^/]+/[^/]+")

        invalid_syntax_errors: List[CSVInvalidRow] = []

        for i, row in enumerate(rows):
            fields: List[str] = []
            if not valid_cell.match(row["_from"]):
                fields.append("_from")
            if not valid_cell.match(row["_to"]):
                fields.append("_to")

            if fields:
                # i+2 -> +1 for index offset, +1 due to header row
                invalid_syntax_errors.append({"fields": fields, "row": i + 2})

        if invalid_syntax_errors:
            data_errors.append(
                CSVInvalidSyntax(type="csv_invalid_syntax", body=invalid_syntax_errors)
            )
    else:
        # Unsupported Table, error since we don't know what's coming in
        data_errors.append(NoBodyError(type="csv_unsupported_table"))

    if len(data_errors) > 0:
        raise ValidationFailed(data_errors)


@bp.route("/<workspace>/<table>", methods=["POST"])
@swag_from("swagger/csv.yaml")
def upload(workspace: str, table: str) -> Any:
    """
    Store a CSV file into the database as a node or edge table.

    `workspace` - the target workspace
    `table` - the target table
    `data` - the CSV data, passed in the request body. If the CSV data contains
             `_from` and `_to` fields, it will be treated as an edge table.
    """
    app.logger.info("Bulk Loading")

    # Read the request body into CSV format
    body = decode_data(request.data)

    rows = list(csv.DictReader(StringIO(body)))

    # Perform validation.
    validate_csv(rows)

    # Set the collection, paying attention to whether the data contains
    # _from/_to fields.
    space = db.db(workspace)
    if space.has_collection(table):
        coll = space.collection(table)
    else:
        fieldnames = rows[0].keys()
        edges = "_from" in fieldnames and "_to" in fieldnames
        coll = space.create_collection(table, edge=edges)

    # Insert the data into the collection.
    results = coll.insert_many(rows)
    return dict(count=len(results))
