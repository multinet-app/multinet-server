"""Flask blueprint for Multinet REST API."""
import json

from flask import Blueprint, request, Response
from webargs import fields
from webargs.flaskparser import use_kwargs

from . import db
from .errors import ValidationFailed

bp = Blueprint("multinet", __name__)


def generate(iterator):
    """Return a generator that yields an iterator's contents into a JSON list."""
    yield "["

    comma = ""
    for row in iterator:
        yield f"{comma}{json.dumps(row)}"
        comma = ","

    yield "]"


def stream(iterator):
    """Convert an iterator to a Flask response."""
    return Response(generate(iterator), mimetype="application/json")


def require_db():
    """Check if the db is live."""
    if not db.check_db():
        return ("", "500 Database Not Live")


bp.before_request(require_db)


@bp.route("/workspaces", methods=["GET"])
def get_workspaces():
    """Retrieve list of workspaces."""
    return stream(db.get_workspaces())


@bp.route("/workspaces/<workspace>", methods=["GET"])
def get_workspace(workspace):
    """Retrieve a single workspace."""
    return db.get_workspace(workspace)


@bp.route("/workspaces/<workspace>/tables", methods=["GET"])
@use_kwargs({"type": fields.Str()})
def get_workspace_tables(workspace, type="all"):
    """Retrieve the tables of a single workspace."""
    tables = db.workspace_tables(workspace, type)
    return stream(tables)


@bp.route("/workspaces/<workspace>/tables/<table>", methods=["GET"])
@use_kwargs({"offset": fields.Int(), "limit": fields.Int()})
def get_table_rows(workspace, table, offset=0, limit=30):
    """Retrieve the rows and headers of a table."""
    rows = db.workspace_table(workspace, table, offset, limit)
    return stream(rows)


@bp.route("/workspaces/<workspace>/graphs", methods=["GET"])
def get_workspace_graphs(workspace):
    """Retrieve the graphs of a single workspace."""
    graphs = db.workspace_graphs(workspace)
    return stream(graphs)


@bp.route("/workspaces/<workspace>/graphs/<graph>", methods=["GET"])
def get_workspace_graph(workspace, graph):
    """Retrieve information about a graph."""
    return db.workspace_graph(workspace, graph)


@bp.route("/workspaces/<workspace>/graphs/<graph>/nodes", methods=["GET"])
@use_kwargs({"offset": fields.Int(), "limit": fields.Int()})
def get_graph_nodes(workspace, graph, offset=0, limit=30):
    """Retrieve the nodes of a graph."""
    return db.graph_nodes(workspace, graph, offset, limit)


@bp.route(
    "/workspaces/<workspace>/graphs/<graph>/nodes/<table>/<node>/attributes", methods=["GET"]
)
def get_node_data(workspace, graph, table, node):
    """Return the attributes associated with a node."""
    return db.graph_node(workspace, graph, table, node)


@bp.route(
    "/workspaces/<workspace>/graphs/<graph>/nodes/<table>/<node>/edges", methods=["GET"]
)
@use_kwargs({"direction": fields.Str(), "offset": fields.Int(), "limit": fields.Int()})
def get_graph_node(workspace, graph, table, node, direction="all", offset=0, limit=30):
    """Return the edges connected to a node."""
    if direction not in ["incoming", "outgoing", "all"]:
        return (direction, "400 Invalid Direction Parameter")

    return db.node_edges(workspace, graph, table, node, offset, limit, direction)


@bp.route("/workspaces/<workspace>", methods=["POST"])
def create_workspace(workspace):
    """Create a new workspace."""
    db.create_workspace(workspace)
    return workspace


@bp.route("/workspaces/<workspace>/aql", methods=["POST"])
def aql(workspace):
    """Perform an AQL query in the given workspace."""
    query = request.data.decode("utf8")
    if not query:
        return (query, "400 Malformed Request Body")

    result = db.aql_query(workspace, query)
    return stream(result)


@bp.route("/workspaces/<workspace>", methods=["DELETE"])
def delete_workspace(workspace):
    """Delete a workspace."""
    db.delete_workspace(workspace)
    return workspace


@bp.route("/workspaces/<workspace>/graph/<graph>", methods=["POST"])
@use_kwargs({"node_tables": fields.List(fields.Str()), "edge_table": fields.Str()})
def create_graph(workspace, graph, node_tables=None, edge_table=None):
    """Create a graph."""

    if not node_tables or not edge_table:
        body = request.data.decode("utf8")
        return (body, "400 Malformed Request Body")

    missing = [arg for arg in [node_tables, edge_table] if arg is None]
    if missing:
        return (missing, "400 Missing Required Parameters")

    loadedWorkspace = db.db(workspace)
    if loadedWorkspace.has_graph(graph):
        return (graph, "409 Graph Already Exists")

    existing_tables = set([x["name"] for x in loadedWorkspace.collections()])
    edges = loadedWorkspace.collection(edge_table).all()

    # Iterate through each edge and check for undefined tables
    errors = []
    valid_tables = dict()
    invalid_tables = set()
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
        for table in invalid_tables:
            errors.append(f"Reference to undefined table: {table}")

    # Iterate through each node table and check for nonexistent keys
    for table in valid_tables:
        existing_keys = set(
            [x["_key"] for x in loadedWorkspace.collection(table).all()]
        )
        nonexistent_keys = valid_tables[table] - existing_keys

        if len(nonexistent_keys) > 0:
            errors.append(
                f"Nonexistent keys {', '.join(nonexistent_keys)} "
                f"referenced in table: {table}"
            )

    # TODO: Update this with the proper JSON schema
    if errors:
        raise ValidationFailed(errors)

    db.create_graph(workspace, graph, node_tables, edge_table)
    return graph
