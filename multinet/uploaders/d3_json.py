"""Multinet uploader for nested JSON files."""
import json
from io import StringIO
from flasgger import swag_from
from dataclasses import dataclass
from collections import OrderedDict

from multinet import db, util
from multinet.auth.util import require_writer
from multinet.errors import ValidationFailed, AlreadyExists
from multinet.util import decode_data
from multinet.validation import ValidationFailure

from flask import Blueprint, request

# Import types
from typing import Any, List, Sequence

bp = Blueprint("d3_json", __name__)
bp.before_request(util.require_db)


@dataclass
class InvalidStructure(ValidationFailure):
    """Invalid structure in a D3 JSON file."""


@dataclass
class InvalidLinkKeys(ValidationFailure):
    """Invalid link keys in a D3 JSON file."""


@dataclass
class InconsistentLinkKeys(ValidationFailure):
    """Inconsistent link keys in a D3 JSON file."""


@dataclass
class NodeDuplicates(ValidationFailure):
    """Duplicate nodes in a D3 JSON file."""


def validate_d3_json(data: dict) -> Sequence[ValidationFailure]:
    """Perform any necessary d3 json validation, and return appropriate errors."""
    data_errors: List[ValidationFailure] = []

    # Check the structure of the uploaded file is what we expect
    if "nodes" not in data.keys() or "links" not in data.keys():
        data_errors.append(InvalidStructure())

    # Check that links are in source -> target form
    if not all(
        "source" in row.keys() and "target" in row.keys() for row in data["links"]
    ):
        data_errors.append(InvalidLinkKeys())

    # Check that the keys for each dictionary match
    if not all(data["links"][0].keys() == row.keys() for row in data["links"]):
        data_errors.append(InconsistentLinkKeys())

    # Check for duplicated nodes
    ids = {row["id"] for row in data["nodes"]}
    if len(data["nodes"]) != len(ids):
        data_errors.append(NodeDuplicates())

    return data_errors


@bp.route("/<workspace>/<graph>", methods=["POST"])
@require_writer
@swag_from("swagger/d3_json.yaml")
def upload(workspace: str, graph: str) -> Any:
    """Store a d3 json-encoded graph into the database, with node and edge tables.

    `workspace` - the target workspace
    `graph` - the target graph
    `data` - the json data, passed in the request body. The json data should contain
    nodes: [] and links: []
    """
    space = db.get_workspace_db(workspace, readonly=False)
    if space.has_graph(graph):
        raise AlreadyExists("graph", graph)

    # Get data from the request and load it as json
    body = decode_data(request.data)
    data = json.load(StringIO(body), object_pairs_hook=OrderedDict)

    # Check file structure
    errors = validate_d3_json(data)
    if len(errors) > 0:
        raise ValidationFailed(errors)

    node_table_name = f"{graph}_nodes"
    edge_table_name = f"{graph}_links"

    # Change column names from the d3 format to the arango format
    nodes = data["nodes"]
    for node in nodes:
        node["_key"] = str(node["id"])
        del node["id"]

    links = data["links"]
    for link in links:
        link["_from"] = f"{node_table_name}/{link['source']}"
        link["_to"] = f"{node_table_name}/{link['target']}"
        del link["source"]
        del link["target"]

    # Create or retrieve the workspace
    if space.has_collection(node_table_name):
        nodes_coll = space.collection(node_table_name)
    else:
        nodes_coll = space.create_collection(node_table_name, edge=False)

    if space.has_collection(edge_table_name):
        links_coll = space.collection(edge_table_name)
    else:
        links_coll = space.create_collection(edge_table_name, edge=True)

    # Insert data
    nodes_coll.insert_many(nodes, sync=True)
    links_coll.insert_many(links, sync=True)

    properties = util.get_edge_table_properties(workspace, edge_table_name)

    db.create_graph(
        workspace,
        graph,
        edge_table_name,
        properties["from_tables"],
        properties["to_tables"],
    )

    return {"nodecount": len(nodes), "edgecount": len(links)}
