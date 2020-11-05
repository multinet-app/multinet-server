"""Multinet uploader for nested JSON files."""
import json
from io import StringIO
from flasgger import swag_from
from collections import OrderedDict

from multinet import util
from multinet.db.models.workspace import Workspace
from multinet.auth.util import require_writer
from multinet.errors import ValidationFailed, AlreadyExists
from multinet.util import decode_data
from multinet.validation import ValidationFailure

from flask import Blueprint, request

# Import types
from typing import Any, List, Dict, Sequence

bp = Blueprint("d3_json", __name__)
bp.before_request(util.require_db)


class InvalidStructure(ValidationFailure):
    """Invalid structure in a D3 JSON file."""


class InvalidLinkKeys(ValidationFailure):
    """Invalid link keys in a D3 JSON file."""


class InconsistentLinkKeys(ValidationFailure):
    """Inconsistent link keys in a D3 JSON file."""


class NodeDuplicates(ValidationFailure):
    """Duplicate nodes in a D3 JSON file."""


def validate_d3_json(data: Dict) -> Sequence[ValidationFailure]:
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
    loaded_workspace = Workspace(workspace)
    if loaded_workspace.has_graph(graph):
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

    # Create or retrieve the node and edge tables
    if loaded_workspace.has_table(node_table_name):
        node_table = loaded_workspace.table(node_table_name)
    else:
        node_table = loaded_workspace.create_table(node_table_name, edge=False)

    if loaded_workspace.has_table(edge_table_name):
        edge_table = loaded_workspace.table(edge_table_name)
    else:
        edge_table = loaded_workspace.create_table(edge_table_name, edge=True)

    # Insert data
    node_table.insert(nodes)
    edge_table.insert(links)

    loaded_workspace.create_graph(graph, edge_table_name)

    return {"nodecount": len(nodes), "edgecount": len(links)}
