import csv
from graphql import graphql
from io import StringIO
import json

from flask import Blueprint, request
from flask import current_app as app

from .schema import schema
from . import db

bp = Blueprint('multinet', __name__, url_prefix='/multinet')


def graphql_query(query, variables=None):
    """Perform a GraphQL query using optional variable definitions."""
    result = graphql(schema, query, variables=variables or {})
    if result:
        errors = [error.message for error in result.errors] if result.errors else []
        app.logger.warn('Errors in request: %s' % len(errors))
        for error in errors[:10]:
            app.logger.warn(error)
    else:
        errors = []
    return dict(data=result.data, errors=errors, query=query)


def validate_csv(rows):
    pass


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


@bp.route('/csv/<workspace>/<table>', methods=['GET', 'POST'])
def bulk(workspace, table):
    app.logger.info('Bulk Loading')

    body = request.data.decode('utf8')

    rows = csv.DictReader(StringIO(body))
    workspace = db.db(workspace)

    # Do any CSV validation necessary, and raise appropriate exceptions
    validate_csv(rows)

    # Set the collection, paying attention to whether the data contains
    # _from/_to fields.
    # coll = None
    if workspace.has_collection(table):
        coll = workspace.collection(table)
    else:
        edges = '_from' in rows.fieldnames and '_to' in rows.fieldnames
        coll = workspace.create_collection(table, edge=edges)

    # Insert the data into the collection.
    results = coll.insert_many(rows)
    return dict(count=len(results))


@bp.route('/newick/<workspace>/<table>', methods=['POST'])
def newick(workspace, table):
    pass


@bp.route('/nested_json/<workspace>/<table>', methods=['POST'])
def nested_json(workspace, table):
    pass
