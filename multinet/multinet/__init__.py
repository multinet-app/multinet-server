from girder import plugin, logprint
from girder.api import access
from girder.api.rest import Resource, RestException, getBodyJson
from girder.api.describe import Description, autoDescribeRoute

import csv
from io import StringIO
import json
import logging
from graphql import graphql
import cherrypy
import newick
import uuid

from .schema import schema
from . import db


def graphql_query(query):
    result = graphql(schema, query)
    if result:
        errors= [error.message for error in result.errors] if result.errors else []
        logprint("Errors in request: %s" % len(errors), level=logging.WARNING)
        for error in errors[:10]:
            logprint(error, level=logging.WARNING)
    else:
        errors = []
    return dict(data=result.data, errors=errors)


class MultiNet(Resource):
    def __init__(self, port):
        super(MultiNet, self).__init__()
        self.resourceName = 'multinet'
        self.arango_port = port
        self.route('POST', ('graphql',), self.graphql)
        self.route('POST', ('bulk', ':workspace', ':table'), self.bulk)

        # Newick tree operations.
        self.route('POST', ('newick', 'tree', ':workspace', ':table'), self.tree)

        # Operations for Juniper application.
        self.route('POST', ('juniper', 'node'), self.juniper_get_node)

    @access.public
    @autoDescribeRoute(
        Description('Receive GraphQL queries')
        .param('query', 'GraphQL query text', paramType='body', required=True)
    )
    def graphql(self, params):
        logprint('Executing GraphQL Request', level=logging.INFO)
        query = getBodyJson()['query']
        logprint('request: %s' % query, level=logging.DEBUG)

        return graphql_query(query)

    @access.public
    @autoDescribeRoute(
        Description('Store CSV data in database')
        .param('workspace', 'Target workspace', required=True)
        .param('table', 'Target table', required=True)
        .param('data', 'CSV data', paramType='body', required=True)
    )
    def bulk(self, params, workspace=None, table=None):
        logprint('Bulk Loading', level=logging.INFO)
        rows = csv.DictReader(StringIO(cherrypy.request.body.read().decode('utf8')))
        workspace = db.db(workspace)

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
        Description('Store tree data in database from nexus/newick style tree files. '
                    'Two tables will be created with the given table name, <table>_edges and <table_nodes')
        .param('workspace', 'Target workspace', required=True)
        .param('table', 'Target table', required=True)
        .param('data', 'Tree data', paramType='body', required=True)
    )
    def tree(self, params, workspace=None, table=None, schema=None):
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
        def read_tree (parent, node):
            nonlocal nodecount
            nonlocal edgecount
            key = node.name or uuid.uuid4().hex
            if not nodetable.has(key):
                nodetable.insert({"_key": key})
            nodecount = nodecount + 1
            for desc in node.descendants:
                read_tree(key, desc)
            if parent:
                edgetable.insert({
                    "_from": "%s/%s" % (nodetable_name, parent),
                    "_to": "%s/%s" % (nodetable_name, key),
                    "length": node.length
                })
                edgecount += 1

        read_tree(None, tree[0])

        return dict(edgecount=edgecount, nodecount=nodecount)

    @access.public
    @autoDescribeRoute(
        Description('Retrieve data for a single node for use in the Juniper application.')
        .param('nodeId', 'ID of the node', required=True)
    )
    def juniper_get_node(self, params, nodeId=None):
        final = {}

        query = f'''query {{
            nodes (workspace: "dblp", graph: "coauth", nodeType: "author", key: "author/{nodeId}") {{
                total
                nodes {{
                    key
                    type
                    incoming {{
                        total
                        edges (limit: 20) {{
                            source {{
                                outgoing {{
                                  total
                                }}
                                properties (keys: ["type", "title", "_key"]) {{
                                    key
                                    value
                                }}
                            }}
                        }}
                    }}
                    properties (keys: ["type", "name"]) {{
                        key
                        value
                    }}
                }}
            }}
        }}'''

        result = graphql_query(query)

        author = result['data']['nodes']['nodes'][0]
        props = {val['key']: val['value'] for val in author['properties']}

        author_data = {'graphDegree': author['incoming']['total'],
                       'label': 'Author',
                       'title': props['name'],
                       'uuid': author['key'].split('/')[1]}

        def make_link(link):
            props = {prop['key']: prop['value'] for prop in link['source']['properties']}
            return {'source': author_data,
                    'target': {'graphDegree': link['source']['outgoing']['total'],
                               'label': 'Article',
                               'title': props['title'],
                               'uuid': props['_key']}}

        links = [make_link(l) for l in author['incoming']['edges']]
        targetNodes = [link['target'] for link in links]

        return {'nodes': [author_data],
                'links': links,
                'root': [author['key'].split('/')[1]],
                'targetNodes': targetNodes}

class GirderPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'MultiNet'

    def load(self, info):
        # add plugin loading logic here
        info['apiRoot'].multinet = MultiNet(port=8080)
