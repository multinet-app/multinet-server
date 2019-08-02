"""Flask blueprint for Multinet REST API."""
import csv
from graphql import graphql
from io import StringIO
import json
import re

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


def validate_csv(rows):
    """Perform any necessary CSV validation, and raise appropriate exceptions."""
    if '_key' in rows.fieldnames:
        # Node Table, check for key uniqueness
        keys = [row['_key'] for row in rows]
        uniqueKeys = set()
        duplicates = set()
        for key in keys:
            if key in uniqueKeys:
                duplicates.add(key)
            else:
                uniqueKeys.add(key)

        if (len(duplicates) > 0):
            return {'error': 'duplicate',
                    'detail': list(duplicates)}
    elif '_from' in rows.fieldnames and '_to' in rows.fieldnames:
        # Edge Table, check that each cell has the correct format
        valid_cell = re.compile('[^/]+/[^/]+')

        detail = []

        for i, row in enumerate(rows):
            fields = []
            if not valid_cell.match(row['_from']):
                fields.append('_from')
            if not valid_cell.match(row['_to']):
                fields.append('_to')

            if fields:
                # i+2 -> +1 for index offset, +1 due to header row
                detail.append({'fields': fields,
                               'row': i + 2})

        if detail:
            return {'error': 'syntax',
                    'detail': detail}

    return None


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


@bp.route('/csv/<workspace>/<table>', methods=['POST'])
def bulk(workspace, table):
    """
    Store a CSV file into the database as a node or edge table.

    `workspace` - the target workspace
    `table` - the target table
    `data` - the CSV data, passed in the request body. If the CSV data contains
             `_from` and `_to` fields, it will be treated as an edge table.
    """
    app.logger.info('Bulk Loading')

    body = request.data.decode('utf8')

    rows = csv.DictReader(StringIO(body))
    workspace = db.db(workspace)

    # Do any CSV validation necessary, and raise appropriate exceptions
    result = validate_csv(rows)
    if result:
        return (result, '400 CSV Validation Failed')

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
