"""Flask blueprint for Multinet REST API."""
from graphql import graphql
import json

from flask import Blueprint, request, Response
from flask import current_app as app
from webargs import fields
from webargs.flaskparser import use_kwargs

from .schema import schema
from . import db

bp = Blueprint("multinet", __name__)


def require_db():
    """Check if the db is live."""
    if not db.check_db():
        return ("", "500 Database Not Live")


bp.before_request(require_db)


def graphql_query(query, variables=None):
    """Perform a GraphQL query using optional variable definitions."""
    data = None
    errors = []

    result = graphql(schema, query, variables=variables or {})
    if result:
        errors = [error.message for error in result.errors] if result.errors else []
        data = result.data

        if errors:
            app.logger.error("Errors in request: %s" % len(errors))
            for error in errors[:10]:
                app.logger.error(error)

            excess = len(errors) - 10
            if excess > 0:
                app.logger.error(f'{excess} more error{"s" if excess > 1 else ""}')

    return dict(data=data, errors=errors, query=query)


@bp.route("/graphql", methods=["POST"])
@use_kwargs({"query": fields.Str(), "variables": fields.Dict()})
def _graphql(query=None, variables=None):
    app.logger.info("Executing GraphQL Request")
    app.logger.debug("request: %s" % query)
    app.logger.debug("variables: %s" % variables)

    if query is None:
        body = request.data.decode("utf8")
        return (body, "400 Malformed Request Body")

    result = graphql_query(query, variables)
    return result


@bp.route("/workspace/<workspace>", methods=["POST"])
def create_workspace(workspace):
    """Create a new workspace."""
    db.create_workspace(workspace)
    return workspace


@bp.route("/workspace/<workspace>/aql", methods=["POST"])
def aql(workspace):
    """Perform an AQL query in the given workspace."""
    query = request.data.decode("utf8")
    if not query:
        return (query, "400 Malformed Request Body")

    result = db.aql_query(workspace, query)

    def generate():
        yield "["

        comma = ""
        for row in result:
            yield f"{comma}{json.dumps(row)}"
            comma = ","

        yield "]"

    return Response(generate(), mimetype="text/json")


@bp.route("/workspace/<workspace>", methods=["DELETE"])
def delete_workspace(workspace):
    """Delete a workspace."""
    return workspace if db.delete_workspace(workspace) else None


@bp.route("/workspace/<workspace>/graph/<graph>", methods=["POST"])
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
        return (errors, "400 Graph Validation Failed")

    db.create_graph(workspace, graph, node_tables, edge_table)
    return graph
