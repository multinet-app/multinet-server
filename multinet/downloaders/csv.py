"""Multinet uploader for CSV files."""
import csv
from flasgger import swag_from
from io import StringIO

from multinet.util import require_db, filter_unwanted_keys, generate_filtered_docs
from multinet.db import get_workspace_db, workspace_table
from multinet.errors import NotFound

from flask import Blueprint, make_response

# Import types
from typing import Any


bp = Blueprint("download_csv", __name__)
bp.before_request(require_db)


@bp.route("/<workspace>/<table>", methods=["GET"])
@swag_from("swagger/csv.yaml")
def download(workspace: str, table: str) -> Any:
    """
    Download a table from the database as a CSV file.

    `workspace` - the target workspace
    `table` - the target table
    """
    space = get_workspace_db(workspace)
    if not space.has_collection(table):
        raise NotFound("table", table)

    limit = workspace_table(workspace, table, 0, 0)["count"]
    table_rows = workspace_table(workspace, table, 0, limit)["rows"]
    fields = filter_unwanted_keys(table_rows[0]).keys()

    io = StringIO()
    writer = csv.DictWriter(io, fieldnames=fields)

    writer.writeheader()
    for row in generate_filtered_docs(table_rows):
        writer.writerow(row)

    output = make_response(io.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={table}.csv"
    output.headers["Content-type"] = "text/csv"

    return output
