import os

from girder import logprint
from arango import ArangoClient

def with_client(fun):
    def wrapper(*args, **kwargs):
        client = ArangoClient(
            host=os.environ["ARANGO_HOST"],
            port=int(os.environ["ARANGO_PORT"]))
        return fun(*args, arango=client, **kwargs)
    return wrapper

def db_name(fully_qualified_name):
    return fully_qualified_name.split('/')[0]

def db(arango, name):
    return arango.db(
        name,
        username="root",
        password=os.environ['MULTINET_APP_PASSWORD'])

@with_client
def graph(name, create=False, arango=None):
    db_name, graph_name = name.split('/')
    graphdb = db(arango, db_name)
    if graphdb.has_graph(graph_name):
        return graphdb.graph(graph_name)
    elif create:
        return graphdb.create_graph(graph_name)
    else:
        return None
