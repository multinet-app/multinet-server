"""Multinet downloader for nested JSON files."""
import re

from flasgger import swag_from

from multinet.util import require_db, generate_filtered_docs
from multinet.db import get_workspace_db
from multinet.errors import GraphNotFound

from flask import Blueprint, make_response

# Import types
from typing import Any

bp = Blueprint("download_d3_json", __name__)
bp.before_request(require_db)


@bp.route("/<workspace>/<graph>", methods=["GET"])
@swag_from("swagger/d3_json.yaml")
def download(workspace: str, graph: str) -> Any:
    """Return a graph as a d3 json-encoded graph.

    `workspace` - the target workspace
    `graph` - the target graph
    """

    nodes = []
    links = []

    space = get_workspace_db(workspace)
    if not space.has_graph(graph):
        raise GraphNotFound(workspace, graph)

    loaded_graph = space.graph(graph)

    node_tables = loaded_graph.vertex_collections()
    for node_table in node_tables:
        table_nodes = loaded_graph.vertex_collection(node_table).all()

        for node in table_nodes:
            node["id"] = node["_key"]
            del node["_key"]
            nodes.append(node)

    pattern = re.compile(r"^([^\d_]\w+)_nodes(/.+)")
    edge_tables = [edef["edge_collection"] for edef in loaded_graph.edge_definitions()]
    for edge_table in edge_tables:
        edges = loaded_graph.edge_collection(edge_table).all()

        for edge in edges:
            source = edge["_from"]
            target = edge["_to"]
            source_match = pattern.search(source)
            target_match = pattern.search(target)

            if source_match and target_match:
                source = "".join(source_match.groups())
                target = "".join(target_match.groups())

            edge["source"] = source
            edge["target"] = target
            del edge["_from"]
            del edge["_to"]

            links.append(edge)

    response = make_response(
        dict(
            nodes=list(generate_filtered_docs(nodes)),
            links=list(generate_filtered_docs(links)),
        )
    )
    response.headers["Content-Disposition"] = f"attachment; filename={graph}.json"
    response.headers["Content-type"] = "application/json"

    return response
