"""Flask blueprint for Multinet REST API."""
import csv
from graphql import graphql
from io import StringIO
import itertools
import json
import newick
import re
import uuid

from flask import Blueprint, request
from flask import current_app as app

from .schema import schema
from . import db

bp = Blueprint('multinet', __name__, url_prefix='/multinet')


def graphql_query(query, variables=None):
    """Perform a GraphQL query using optional variable definitions."""
    data = None
    errors = []

    result = graphql(schema, query, variables=variables or {})
    if result:
        errors = [error.message for error in result.errors] if result.errors else []
        app.logger.warn('Errors in request: %s' % len(errors))
        for error in errors[:10]:
            app.logger.warn(error)
    else:
        data = result.data

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

        return {'error': 'syntax' if detail else None,
                'detail': detail}

    return {'error': None}


def analyze_nested_json(data, int_table_name, leaf_table_name):
    """
    Transform nested JSON data into MultiNet format.

    `data` - the text of a nested_json file
    `(nodes, edges)` - a node and edge table describing the tree.
    """
    id = itertools.count(100)
    data = json.loads(data)

    def keyed(rec):
        if '_key' in rec:
            return rec

        # keyed = dict(rec)
        rec['_key'] = str(next(id))

        return rec

    # The helper function will collect nodes and edges into these two lists.
    nodes = [[], []]
    edges = []

    def helper(tree):
        # Grab the root node of the subtree, and the child nodes.
        root = keyed(tree.get('node_data', {}))
        children = tree.get('children', [])

        # Capture the root node into one of two tables.
        if children:
            nodes[0].append(root)
        else:
            nodes[1].append(root)

        # Capture edges for each child.
        for child in children:
            # Grab the child data.
            child_data = keyed(child.get('node_data', {}))

            # Determine which table the child is in.
            child_table_name = int_table_name if child.get('children') else leaf_table_name

            # Record the edge record.
            edge = dict(child.get('edge_data', {}))
            edge['_from'] = f'{child_table_name}/{child_data["_key"]}'
            edge['_to'] = f'{int_table_name}/{root["_key"]}'
            edges.append(edge)

        # Recursively add the child subtrees.
        for child in children:
            helper(child)

    # Kick off the analysis.
    helper(data)
    return (nodes, edges)


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
    if result['error'] == 'duplicate':
        payload = {'message': 'Duplicated keys',
                   'duplicates': result['detail']}
        return (payload, '400 Bad CSV Data')
    elif result['error'] == 'syntax':
        payload = {'message': 'Bad syntax',
                   'rows': result['detail']}
        return (payload, '400 Bad CSV Data')

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
    """
    Store a nested_json tree into the database in coordinated node and edge tables.

    `workspace` - the target workspace.
    `table` - the target table.
    `data` - the nested_json data, passed in the request body.
    """
    # Set up the parameters.
    data = request.data.decode('utf8')
    workspace = db.db(workspace)
    edgetable_name = f'{table}_edges'
    int_nodetable_name = f'{table}_internal_nodes'
    leaf_nodetable_name = f'{table}_leaf_nodes'

    # Set up the database targets.
    if workspace.has_collection(edgetable_name):
        edgetable = workspace.collection(edgetable_name)
    else:
        edgetable = workspace.create_collection(edgetable_name, edge=True)

    if workspace.has_collection(int_nodetable_name):
        int_nodetable = workspace.collection(int_nodetable_name)
    else:
        int_nodetable = workspace.create_collection(int_nodetable_name)

    if workspace.has_collection(leaf_nodetable_name):
        leaf_nodetable = workspace.collection(leaf_nodetable_name)
    else:
        leaf_nodetable = workspace.create_collection(leaf_nodetable_name)

    # Analyze the nested_json data into a node and edge table.
    (nodes, edges) = analyze_nested_json(data, int_nodetable_name, leaf_nodetable_name)

    # Upload the data to the database.
    edgetable.insert_many(edges)
    int_nodetable.insert_many(nodes[0])
    leaf_nodetable.insert_many(nodes[1])

    return dict(edgecount=len(edges), int_nodecount=len(nodes[0]), leaf_nodecount=len(nodes[1]))
