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

@with_client
def create_workspace(name, arango=None):
    sys = db('_system', arango=arango)
    if not sys.has_database(name):
        sys.create_database(name)

@with_client
def create_graph(workspace, name, node_tables, edge_tables, arango=None):
    workspace = db(workspace, arango=arango)
    if workspace.has_graph(name):
        graph = workspace.graph(name)
    else:
        graph = workspace.create_graph(name)

    for table in node_tables:
        if not graph.has_vertex_collection(table):
            graph.create_vertex_collection(table)

    for table in edge_tables:
        if graph.has_edge_definition(table):
            graph.replace_edge_definition(
                edge_collection=table,
                from_vertex_collections=node_tables,
                to_vertex_collections=node_tables)
        else:
            graph.create_edge_definition(
                edge_collection=table,
                from_vertex_collections=node_tables,
                to_vertex_collections=node_tables)

    for table in graph.edge_definitions():
        if table['edge_collection'] not in edge_tables:
            graph.delete_edge_definition(table, purge=False)

    for table in graph.vertex_collections():
        if table not in node_tables:
            graph.delete_vertex_collection(table)
