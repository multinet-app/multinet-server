"""Flask blueprint for Multinet REST API."""
from graphql import graphql

from flask import Blueprint, request
from flask import current_app as app
from webargs import fields
from webargs.flaskparser import use_kwargs

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

    # Validate that all referenced tables exist
    edges = list(db.db(workspace).collection(edge_table).find({}))
    invalid_from = set(
        [
            edge["_from"].split("/")[0]
            for edge in edges
            if edge["_from"].split("/")[0] not in node_tables
        ]
    )
    invalid_to = set(
        [
            edge["_to"].split("/")[0]
            for edge in edges
            if edge["_to"].split("/")[0] not in node_tables
        ]
    )

    if invalid_from or invalid_to:
        error = {"error": "undefined_tables", "detail": list(invalid_from | invalid_to)}
        return (error, "400 Edge Table Validation Failed")

    if db.create_graph(workspace, graph, node_tables, edge_table):
        return graph
    else:
        return (graph, "409 Graph Already Exists")
