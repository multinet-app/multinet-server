"""Multinet uploader for nested JSON files."""
import json
from io import StringIO
import pandas as pd

from .. import db, util
from ..util import decode_data

from flask import Blueprint, request
from flask import current_app as app

# Import types
from typing import Any

bp = Blueprint("d3_json", __name__)
bp.before_request(util.require_db)


def validate_d3_json():
    """Works something."""
    pass


@bp.route("/<workspace>/<table>", methods=["POST"])
def upload(workspace: str, table: str) -> Any:
    """Store a d3-esque json file into the database as a node or edge table.

    `workspace` - the target workspace
    `table` - the target table
    `data` - the json data, passed in the request body. The json data should contain
    nodes: [] and links: []
    """
    app.logger.info("Bulk Loading D3 Json Data")

    # Get data from the request and load it as json
    body = decode_data(request.data)
    data = json.load(StringIO(body))

    # Extract each table to pandas dataframes and change column names
    nodes = pd.DataFrame(data["nodes"])
    nodes["_key"] = nodes["id"]
    del nodes["id"]
    print(nodes)

    links = pd.DataFrame(data["links"])
    links["_from"] = links["source"]
    links["_to"] = links["target"]
    del links["source"]
    del links["target"]
    print(links)

    # Create the workspace
    space = db.db(workspace)
    if space.has_collection(table):
        coll = space.collection(table)
    else:
        coll = space.create_collection(table, edge=True)
        coll = space.create_collection(table, edge=False)

    results = coll.insert_many()
    return dict(count=len(results))
