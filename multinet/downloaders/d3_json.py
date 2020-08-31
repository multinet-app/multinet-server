"""Multinet downloader for nested JSON files."""
import re
import json

from flasgger import swag_from

from multinet.db.models.workspace import Workspace
from multinet.db.models.graph import Graph
from multinet.util import require_db
from multinet.errors import GraphNotFound

from flask import Blueprint, Response

# Import types
from typing import Any, Generator, List

bp = Blueprint("download_d3_json", __name__)
bp.before_request(require_db)


def node_generator(
    loaded_workspace: Workspace, loaded_graph: Graph
) -> Generator[str, None, None]:
    """Generate the JSON list of nodes."""

    comma = ""
    node_tables = loaded_graph.node_tables()
    for node_table in node_tables:
        table_nodes = loaded_workspace.table(node_table).rows()["rows"]

        for node in table_nodes:
            node["id"] = node["_key"]
            del node["_key"]

            yield f"{comma}{json.dumps(node, separators=(',', ':'))}"
            comma = comma or ","


def link_generator(
    loaded_workspace: Workspace, loaded_graph: Graph
) -> Generator[str, None, None]:
    """Generate the JSON list of links."""

    # Checks for node tables that have a `_nodes` suffix.
    # If matched, removes this suffix.
    table_nodes_pattern = re.compile(r"^([^\d_]\w+)_nodes(/.+)")

    # Done this way to preserve logic in the future case of multiple edge tables
    edge_tables: List[str] = [loaded_graph.edge_table()]

    comma = ""
    for edge_table in edge_tables:
        edges = loaded_workspace.table(edge_table).rows()["rows"]

        for edge in edges:
            source = edge["_from"]
            target = edge["_to"]
            source_match = table_nodes_pattern.search(source)
            target_match = table_nodes_pattern.search(target)

            if source_match and target_match:
                source = "".join(source_match.groups())
                target = "".join(target_match.groups())

            edge["source"] = source
            edge["target"] = target
            del edge["_from"]
            del edge["_to"]

            yield f"{comma}{json.dumps(edge, separators=(',', ':'))}"
            comma = comma or ","


@bp.route("/workspaces/<workspace>/graphs/<graph>/download", methods=["GET"])
@swag_from("swagger/d3_json.yaml")
def download(workspace: str, graph: str) -> Any:
    """Return a graph as a d3 json-encoded graph.

    `workspace` - the target workspace
    `graph` - the target graph
    """

    loaded_workspace = Workspace(workspace)
    if not loaded_workspace.has_graph(graph):
        raise GraphNotFound(workspace, graph)

    loaded_graph = loaded_workspace.graph(graph)

    def d3_json_generator() -> Generator[str, None, None]:
        yield """{"nodes":["""
        yield from node_generator(loaded_workspace, loaded_graph)
        yield """],"links":["""
        yield from link_generator(loaded_workspace, loaded_graph)
        yield "]}"

    response = Response(d3_json_generator(), mimetype="application/json")
    response.headers["Content-Disposition"] = f"attachment; filename={graph}.json"
    response.headers["Content-type"] = "application/json"

    return response
