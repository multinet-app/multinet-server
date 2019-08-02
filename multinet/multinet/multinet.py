"""Flask blueprint for Multinet REST API."""
from graphql import graphql
import json

from flask import Blueprint, request
from flask import current_app as app

from .schema import schema

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
