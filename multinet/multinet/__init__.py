from girder import plugin
from girder.api import access
from girder.api.rest import Resource
from girder.api.describe import Description, autoDescribeRoute


class MultiNet(Resource):
    def __init__(self):
        super(MultiNet, self).__init__()
        self.resourceName = 'multinet'

        self.route('GET', ('greeting',), self.get_greeting)

    @access.public
    @autoDescribeRoute(
        Description('Get a greeting')
    )
    def get_greeting(self):
        return '¡Hola!'


class GirderPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'MultiNet'

    def load(self, info):
        # add plugin loading logic here
        info['apiRoot'].multinet = MultiNet()
