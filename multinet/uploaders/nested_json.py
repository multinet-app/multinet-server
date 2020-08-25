"""Multinet uploader for nested JSON files."""
from flasgger import swag_from
import itertools
import json

from multinet import util
from multinet.workspace import Workspace
from multinet.auth.util import require_writer
from multinet.errors import AlreadyExists

from flask import Blueprint, request

from typing import Tuple, List, Any

bp = Blueprint("nested_json", __name__)
bp.before_request(util.require_db)


def analyze_nested_json(
    raw_data: str, int_table_name: str, leaf_table_name: str
) -> Tuple[List[List[dict]], List[dict]]:
    """
    Transform nested JSON data into MultiNet format.

    `data` - the text of a nested_json file
    `(nodes, edges)` - a node and edge table describing the tree.
    """
    ident = itertools.count(100)
    data = json.loads(raw_data)

    def keyed(rec: dict) -> dict:
        if "_key" in rec:
            return rec

        rec["_key"] = str(next(ident))

        return rec

    # The helper function will collect nodes and edges into these two lists.
    nodes: List[List[dict]] = [[], []]
    edges = []

    def helper(tree: dict) -> None:
        # Grab the root node of the subtree, and the child nodes.
        root = keyed(tree.get("node_data", {}))
        children = tree.get("children", [])

        # Capture the root node into one of two tables.
        if children:
            nodes[0].append(root)
        else:
            nodes[1].append(root)

        # Capture edges for each child.
        for child in children:
            # Grab the child data.
            child_data = keyed(child.get("node_data", {}))

            # Determine which table the child is in.
            child_table_name = (
                int_table_name if child.get("children") else leaf_table_name
            )

            # Record the edge record.
            edge = dict(child.get("edge_data", {}))
            edge["_from"] = f'{child_table_name}/{child_data["_key"]}'
            edge["_to"] = f'{int_table_name}/{root["_key"]}'
            edges.append(edge)

        # Recursively add the child subtrees.
        for child in children:
            helper(child)

    # Kick off the analysis.
    helper(data)
    return (nodes, edges)


@bp.route("/<workspace>/<graph>", methods=["POST"])
@require_writer
@swag_from("swagger/nested_json.yaml")
def upload(workspace: str, graph: str) -> Any:
    """
    Store a nested_json tree into the database in coordinated node and edge tables.

    `workspace` - the target workspace.
    `graph` - the target graph.
    `data` - the nested_json data, passed in the request body.
    """
    loaded_workspace = Workspace(workspace)
    if loaded_workspace.has_graph(graph):
        raise AlreadyExists("graph", graph)

    # Set up the parameters.
    data = request.data.decode("utf8")

    edgetable_name = f"{graph}_edges"
    int_nodetable_name = f"{graph}_internal_nodes"
    leaf_nodetable_name = f"{graph}_leaf_nodes"

    # Set up the database targets.
    if loaded_workspace.has_table(edgetable_name):
        edgetable = loaded_workspace.table(edgetable_name)
    else:
        edgetable = loaded_workspace.create_table(edgetable_name, edge=True)

    if loaded_workspace.has_table(int_nodetable_name):
        int_nodetable = loaded_workspace.table(int_nodetable_name)
    else:
        int_nodetable = loaded_workspace.create_table(int_nodetable_name, edge=False)

    if loaded_workspace.has_table(leaf_nodetable_name):
        leaf_nodetable = loaded_workspace.table(leaf_nodetable_name)
    else:
        leaf_nodetable = loaded_workspace.create_table(leaf_nodetable_name, edge=False)

    # Analyze the nested_json data into a node and edge table.
    (nodes, edges) = analyze_nested_json(data, int_nodetable_name, leaf_nodetable_name)

    # Upload the data to the database.
    edgetable.insert(edges)
    int_nodetable.insert(nodes[0])
    leaf_nodetable.insert(nodes[1])

    # Create graph
    loaded_workspace.create_graph(graph, edgetable_name)

    return {
        "edgecount": len(edges),
        "int_nodecount": len(nodes[0]),
        "leaf_nodecount": len(nodes[1]),
    }
