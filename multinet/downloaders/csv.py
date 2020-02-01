"""Multinet uploader for CSV files."""
import csv
from flasgger import swag_from
from io import StringIO

from multinet.util import require_db, generate_filtered_docs
from multinet.db import (
    get_workspace_db,
    workspace_table_row_count,
    workspace_table_rows,
    workspace_table_keys,
)
from multinet.errors import NotFound

from flask import Blueprint, make_response

# Import types
from typing import Any


bp = Blueprint("download_csv", __name__)
bp.before_request(require_db)


@bp.route("/workspaces/<workspace>/tables/<table>/download", methods=["GET"])
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

    limit = workspace_table_row_count(workspace, table)
    table_rows = workspace_table_rows(workspace, table, 0, limit)
    fields = workspace_table_keys(workspace, table, filter_keys=True)

    io = StringIO()
    writer = csv.DictWriter(io, fieldnames=fields)

    writer.writeheader()
    for row in generate_filtered_docs(table_rows):
        writer.writerow(row)

    output = make_response(io.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={table}.csv"
    output.headers["Content-type"] = "text/csv"

    return output
