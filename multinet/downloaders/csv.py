"""Multinet uploader for CSV files."""
import csv
from flasgger import swag_from
from io import StringIO

from multinet.util import require_db, generate_filtered_docs
from multinet.errors import NotFound
from multinet.db.models.workspace import Workspace

from flask import Blueprint, Response

# Import types
from typing import Any, Generator


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
    loaded_workspace = Workspace(workspace)
    if not loaded_workspace.has_table(table):
        raise NotFound("table", table)

    loaded_table = loaded_workspace.table(table)
    table_rows = loaded_table.rows()["rows"]

    fields = loaded_table.headers()

    def csv_row_generator() -> Generator[str, None, None]:
        header_line = StringIO()
        writer = csv.DictWriter(header_line, fieldnames=fields)
        writer.writeheader()
        yield header_line.getvalue()

        for csv_row in generate_filtered_docs(table_rows):
            line = StringIO()
            writer = csv.DictWriter(line, fieldnames=fields)
            writer.writerow(csv_row)
            yield line.getvalue()

    response = Response(csv_row_generator(), mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={table}.csv"
    response.headers["Content-type"] = "text/csv"

    return response
