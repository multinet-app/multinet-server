"""Flask blueprint for Multinet REST API."""
from graphql import graphql
import json

from flask import Blueprint, request
from flask import current_app as app

from .schema import schema
from . import db

bp = Blueprint("multinet", __name__)


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
def _graphql():
    app.logger.info("Executing GraphQL Request")

    # Grab the GraphQL parameters from the request body.
    query = request.data.decode("utf8")
    variables = None
    try:
        app.logger.info("trying to parse json")
        body = json.loads(query)
        query = body["query"]
        variables = body.get("variables")
    except json.decoder.JSONDecodeError:
        app.logger.info("couldnt do it")
        pass

    app.logger.debug("request: %s" % query)
    app.logger.debug("variables: %s" % variables)

    result = graphql_query(query, variables)
    return result


@bp.route("/workspace/<workspace>", methods=["POST"])
def create_workspace(workspace):
    """Create a new workspace."""
    db.create_workspace(workspace)
    return workspace


@bp.route("/workspace/<workspace>", methods=["DELETE"])
def delete_workspace(workspace):
    """Delete a workspace."""
    return workspace if db.delete_workspace(workspace) else None


@bp.route("/workspace/<workspace>/graph/<graph>", methods=["POST"])
def create_graph(workspace, graph):
    """Create a graph."""

    # Get parameters from request body.
    body = request.data.decode("utf8")
    try:
        params = json.loads(body)
    except json.decoder.JSONDecodeError:
        return (body, "400 Malformed Request Body")

    node_tables = params.get("node_tables")
    edge_table = params.get("edge_table")

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
