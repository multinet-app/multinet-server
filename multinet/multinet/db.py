import os

from girder import logprint
from arango import ArangoClient

def with_client(fun):
    def wrapper(*args, **kwargs):
        kwargs['arango'] = kwargs.get('arango', ArangoClient(
            host=os.environ.get("ARANGO_HOST", "localhost"),
            port=int(os.environ.get("ARANGO_PORT", "8529"))))
        return fun(*args, **kwargs)
    return wrapper

def db_name(fully_qualified_name):
    return fully_qualified_name.split('/')[0]

@with_client
def db(name, arango=None):
    return arango.db(
        name,
        username="root",
        password=os.environ['MULTINET_APP_PASSWORD'])

@with_client
def graph(name, create=False, arango=None):
    db_name, graph_name = name.split('/')
    graphdb = db(db_name, arango=arango)
    if graphdb.has_graph(graph_name):
        return graphdb.graph(graph_name)
    elif create:
        return graphdb.create_graph(graph_name)
    else:
        return None
