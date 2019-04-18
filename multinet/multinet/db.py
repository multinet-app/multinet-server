import os

from girder import logprint
from arango import ArangoClient

from types import *

def with_client(fun):
    def wrapper(*args, **kwargs):
        kwargs['arango'] = kwargs.get('arango', ArangoClient(
            host=os.environ.get("ARANGO_HOST", "localhost"),
            port=int(os.environ.get("ARANGO_PORT", "8529"))))
        return fun(*args, **kwargs)
    return wrapper

@with_client
def db(name, arango=None):
    return arango.db(
        name,
        username="root",
        password=os.environ['MULTINET_APP_PASSWORD'])

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
    return [table['name'] for table in space.collections() if not table['name'].startswith('_')]

@with_client
def workspace_graphs(workspace, arango=None):
    space = db(workspace, arango=arango)
    return [graph['name'] for graph in space.graphs()]

@with_client
def table_fields(table, arango=None):
    workspace = db(table.workspace, arango=arango)
    if workspace.has_collection(table.name):
        sample = workspace.collection(table.name).random()
        return sample.keys()
    else:
        return []

@with_client
def nodes(query, cursor, arango=None):
    db = db(query.entity_type.graph.workspace, arango=arango)
    g = db.graph(query.entity_type.graph.name)
    tables = [db.collection(nodes) for nodes in g.vertex_collections()]
    if len(tables) == 0:
        return [], 0

    return paged(tables, cursor)

@with_client
def edges(query, cursor, arango=None):
    db = db(query.entity_type.graph.workspace, arango=arango)
    g = db.graph(query.entity_type.graph.name)
    tables = [db.collection(edges['edge_collection']) for edges in g.edge_definitions()]
    if len(tables) == 0:
        return [], 0

    return paged(tables, cursor)

def paged(tables, cursor):
    docs = []
    total = 0
    for table in tables:
        count = table.count()
        if (cursor.offset <= total + count) and (len(docs) < cursor.limit):
            items = table.all(skip=(cursor.offset-total), limit=(cursor.limit-len(docs)))
            docs += items
        total += count

    return docs, total

@with_client
def create_graph(graph, node_types, edge_types, arango=None):
    workspace = db(graph.workspace, arango=arango)
    if workspace.has_graph(graph.name):
        graph = workspace.graph(graph.name)
    else:
        graph = workspace.create_graph(graph.name)

    for table in node_types:
        if not graph.has_vertex_collection(table):
            graph.create_vertex_collection(table)

    for table in edge_types:
        if graph.has_edge_definition(table):
            graph.replace_edge_definition(
                edge_collection=table,
                from_vertex_collections=node_types,
                to_vertex_collections=node_types)
        else:
            graph.create_edge_definition(
                edge_collection=table,
                from_vertex_collections=node_types,
                to_vertex_collections=node_types)

    for table in graph.edge_definitions():
        if table['edge_collection'] not in edge_types:
            graph.delete_edge_definition(table, purge=False)

    for table in graph.vertex_collections():
        if table not in node_tables:
            graph.delete_vertex_collection(table)

@with_client
def table(table, arango=None):
    workspace = db(table.workspace, arango=arango)
    if workspace.has_collection(table.name):
        return workspace.collection(table.name)
    elif create:
        return workspace.create_collection(table.name)
    else:
        return None

@with_client
def graph(graph, create=False, arango=None):
    workspace = db(graph.workspace, arango=arango)
    if workspace.has_graph(graph.name):
        return workspace.graph(graph.name)
    elif create:
        return workspace.create_graph(graph.name)
    else:
        return None

def countRows(query):
    logprint(query)
    collection = table(query.table)
    if query.id:
        return 1
    elif query.search:
        return 0 # to be implemented
    else:
        return collection.count()

def fetchRows(query, cursor):
    collection = table(query.table)
    if query.id:
        return [collection.get(query.id)]
    elif query.search:
        return [] # to be implemented
    else:
        return collection.all(skip=cursor.offset, limit=cursor.limit)

def countNodes(query):
    if query.search or query.entity_type.name:
        return 0 # to be implemented
    else:
        return (nodes(query, Cursor(0, 0)))[1]

def fetchNodes(query, cursor):
    if query.search or query.entity_type.name:
        return [] # to be implemented
    else:
        return (nodes(query, cursor))[0]

def countEdges(query):
    if query.search or query.entity_type.name:
        return 0 # to be implemented
    else:
        return (edges(query, Cursor(0, 0)))[1]

def fetchEdges(query, cursor):
    if query.search or query.entity_type.name:
        return [] # to be implemented
    else:
        return (edges(query, cursor))[0]

def graph_node_types(graph):
    workspace = db(graph.workspace)
    graph = workspace.graph(graph.name)
    return graph.vertex_collections()

def graph_edge_types(graph):
    workspace = db(graph.workspace)
    graph = workspace.graph(graph.name)
    return [edges['edge_collection'] for edges in graph.edge_definitions()]

def source(edge):
    pass

def target(edge):
    pass

def outgoing(node):
    pass

def incoming(node):
    pass

def create_table(table, fields, primary):
    pass
