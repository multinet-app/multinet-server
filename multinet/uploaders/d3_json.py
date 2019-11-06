"""Multinet uploader for nested JSON files."""
import json
from io import StringIO
import pandas as pd
from collections import OrderedDict

from .. import db, util
from ..errors import ValidationFailed
from ..util import decode_data

from flask import Blueprint, request
from flask import current_app as app

# Import types
from typing import Any

bp = Blueprint("d3_json", __name__)
bp.before_request(util.require_db)


def validate_d3_json(data):
    """Perform any necessary d3 json validation, and return appropriate errors."""
    data_errors = []

    # Check the structure of the uploaded file is what we expect
    if "nodes" not in data.keys() or "links" not in data.keys():
        data_errors.append({"error": "structure"})

    # Check that links are in source -> target form
    if not all(
        "source" in row.keys() and "target" in row.keys() for row in data["links"]
    ):
        data_errors.append({"error": "invalid_link_keys"})

    # Check that the keys for each dictionary match
    if not all(data["links"][0].keys() == row.keys() for row in data["links"]):
        data_errors.append({"error": "inconsistent_link_keys"})

    # Check for duplicated nodes
    ids = [row["id"] for row in data["nodes"]]
    if len(ids) != len(set(ids)):
        data_errors.append({"error": "node_duplicates"})

    # Duplicated edges are okay, they might encode different relationships, but
    # that should be specified in the attributes. Thus duplicated dicts are not okay
    if len(data["links"]) != len(set([tuple(x.items()) for x in data["links"]])):
        data_errors.append({"error": "link_duplicates"})

    if len(data_errors) > 0:
        raise ValidationFailed(data_errors)


@bp.route("/<workspace>/<table>", methods=["POST"])
def upload(workspace: str, table: str) -> Any:
    """Store a d3-esque json file into the database as a node and edge table.

    `workspace` - the target workspace
    `table` - the target table
    `data` - the json data, passed in the request body. The json data should contain
    nodes: [] and links: []
    """
    app.logger.info("Bulk Loading D3 Json Data")

    # Get data from the request and load it as json
    body = decode_data(request.data)
    data = json.load(StringIO(body))

    # Check file structure
    validate_d3_json(data)

    # Extract each table to pandas dataframes and change column names
    nodes = pd.DataFrame(data["nodes"])
    nodes["_key"] = nodes["id"]
    del nodes["id"]

    links = pd.DataFrame(data["links"])
    links["_from"] = links["source"].apply(lambda x: table + "_nodes/" + x)
    links["_to"] = links["target"].apply(lambda x: table + "_nodes/" + x)
    del links["source"]
    del links["target"]

    # Convert the dataframes to lists of OrderedDicts
    nodes = nodes.to_dict(orient="records", into=OrderedDict)
    links = links.to_dict(orient="records", into=OrderedDict)

    # Create the workspace
    space = db.db(workspace)
    if space.has_collection(table + "_nodes") or space.has_collection(table + "_links"):
        nodes_coll = space.collection(table + "_nodes")
        links_coll = space.collection(table + "_links")
    else:
        nodes_coll = space.create_collection(table + "_nodes", edge=False)
        links_coll = space.create_collection(table + "_links", edge=True)

    # Insert data
    nodes_coll.insert_many(nodes)
    links_coll.insert_many(links)

    return dict(count=len(nodes) + len(links))
