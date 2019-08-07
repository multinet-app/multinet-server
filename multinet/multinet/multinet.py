"""Flask blueprint for Multinet REST API."""
from graphql import graphql
import json

from flask import Blueprint, request
from flask import current_app as app

from .schema import schema
from . import db

bp = Blueprint('multinet', __name__)


def graphql_query(query, variables=None):
    """Perform a GraphQL query using optional variable definitions."""
    data = None
    errors = []

    result = graphql(schema, query, variables=variables or {})
    if result:
        errors = [error.message for error in result.errors] if result.errors else []
        data = result.data

        if errors:
            app.logger.error('Errors in request: %s' % len(errors))
            for error in errors[:10]:
                app.logger.error(error)

            excess = len(errors) - 10
            if excess > 0:
                app.logger.error(f'{excess} more error{"s" if excess > 1 else ""}')

    return dict(data=data, errors=errors, query=query)


@bp.route('/graphql', methods=['POST'])
def _graphql():
    app.logger.info('Executing GraphQL Request')

    # Grab the GraphQL parameters from the request body.
    query = request.data.decode('utf8')
    variables = None
    try:
        app.logger.info('trying to parse json')
        body = json.loads(query)
        query = body['query']
        variables = body.get('variables')
    except json.decoder.JSONDecodeError:
        app.logger.info('couldnt do it')
        pass

    app.logger.debug('request: %s' % query)
    app.logger.debug('variables: %s' % variables)

    result = graphql_query(query, variables)
    return result


@bp.route('/workspace/<workspace>', methods=['POST'])
def create_workspace(workspace):
    """Create a new workspace."""
    db.create_workspace(workspace)
    return workspace


@bp.route('/workspace/<workspace>', methods=['DELETE'])
def delete_workspace(workspace):
    """Delete a workspace."""
    return workspace if db.delete_workspace(workspace) else None


@bp.route('/workspace/<workspace>/graph/<graph>', methods=['POST'])
def create_graph(workspace, graph):
    """Create a graph."""
    # Get parameters from request body.
    body = request.data.decode('utf8')
    try:
        params = json.loads(body)
    except json.decoder.JSONDecodeError:
        return (body, '400 Malformed Request Body')

    node_tables = params.get('node_tables')
    edge_table = params.get('edge_table')

    missing = [arg for arg in [node_tables, edge_table] if arg is None]
    if missing:
        return (missing, '400 Missing Required Parameters')

    # Validate that all referenced tables exist
    edges = list(db.db(workspace).collection(edge_table).find({}))
    invalid_from = set([edge['_from'].split('/')[0] for edge in edges
                       if edge['_from'].split('/')[0] not in node_tables])
    invalid_to = set([edge['_to'].split('/')[0] for edge in edges
                     if edge['_to'].split('/')[0] not in node_tables])

    if invalid_from or invalid_to:
        error = {'error': 'undefined_tables',
                 'detail': list(invalid_from | invalid_to)}
        return (error, '400 Edge Table Validation Failed')

    return graph if db.create_graph2(workspace, graph, node_tables, edge_table) else None
