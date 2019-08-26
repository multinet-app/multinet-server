"""Multinet uploader for CSV files."""
import csv
from io import StringIO
import re

from .. import db, util

from flask import Blueprint, request
from flask import current_app as app

bp = Blueprint("csv", __name__)
bp.before_request(util.require_db)


def validate_csv(rows):
    """Perform any necessary CSV validation, and return appropriate errors."""
    fieldnames = rows[0].keys()
    if "_key" in fieldnames:
        # Node Table, check for key uniqueness
        keys = [row["_key"] for row in rows]
        uniqueKeys = set()
        duplicates = set()
        for key in keys:
            if key in uniqueKeys:
                duplicates.add(key)
            else:
                uniqueKeys.add(key)

        if len(duplicates) > 0:
            return {"error": "duplicate", "detail": list(duplicates)}
    elif "_from" in fieldnames and "_to" in fieldnames:
        # Edge Table, check that each cell has the correct format
        valid_cell = re.compile("[^/]+/[^/]+")

        detail = []

        for i, row in enumerate(rows):
            fields = []
            if not valid_cell.match(row["_from"]):
                fields.append("_from")
            if not valid_cell.match(row["_to"]):
                fields.append("_to")

            if fields:
                # i+2 -> +1 for index offset, +1 due to header row
                detail.append({"fields": fields, "row": i + 2})

        if detail:
            return {"error": "syntax", "detail": detail}

    return None


@bp.route("/<workspace>/<table>", methods=["POST"])
def upload(workspace, table):
    """
    Store a CSV file into the database as a node or edge table.

    `workspace` - the target workspace
    `table` - the target table
    `data` - the CSV data, passed in the request body. If the CSV data contains
             `_from` and `_to` fields, it will be treated as an edge table.
    """
    app.logger.info("Bulk Loading")

    # Read the request body into CSV format
    body = request.data.decode("utf8")
    rows = list(csv.DictReader(StringIO(body)))

    # Perform validation.
    result = validate_csv(rows)
    if result:
        return (result, "400 CSV Validation Failed")

    # Set the collection, paying attention to whether the data contains
    # _from/_to fields.
    workspace = db.db(workspace)
    if workspace.has_collection(table):
        coll = workspace.collection(table)
    else:
        fieldnames = rows[0].keys()
        edges = "_from" in fieldnames and "_to" in fieldnames
        coll = workspace.create_collection(table, edge=edges)

    # Insert the data into the collection.
    results = coll.insert_many(rows)
    return dict(count=len(results))
