"""Defines the MultiNet Girder plugin."""

from girder import plugin, logprint
from girder.api import access
from girder.api.rest import Resource, getBodyJson
from girder.api.describe import Description, autoDescribeRoute
from girder.exceptions import RestException

import csv
from io import StringIO
import itertools
import json
import logging
from graphql import graphql
import cherrypy
import newick
import uuid

from .schema import schema
from . import db


def graphql_query(query, variables=None):
    """Perform a GraphQL query using optional variable definitions."""
    result = graphql(schema, query, variables=variables or {})
    if result:
        errors = [error.message for error in result.errors] if result.errors else []
        logprint('Errors in request: %s' % len(errors), level=logging.WARNING)
        for error in errors[:10]:
            logprint(error, level=logging.WARNING)
    else:
        errors = []
    return dict(data=result.data, errors=errors, query=query)


def validate_csv(rows):
    """Perform any necessary CSV validation, and raise appropriate exceptions."""
    # Check for key uniqueness
    if ('_key' in rows.fieldnames):
        keys = [row['_key'] for row in rows]
        uniqueKeys = set()
        duplicates = set()
        for key in keys:
            if key in uniqueKeys:
                duplicates.add(key)
            else:
                uniqueKeys.add(key)

        if (len(duplicates) > 0):
            raise RestException(f'CSV Validation Failed: Duplicate Keys {", ".join(duplicates)}.')


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


class MultiNet(Resource):
    """Define the MultiNet API within Girder."""

    def __init__(self, port):
        """
        Initialize the plugin.

        `port` - the port where Arango is running.
        """
        super(MultiNet, self).__init__()
        self.resourceName = 'multinet'
        self.arango_port = port
        self.route('POST', ('graphql',), self.graphql)
        self.route('POST', ('csv', ':workspace', ':table'), self.bulk)

        # Newick tree operations.
        self.route('POST', ('newick', ':workspace', ':table'), self.tree)

        # Nested JSON.
        self.route('POST', ('nested_json', ':workspace', ':table'), self.nested_json)

    @access.public
    @autoDescribeRoute(
        Description('Receive GraphQL queries')
        .param('query', 'GraphQL query text', paramType='body', required=True)
    )
    def graphql(self, params):
        """
        Perform a GraphQL query.

        The body of the request is a JSON object containing a required `query`
        property containing the text of the query itself, and an options
        `variables` property, containing variable definitions for the body of
        `query`.
        """
        logprint('Executing GraphQL Request', level=logging.INFO)

        # Grab the GraphQL parameters from the request body.
        body = getBodyJson()
        query = body['query']
        variables = body.get('variables')

        logprint('request: %s' % query, level=logging.DEBUG)
        logprint('variables: %s' % variables, level=logging.DEBUG)

        return graphql_query(query, variables)

    @access.public
    @autoDescribeRoute(
        Description('Store CSV data in database')
        .param('workspace', 'Target workspace', required=True)
        .param('table', 'Target table', required=True)
        .param('data', 'CSV data', paramType='body', required=True)
        .errorResponse()
    )
    def bulk(self, params, workspace=None, table=None):
        """
        Append CSV rows to a particular table in a particular workspace.

        `workspace` - the target workspace.
        `table` - the target table.
        `data` - CSV text, passed in the request body.
        """
        logprint('Bulk Loading', level=logging.INFO)
        rows = csv.DictReader(StringIO(cherrypy.request.body.read().decode('utf8')))
        workspace = db.db(workspace)

        # Do any CSV validation necessary, and raise appropriate exceptions
        validate_csv(rows)

        # Set the collection, paying attention to whether the data contains
        # _from/_to fields.
        coll = None
        if workspace.has_collection(table):
            coll = workspace.collection(table)
        else:
            edges = '_from' in rows.fieldnames and '_to' in rows.fieldnames
            coll = workspace.create_collection(table, edge=edges)

        # Insert the data into the collection.
        results = coll.insert_many(rows)
        return dict(count=len(results))

    @access.public
    @autoDescribeRoute(
        Description('Store tree in database from nexus/newick files. '
                    'Two tables will be created with the given table name, '
                    '<table>_edges and <table>_nodes')
        .param('workspace', 'Target workspace', required=True)
        .param('table', 'Target table', required=True)
        .param('data', 'Tree data', paramType='body', required=True)
    )
    def tree(self, params, workspace=None, table=None, schema=None):
        """
        Store a newick tree into the database in coordinated node and edge tables.

        `workspace` - the target workspace.
        `table` - the target table.
        `data` - the newick data, passed in the request body.
        """
        logprint('Bulk Loading', level=logging.INFO)
        tree = newick.loads(cherrypy.request.body.read().decode('utf8'))
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

    @access.public
    @autoDescribeRoute(
        Description('Store a nested_json file in database. '
                    'Two tables will be created with the given table name, '
                    '<table>_edges and <table>_nodes.')
        .param('workspace', 'Target workspace', required=True)
        .param('table', 'Target table', required=True)
        .param('data', 'nested_json data', paramType='body', dataType='string', required=True)
    )
    def nested_json(self, params, workspace=None, table=None):
        """
        Store a nested_json tree into the database in coordinated node and edge tables.

        `workspace` - the target workspace.
        `table` - the target table.
        `data` - the nested_json data, passed in the request body.
        """
        # Set up the parameters.
        data = cherrypy.request.body.read().decode('utf8')
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


class GirderPlugin(plugin.GirderPlugin):
    """Girder plugin infrastructure for MultiNet API."""

    DISPLAY_NAME = 'MultiNet'

    def load(self, info):
        """Load the plugin at Girder startup."""
        info['apiRoot'].multinet = MultiNet(port=8080)
