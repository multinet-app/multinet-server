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
def get_workspaces(name, arango=None):
    sys = db('_system', arango=arango)
    if name and sys.has_database(name):
        return [name]

    workspaces = sys.databases()
    return [workspace for workspace in workspaces if workspace != '_system']

@with_client
def workspace_tables(workspace, arango=None):
    space = db(workspace, arango=arango)
    return ['%s/%s' % (workspace, table['name']) for table in space.collections() if not table['name'].startswith('_')]

@with_client
def workspace_graphs(workspace, arango=None):
    space = db(workspace, arango=arango)
    return ['%s/%s' % (workspace, graph['name']) for graph in space.graphs()]

@with_client
def table_fields(table, arango=None):
    db_name, coll_name = table.split('/')
    workspace = db(db_name, arango=arango)
    if workspace.has_collection(coll_name):
        sample = workspace.collection(coll_name).random()
        logprint(sample)
        return sample.keys()
    else:
        return []

@with_client
def graph_edge_tables(graph, arango=None):
    db_name, graph_name = graph.split('/')
    workspace = db(db_name, arango=arango)
    if workspace.has_graph(graph_name):
        graph = workspace.graph(graph_name)
        return [edges['edge_collection'] for edges in graph.edge_definitions()]
    else:
        return []

@with_client
def graph_node_tables(graph, arango=None):
    db_name, graph_name = graph.split('/')
    workspace = db(db_name, arango=arango)
    if workspace.has_graph(graph_name):
        graph = workspace.graph(graph_name)
        return [nodes for nodes in graph.vertex_collections()]
    else:
        return []


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
