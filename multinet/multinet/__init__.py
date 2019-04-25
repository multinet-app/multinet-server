from girder import plugin, logprint
from girder.api import access
from girder.api.rest import Resource, RestException, getBodyJson
from girder.api.describe import Description, autoDescribeRoute

import csv
import json
import logging
from graphql import graphql
import cherrypy

from .schema import schema
from . import db

class MultiNet(Resource):
    def __init__(self, port):
        super(MultiNet, self).__init__()
        self.resourceName = 'multinet'
        self.arango_port = port
        self.route('POST', ('graphql',), self.graphql)
        self.route('POST', ('bulk', ':workspace', ':table'), self.bulk)

    @access.public
    @autoDescribeRoute(
        Description('Receive GraphQL queries')
        .param('query', 'GraphQL query text', paramType='body', required=True)
    )
    def graphql(self, params):
        logprint('Executing GraphQL Request', level=logging.INFO)
        query = getBodyJson()['query']
        logprint('request: %s' % query, level=logging.DEBUG)

        result = graphql(schema, query)
        if result:
            errors= [error.message for error in result.errors] if result.errors else []
            logprint("Errors in request: %s" % len(errors), level=logging.WARNING)
            for error in errors[:10]:
                logprint(error, level=logging.WARNING)
        else:
            errors = []
        return dict(data=result.data, errors=errors)

    @access.public
    @autoDescribeRoute(
        Description('Store CSV data in database')
        .param('workspace', 'Target workspace', required=True)
        .param('table', 'Target table', required=True)
        .param('data', 'CSV data', paramType='body', required=True)
    )
    def bulk(self, params, workspace=None, table=None):
        logprint('Bulk Loading', level=logging.INFO)
        rows = csv.DictReader(cherrypy.request.body.read().decode('utf8'))
        workspace = db.db(workspace)
        if workspace.has_collection(table):
            table = workspace.collection(table)
        else:
            table = workspace.create_collection(table)

        count = 0
        for row in rows:
            count = count+1
            table.insert(row)
        return dict(count=count)

class GirderPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'MultiNet'

    def load(self, info):
        # add plugin loading logic here
        info['apiRoot'].multinet = MultiNet(port=8080)
