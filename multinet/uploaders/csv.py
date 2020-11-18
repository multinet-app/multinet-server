"""Multinet uploader for CSV files."""
import csv
import json
from flasgger import swag_from
from io import StringIO

from multinet import util
from multinet.db.models.workspace import Workspace
from multinet.db.models.table import table_metadata_from_dict
from multinet.auth.util import require_writer
from multinet.errors import (
    AlreadyExists,
    FlaskTuple,
    ServerError,
    BadQueryArgument,
    ValidationFailed,
)
from multinet.util import decode_data
from multinet.metadata.utils import process_rows_with_metadata
from multinet.validation.csv import validate_csv, is_edge_table

from flask import Blueprint, request
from flask import current_app as app
from webargs import fields as webarg_fields
from webargs.flaskparser import use_kwargs

# Import types
from typing import Any, List, Dict, Optional


bp = Blueprint("csv", __name__)
bp.before_request(util.require_db)


class CSVReadError(ServerError):
    """Exception for unprocessable CSV data."""

    def flask_response(self) -> FlaskTuple:
        """Generate a 415 error for the read failure."""
        return ("Could not read CSV data", "415 Unsupported Media Type")


def set_table_key(rows: List[Dict[str, str]], key: str) -> List[Dict[str, str]]:
    """Update the _key field in each row."""
    new_rows: List[Dict[str, str]] = []
    for row in rows:
        new_row = dict(row)
        new_row["_key"] = new_row[key]
        new_rows.append(new_row)

    return new_rows


@bp.route("/<workspace>/<table>", methods=["POST"])
@use_kwargs(
    {
        "key": webarg_fields.Str(location="query"),
        "overwrite": webarg_fields.Bool(location="query"),
        "metadata": webarg_fields.Str(location="query"),
    }
)
@require_writer
@swag_from("swagger/csv.yaml")
def upload(
    workspace: str,
    table: str,
    key: str = "_key",
    overwrite: bool = False,
    metadata: Optional[str] = None,
) -> Any:
    """
    Store a CSV file into the database as a node or edge table.

    `workspace` - the target workspace
    `table` - the target table
    `data` - the CSV data, passed in the request body. If the CSV data contains
             `_from` and `_to` fields, it will be treated as an edge table.
    """
    loaded_workspace = Workspace(workspace)

    if loaded_workspace.has_table(table):
        raise AlreadyExists("table", table)

    app.logger.info("Bulk Loading")

    # Read the request body into CSV format
    body = decode_data(request.data)

    try:
        # Type to a Dict rather than an OrderedDict
        rows: List[Dict[str, str]] = list(csv.DictReader(StringIO(body)))
    except csv.Error:
        raise CSVReadError()

    # TODO: This temporarily needs to be done here, so that validation of the metadata
    # can be done before the table is actually created. Once the API is updated, this
    # will change.
    metadata_dict = {}
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.decoder.JSONDecodeError:
            raise BadQueryArgument("metadata", metadata)

    table_metadata = table_metadata_from_dict(metadata_dict)
    rows, metadata_validation_errors = process_rows_with_metadata(rows, table_metadata)

    # Perform validation.
    csv_validation_errors = validate_csv(rows, key, overwrite)

    validation_errors = [*metadata_validation_errors, *csv_validation_errors]
    if len(validation_errors):
        raise ValidationFailed(errors=validation_errors)

    # Once we reach here, we know that the specified key field must be present,
    # and either:
    #   key == "_key"   # noqa: E800
    #   or key != "_key" and the "_key" field is not present
    #   or key != "_key" and "_key" is present, but overwrite = True
    if key != "_key":
        rows = set_table_key(rows, key)

    # Create table and insert the data
    loaded_table = loaded_workspace.create_table(table, edge=is_edge_table(rows))

    # Set table metadata
    loaded_table.set_metadata(metadata_dict)

    results = loaded_table.insert(rows)
    return {"count": len(results)}
