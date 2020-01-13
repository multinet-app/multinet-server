"""Flask blueprint for Multinet REST API."""
from flasgger import swag_from
from flask import Blueprint, request
from webargs import fields
from webargs.flaskparser import use_kwargs

from typing import Any, Optional, List, Dict, Set
from .types import EdgeDirection, TableType, ValidatonFailedError

from . import db, util
from .errors import (
    ValidationFailed,
    BadQueryArgument,
    MalformedRequestBody,
    AlreadyExists,
    RequiredParamsMissing,
)

bp = Blueprint("multinet", __name__)
bp.before_request(util.require_db)


@bp.route("/workspaces", methods=["GET"])
@swag_from("swagger/workspaces.yaml")
def get_workspaces() -> Any:
    """Retrieve list of workspaces."""
    return util.stream(db.get_workspaces())


@bp.route("/workspaces/<workspace>", methods=["GET"])
@swag_from("swagger/workspace.yaml")
def get_workspace(workspace: str) -> Any:
    """Retrieve a single workspace."""
    return db.get_workspace(workspace)


@bp.route("/workspaces/<workspace>/tables", methods=["GET"])
@use_kwargs({"type": fields.Str()})
@swag_from("swagger/workspace_tables.yaml")
def get_workspace_tables(workspace: str, type: TableType = "all") -> Any:
    """Retrieve the tables of a single workspace."""
    tables = db.workspace_tables(workspace, type)
    return util.stream(tables)


@bp.route("/workspaces/<workspace>/tables/<table>", methods=["GET"])
@use_kwargs({"offset": fields.Int(), "limit": fields.Int()})
@swag_from("swagger/table_rows.yaml")
def get_table_rows(workspace: str, table: str, offset: int = 0, limit: int = 30) -> Any:
    """Retrieve the rows and headers of a table."""
    return db.workspace_table(workspace, table, offset, limit)


@bp.route("/workspaces/<workspace>/graphs", methods=["GET"])
@swag_from("swagger/workspace_graphs.yaml")
def get_workspace_graphs(workspace: str) -> Any:
    """Retrieve the graphs of a single workspace."""
    graphs = db.workspace_graphs(workspace)
    return util.stream(graphs)


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["GET"])
@swag_from("swagger/workspace_graph.yaml")
def get_workspace_graph(workspace: str, graph: str) -> Any:
    """Retrieve information about a graph."""
    return db.workspace_graph(workspace, graph)


@bp.route("/workspaces/<workspace>/graphs/<graph>/nodes", methods=["GET"])
@use_kwargs({"offset": fields.Int(), "limit": fields.Int()})
@swag_from("swagger/graph_nodes.yaml")
def get_graph_nodes(
    workspace: str, graph: str, offset: int = 0, limit: int = 30
) -> Any:
    """Retrieve the nodes of a graph."""
    return db.graph_nodes(workspace, graph, offset, limit)


@bp.route(
    "/workspaces/<workspace>/graphs/<graph>/nodes/<table>/<node>/attributes",
    methods=["GET"],
)
@swag_from("swagger/node_data.yaml")
def get_node_data(workspace: str, graph: str, table: str, node: str) -> Any:
    """Return the attributes associated with a node."""
    return db.graph_node(workspace, graph, table, node)


@bp.route(
    "/workspaces/<workspace>/graphs/<graph>/nodes/<table>/<node>/edges", methods=["GET"]
)
@use_kwargs({"direction": fields.Str(), "offset": fields.Int(), "limit": fields.Int()})
@swag_from("swagger/node_edges.yaml")
def get_node_edges(
    workspace: str,
    graph: str,
    table: str,
    node: str,
    direction: EdgeDirection = "all",
    offset: int = 0,
    limit: int = 30,
) -> Any:
    """Return the edges connected to a node."""
    allowed = ["incoming", "outgoing", "all"]
    if direction not in allowed:
        raise BadQueryArgument("direction", direction, allowed)

    return db.node_edges(workspace, graph, table, node, offset, limit, direction)


@bp.route("/workspaces/<workspace>", methods=["POST"])
@swag_from("swagger/create_workspace.yaml")
def create_workspace(workspace: str) -> Any:
    """Create a new workspace."""
    db.create_workspace(workspace)
    return workspace


@bp.route("/workspaces/<workspace>/aql", methods=["POST"])
@swag_from("swagger/aql.yaml")
def aql(workspace: str) -> Any:
    """Perform an AQL query in the given workspace."""
    query = request.data.decode("utf8")
    if not query:
        raise MalformedRequestBody(query)

    result = db.aql_query(workspace, query)
    return util.stream(result)


@bp.route("/workspaces/<workspace>", methods=["DELETE"])
@swag_from("swagger/delete_workspace.yaml")
def delete_workspace(workspace: str) -> Any:
    """Delete a workspace."""
    db.delete_workspace(workspace)
    return workspace


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["POST"])
@use_kwargs({"node_tables": fields.List(fields.Str()), "edge_table": fields.Str()})
@swag_from("swagger/create_graph.yaml")
def create_graph(
    workspace: str,
    graph: str,
    node_tables: Optional[List[str]] = None,
    edge_table: Optional[str] = None,
) -> Any:
    """Create a graph."""

    if not node_tables or not edge_table:
        body = request.data.decode("utf8")
        raise MalformedRequestBody(body)

    missing = [
        arg[0]
        for arg in [("node_tables", node_tables), ("edge_table", edge_table)]
        if arg[1] is None
    ]
    if missing:
        raise RequiredParamsMissing(missing)

    loaded_workspace = db.db(workspace)
    if loaded_workspace.has_graph(graph):
        raise AlreadyExists("Graph", graph)

    existing_tables = set([x["name"] for x in loaded_workspace.collections()])
    edges = loaded_workspace.collection(edge_table).all()

    # Iterate through each edge and check for undefined tables
    errors: List[ValidatonFailedError] = []
    valid_tables: Dict[str, Set[str]] = dict()
    invalid_tables: Set[str] = set()
    for edge in edges:
        nodes = (edge["_from"].split("/"), edge["_to"].split("/"))

        for (table, key) in nodes:
            if table not in existing_tables:
                invalid_tables.add(table)
            elif table in valid_tables:
                valid_tables[table].add(key)
            else:
                valid_tables[table] = {key}

    if invalid_tables:
        errors.append(
            {"type": "graph_creation_undefined_tables", "body": list(invalid_tables)}
        )

    # Iterate through each node table and check for nonexistent keys
    for table in valid_tables:
        existing_keys = set(
            [x["_key"] for x in loaded_workspace.collection(table).all()]
        )
        nonexistent_keys = valid_tables[table] - existing_keys

        if len(nonexistent_keys) > 0:
            errors.append(
                {
                    "type": "graph_creation_undefined_keys",
                    "body": {"table": table, "keys": list(nonexistent_keys)},
                }
            )

    if errors:
        raise ValidationFailed(errors)

    db.create_graph(workspace, graph, node_tables, edge_table)
    return graph


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["DELETE"])
@swag_from("swagger/delete_graph.yaml")
def delete_graph(workspace: str, graph: str) -> Any:
    """Delete a graph."""
    db.delete_graph(workspace, graph)
    return graph


@bp.route("/workspaces/<workspace>/tables/<table>", methods=["DELETE"])
@swag_from("swagger/delete_table.yaml")
def delete_table(workspace: str, table: str) -> Any:
    """Delete a table."""
    db.delete_table(workspace, table)
    return table
