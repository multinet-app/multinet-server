"""Multinet uploader for CSV files."""
import csv
from flasgger import swag_from
from io import StringIO

from multinet import util
from multinet.db.models.workspace import Workspace
from multinet.auth.util import require_writer
from multinet.errors import AlreadyExists, FlaskTuple, ServerError
from multinet.util import decode_data
from multinet.validation.csv import validate_csv

from flask import Blueprint, request
from flask import current_app as app
from webargs import fields as webarg_fields
from webargs.flaskparser import use_kwargs

# Import types
from typing import Any, List, Dict


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
    }
)
@require_writer
@swag_from("swagger/csv.yaml")
def upload(
    workspace: str, table: str, key: str = "_key", overwrite: bool = False
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

    # Perform validation.
    validate_csv(rows, key, overwrite)

    # Once we reach here, we know that the specified key field must be present,
    # and either:
    #   key == "_key"   # noqa: E800
    #   or key != "_key" and the "_key" field is not present
    #   or key != "_key" and "_key" is present, but overwrite = True
    if key != "_key":
        rows = set_table_key(rows, key)

    # Check if it's an edge table or not
    fieldnames = rows[0].keys()
    edges = "_from" in fieldnames and "_to" in fieldnames

    # Create table and insert the data
    loaded_table = loaded_workspace.create_table(table, edges)
    results = loaded_table.insert(rows)

    return {"count": len(results)}
