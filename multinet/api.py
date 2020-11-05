"""Flask blueprint for Multinet REST API."""
from flasgger import swag_from
from flask import Blueprint, request
from webargs import fields
from webargs.flaskparser import use_kwargs

from typing import Any, Optional
from multinet.types import EdgeDirection, UnionTableType
from multinet.auth.util import (
    require_login,
    require_reader,
    require_writer,
    require_maintainer,
    require_owner,
    current_user,
)

from multinet import util
from multinet.errors import (
    BadQueryArgument,
    MalformedRequestBody,
    AlreadyExists,
    RequiredParamsMissing,
)

from multinet.db.models.workspace import Workspace

bp = Blueprint("multinet", __name__)


@bp.route("/workspaces", methods=["GET"])
@swag_from("swagger/workspaces.yaml")
def get_workspaces() -> Any:
    """Return the list of available workspaces, based on the logged in user."""
    user = current_user()

    # If the user is logged in, return all workspaces visible to them
    if user is not None:
        return util.stream(user.available_workspaces())

    # Otherwise, return only public workspaces
    return util.stream(Workspace.list_public())


@bp.route("/workspaces/<workspace>/permissions", methods=["GET"])
@require_maintainer
@swag_from("swagger/get_workspace_permissions.yaml")
def get_workspace_permissions(workspace: str) -> Any:
    """Retrieve the permissions of a workspace."""
    perms = Workspace(workspace).permissions
    return util.expand_user_permissions(perms)


@bp.route("/workspaces/<workspace>/permissions", methods=["PUT"])
@require_maintainer
@swag_from("swagger/set_workspace_permissions.yaml")
def set_workspace_permissions(workspace: str) -> Any:
    """Set the permissions on a workspace."""
    if set(request.json.keys()) != {
        "owner",
        "maintainers",
        "writers",
        "readers",
        "public",
    }:
        raise MalformedRequestBody(request.json)

    perms = util.contract_user_permissions(request.json)
    return Workspace(workspace).set_permissions(perms).__dict__


@bp.route("/workspaces/<workspace>/tables", methods=["GET"])
@require_reader
@use_kwargs({"type": fields.Str()})
@swag_from("swagger/workspace_tables.yaml")
def get_workspace_tables(
    workspace: str, type: UnionTableType = "all"  # noqa: A002
) -> Any:
    """Retrieve the tables of a single workspace."""
    tables = Workspace(workspace).tables(type)
    return util.stream(tables)


@bp.route("/workspaces/<workspace>/tables", methods=["POST"])
@require_writer
@use_kwargs({"table": fields.Str()})
@swag_from("swagger/workspace_aql_tables.yaml")
def create_aql_table(workspace: str, table: str) -> Any:
    """Create a table from an AQL query."""
    aql = request.data.decode()
    Workspace(workspace).create_aql_table(table, aql)

    return table


@bp.route("/workspaces/<workspace>/tables/<table>", methods=["GET"])
@require_reader
@use_kwargs({"offset": fields.Int(), "limit": fields.Int()})
@swag_from("swagger/table_rows.yaml")
def get_table_rows(workspace: str, table: str, offset: int = 0, limit: int = 30) -> Any:
    """Retrieve the rows and headers of a table."""
    return Workspace(workspace).table(table).rows(offset, limit)


@bp.route("/workspaces/<workspace>/tables/<table>/metadata", methods=["GET"])
@require_reader
@swag_from("swagger/get_metadata.yaml")
def get_table_metadata(workspace: str, table: str) -> Any:
    """Retrieve the metadata of a table, if it exists."""
    metadata = Workspace(workspace).table(table).get_metadata()
    return "" if metadata is None else metadata.dict()


@bp.route("/workspaces/<workspace>/tables/<table>/metadata", methods=["PUT"])
@require_reader
@swag_from("swagger/set_metadata.yaml")
def set_table_metadata(workspace: str, table: str) -> Any:
    """Retrieve the rows and headers of a table."""
    return Workspace(workspace).table(table).set_metadata(request.json).dict()


