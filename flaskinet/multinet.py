import csv
from graphql import graphql
from io import StringIO
import json
import newick
import uuid

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


@bp.route('/csv/<workspace>/<table>', methods=['POST'])
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
def _newick(workspace, table):
    """
    Store a newick tree into the database in coordinated node and edge tables.

    `workspace` - the target workspace.
    `table` - the target table.
    `data` - the newick data, passed in the request body.
    """
    app.logger.info('newick tree')
    tree = newick.loads(request.data.decode('utf8'))
    workspace = db.db(workspace)
    edgetable_name = '%s_edges' % table
    nodetable_name = '%s_nodes' % table
    if workspace.has_collection(edgetable_name):
        edgetable = workspace.collection(edgetable_name)
    else:
        # Note that edge=True must be set or the _from and _to keys
        # will be ignored below.
        edgetable = workspace.create_collection(edgetable_name, edge=True)
    if workspace.has_collection(nodetable_name):
        nodetable = workspace.collection(nodetable_name)
    else:
        nodetable = workspace.create_collection(nodetable_name)

    edgecount = 0
    nodecount = 0

    def read_tree(parent, node):
        nonlocal nodecount
        nonlocal edgecount
        key = node.name or uuid.uuid4().hex
        if not nodetable.has(key):
            nodetable.insert({'_key': key})
        nodecount = nodecount + 1
        for desc in node.descendants:
            read_tree(key, desc)
        if parent:
            edgetable.insert({
                '_from': '%s/%s' % (nodetable_name, parent),
                '_to': '%s/%s' % (nodetable_name, key),
                'length': node.length
            })
            edgecount += 1

    read_tree(None, tree[0])

    return dict(edgecount=edgecount, nodecount=nodecount)


@bp.route('/nested_json/<workspace>/<table>', methods=['POST'])
def nested_json(workspace, table):
    pass
