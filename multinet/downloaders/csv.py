"""Multinet uploader for CSV files."""
import csv
from flasgger import swag_from
from io import StringIO

from .. import db, util
from ..errors import NotFound

from flask import Blueprint, make_response

# Import types
from typing import Any


bp = Blueprint("download_csv", __name__)
bp.before_request(util.require_db)


@bp.route("/<workspace>/<table>", methods=["GET"])
@swag_from("swagger/csv.yaml")
def download(workspace: str, table: str) -> Any:
    """
    Store a CSV file into the database as a node or edge table.

    `workspace` - the target workspace
    `table` - the target table
    """
    space = db.get_workspace_db(workspace)
    if not space.has_collection(table):
        raise NotFound("table", table)

    limit = db.workspace_table(workspace, table, 0, 0)["count"]
    rows = util.filter_unwanted_keys(
        db.workspace_table(workspace, table, 0, limit)["rows"]
    )

    io = StringIO()
    writer = csv.DictWriter(io, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    output = make_response(io.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={table}.csv"
    output.headers["Content-type"] = "text/csv"

    return output
