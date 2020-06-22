"""Flask blueprint for Multinet REST API."""
from flasgger import swag_from
from flask import Blueprint, request
from webargs import fields
from webargs.flaskparser import use_kwargs

from typing import Any, Optional, List
from multinet.types import EdgeDirection, TableType, Workspace
from multinet.auth.types import UserInfo
from multinet.auth.util import require_login, is_reader
from multinet.validation import ValidationFailure, UndefinedKeys, UndefinedTable

from multinet import db, util
from multinet.errors import (
    ValidationFailed,
    BadQueryArgument,
    MalformedRequestBody,
    AlreadyExists,
    RequiredParamsMissing,
)
from multinet.user import current_user

bp = Blueprint("multinet", __name__)


@bp.route("/workspaces", methods=["GET"])
@swag_from("swagger/workspaces.yaml")
def get_workspaces() -> Any:
    """Retrieve list of workspaces."""
    user = current_user()

    # Filter all workspaces based on whether it should be shown to the user who
    # is logged in.
    stream = util.stream(w["name"] for w in db.get_workspaces() if is_reader(user, w))
    return stream


@bp.route("/workspaces/<workspace>", methods=["GET"])
@swag_from("swagger/workspace.yaml")
def get_workspace(workspace: str) -> Any:
    """Retrieve a single workspace."""
    return db.get_workspace(workspace)


@bp.route("/workspaces/<workspace>/tables", methods=["GET"])
@use_kwargs({"type": fields.Str()})
@swag_from("swagger/workspace_tables.yaml")
def get_workspace_tables(workspace: str, type: TableType = "all") -> Any:  # noqa: A002
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
@require_login
def create_workspace(workspace: str) -> Any:
    """Create a new workspace."""

    # The `require_login()` decorator ensures that a user is logged in by this
    # point.
    user = current_user()
    assert user is not None

    # Perform the actual backend update to create a new workspace owned by the
    # logged in user.
    return db.create_workspace(workspace, user)


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


@bp.route("/workspaces/<workspace>/name", methods=["PUT"])
@use_kwargs({"name": fields.Str()})
@swag_from("swagger/rename_workspace.yaml")
def rename_workspace(workspace: str, name: str) -> Any:
    """Delete a workspace."""
    db.rename_workspace(workspace, name)
    return name


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["POST"])
@use_kwargs({"edge_table": fields.Str()})
@swag_from("swagger/create_graph.yaml")
def create_graph(workspace: str, graph: str, edge_table: Optional[str] = None) -> Any:
    """Create a graph."""

    if not edge_table:
        raise RequiredParamsMissing(["edge_table"])

    loaded_workspace = db.get_workspace_db(workspace)
    if loaded_workspace.has_graph(graph):
        raise AlreadyExists("Graph", graph)

    # Get reference tables with respective referenced keys,
    # tables in the _from column and tables in the _to column
    edge_table_properties = util.get_edge_table_properties(workspace, edge_table)
    referenced_tables = edge_table_properties["table_keys"]
    from_tables = edge_table_properties["from_tables"]
    to_tables = edge_table_properties["to_tables"]

    errors: List[ValidationFailure] = []
    for table, keys in referenced_tables.items():
        if not loaded_workspace.has_collection(table):
            errors.append(UndefinedTable(table=table))
        else:
            table_keys = set(loaded_workspace.collection(table).keys())
            undefined = keys - table_keys

            if undefined:
                errors.append(UndefinedKeys(table=table, keys=list(undefined)))

    if errors:
        raise ValidationFailed(errors)

    db.create_graph(workspace, graph, edge_table, from_tables, to_tables)
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
