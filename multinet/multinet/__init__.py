from girder import plugin
from girder.api import access
from girder.api.rest import Resource, RestException
from girder.api.describe import Description, autoDescribeRoute

import requests


class MultiNet(Resource):
    def __init__(self, port):
        super(MultiNet, self).__init__()
        self.resourceName = 'multinet'
        self.arango_port = port

        self.route('GET', ('vertices',), self.get_vertices)

    @access.public
    @autoDescribeRoute(
        Description('Foobar')
        .param('db', 'The database', dataType='string', required=True)
        .param('collection', 'The collection', dataType='string', required=True)
    )
    def get_vertices(self, params):
        db = params['db']
        collection = params['collection']

        r = requests.get('http://localhost:8080/vertices/{}/graph/{}'.format(db, collection))
        if r.status_code == requests.codes.ok:
            return r.json()

        raise RestException(r.reason, r.status_code)


class GirderPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'MultiNet'

    def load(self, info):
        # add plugin loading logic here
        info['apiRoot'].multinet = MultiNet(port=8080)