@bp.route("/workspaces/<workspace>/graphs", methods=["GET"])
@require_reader
@swag_from("swagger/workspace_graphs.yaml")
def get_workspace_graphs(workspace: str) -> Any:
    """Retrieve the graphs of a single workspace."""
    return util.stream((g["name"] for g in Workspace(workspace).graphs()))


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["GET"])
@require_reader
@swag_from("swagger/workspace_graph.yaml")
def get_workspace_graph(workspace: str, graph: str) -> Any:
    """Retrieve information about a graph."""
    node_tables = Workspace(workspace).graph(graph).node_tables()
    edge_table = Workspace(workspace).graph(graph).edge_table()
    return {"edgeTable": edge_table, "nodeTables": node_tables}


@bp.route("/workspaces/<workspace>/graphs/<graph>/nodes", methods=["GET"])
@require_reader
@use_kwargs({"offset": fields.Int(), "limit": fields.Int()})
@swag_from("swagger/graph_nodes.yaml")
def get_graph_nodes(
    workspace: str, graph: str, offset: int = 0, limit: int = 30
) -> Any:
    """Retrieve the nodes of a graph."""
    return Workspace(workspace).graph(graph).nodes(offset, limit)


@bp.route(
    "/workspaces/<workspace>/graphs/<graph>/nodes/<table>/<node>/attributes",
    methods=["GET"],
)
@require_reader
@swag_from("swagger/node_data.yaml")
def get_node_data(workspace: str, graph: str, table: str, node: str) -> Any:
    """Return the attributes associated with a node."""
    return Workspace(workspace).graph(graph).node_attributes(table, node)


@bp.route(
    "/workspaces/<workspace>/graphs/<graph>/nodes/<table>/<node>/edges", methods=["GET"]
)
@require_reader
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

    return (
        Workspace(workspace)
        .graph(graph)
        .node_edges(table, node, direction, offset, limit)
    )


@bp.route("/workspaces/<workspace>", methods=["POST"])
@require_login
@swag_from("swagger/create_workspace.yaml")
def create_workspace(workspace: str) -> Any:
    """Create a new workspace."""
    # The `require_login()` decorator ensures that a user is logged in
    user = current_user()
    assert user is not None

    Workspace.create(workspace, user)
    return workspace


@bp.route("/workspaces/<workspace>/aql", methods=["POST"])
@require_reader
@swag_from("swagger/aql.yaml")
def aql(workspace: str) -> Any:
    """Perform an AQL query in the given workspace."""
    query = request.data.decode("utf8")
    if not query:
        raise MalformedRequestBody(query)

    result = Workspace(workspace).run_query(query)
    return util.stream(result)


@bp.route("/workspaces/<workspace>", methods=["DELETE"])
@require_owner
@swag_from("swagger/delete_workspace.yaml")
def delete_workspace(workspace: str) -> Any:
    """Delete a workspace."""
    Workspace(workspace).delete()
    return workspace


@bp.route("/workspaces/<workspace>/name", methods=["PUT"])
@use_kwargs({"name": fields.Str()})
@require_maintainer
@swag_from("swagger/rename_workspace.yaml")
def rename_workspace(workspace: str, name: str) -> Any:
    """Delete a workspace."""
    Workspace(workspace).rename(name)
    return name


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["POST"])
@use_kwargs({"edge_table": fields.Str()})
@require_writer
@swag_from("swagger/create_graph.yaml")
def create_graph(workspace: str, graph: str, edge_table: Optional[str] = None) -> Any:
    """Create a graph."""
    if not edge_table:
        raise RequiredParamsMissing(["edge_table"])

    loaded_workspace = Workspace(workspace)
    if loaded_workspace.has_graph(graph):
        raise AlreadyExists("Graph", graph)

    Workspace(workspace).create_graph(graph, edge_table)
    return graph


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["DELETE"])
@require_writer
@swag_from("swagger/delete_graph.yaml")
def delete_graph(workspace: str, graph: str) -> Any:
    """Delete a graph."""
    Workspace(workspace).delete_graph(graph)
    return graph


@bp.route("/workspaces/<workspace>/tables/<table>", methods=["DELETE"])
@require_writer
@swag_from("swagger/delete_table.yaml")
def delete_table(workspace: str, table: str) -> Any:
    """Delete a table."""
    Workspace(workspace).delete_table(table)
    return table
