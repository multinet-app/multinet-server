import os

from arango import ArangoClient

from multinet.types import Row, Entity, EntityType, Cursor


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
def delete_workspace(name, arango=None):
    sys = db('_system', arango=arango)
    if sys.has_database(name):
        sys.delete_database(name)
        return True
    else:
        return False


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
def workspace_graph(workspace, name, arango=None):
    space = db(workspace, arango=arango)

    graphs = filter(lambda g: g['name'] == name, space.graphs())
    graph = None
    try:
        graph = next(graphs)
    except StopIteration:
        pass

    return graph


@with_client
def table_fields(query, arango=None):
    workspace = db(query.workspace, arango=arango)
    if workspace.has_collection(query.table):
        sample = workspace.collection(query.table).random()
        return sample.keys()
    else:
        return []


@with_client
def nodes(query, cursor, arango=None):
    workspace = db(query.workspace, arango=arango)
    graph = workspace.graph(query.graph)
    if query.entity_type:
        if query.id:
            result = workspace.collection(query.entity_type).get(query.id)
            if result is not None:
                return [Entity(query.workspace, query.graph, query.entity_type, workspace.collection(query.entity_type).get(query.id))], 1
            else:
                return [], 0
        else:
            tables = [workspace.collection(query.entity_type)]
    else:
        tables = [workspace.collection(nodes) for nodes in graph.vertex_collections()]
    if len(tables) == 0:
        return [], 0

    pages = paged(tables, cursor, query.id)
    return [Entity(query.workspace, query.graph, node['_id'].split('/')[0], node)
            for node in pages[0]], pages[1]


@with_client
def edges(query, cursor, arango=None):
    workspace = db(query.workspace, arango=arango)
    graph = workspace.graph(query.graph)
    if query.entity_type:
        if query.id:
            return [Entity(query.workspace, query.graph, query.entity_type, workspace.collection(query.entity_type).get(query.id))], 1
        else:
            tables = [workspace.collection(query.entity_type)]
    else:
        tables = [workspace.collection(edges['edge_collection']) for edges in graph.edge_definitions()]
    if len(tables) == 0:
        return [], 0

    pages = paged(tables, cursor, query.id)
    return [Entity(query.workspace, query.graph, edge['_id'].split('/')[0], edge)
            for edge in pages[0]], pages[1]


def paged(tables, cursor, id=None):
    # If id is set, we have to simply verify that: 1. one of the specified
    # tables contains the id'd object and 2. the cursor has an offset of 0.
    if id:
        if cursor.offset > 0:
            return [], 0

        doc = None
        for table in tables:
            doc = table.get(id)
            if doc:
                break

        if doc:
            return [doc], 1
        else:
            return [], 0

    # Need to retrieve up to cursor.limit items.
    remaining = cursor.limit or -1
    offset = cursor.offset

    # We will step through the tables one by one collecting items.
    which = 0

    # Continue looking for items until we run out of tables, or we find the
    # total number we need.
    #
    # NOTE: if `remaining` is set to -1, then it will never reach 0 and thus
    # represents an unlimited query; similarly, if it is positive, then it
    # *will* reach 0 eventually (given enough avaialble data) and thus
    # represents a limited query.
    docs = []
    while remaining != 0 and which < len(tables):
        # Select the table.
        table = tables[which]

        # Compute how many entries of this table are available, and grab the
        # appropriate number.
        available = table.count() - offset
        if remaining < 0:
            take = available
        else:
            take = min(available, remaining)
        docs += table.all(skip=offset, limit=take)

        remaining -= take
        offset = 0
        which += 1

    return docs, len(docs)


@with_client
def create_graph(graph, node_tables, edge_table, arango=None):
    workspace = db(graph.workspace, arango=arango)
    if workspace.has_graph(graph.graph):
        return False
    else:
        graph = workspace.create_graph(graph.graph)
        graph.create_edge_definition(edge_collection=edge_table, from_vertex_collections=node_tables, to_vertex_collections=node_tables)

        return True

    # for table in node_types:
    #     if not graph.has_vertex_collection(table):
    #         graph.create_vertex_collection(table)
    #
    # for table in edge_types:
    #     if graph.has_edge_definition(table):
    #         graph.replace_edge_definition(
    #             edge_collection=table,
    #             from_vertex_collections=node_types,
    #             to_vertex_collections=node_types)
    #     else:
    #         graph.create_edge_definition(
    #             edge_collection=table,
    #             from_vertex_collections=node_types,
    #             to_vertex_collections=node_types)
    #
    # for table in graph.edge_definitions():
    #     if table['edge_collection'] not in edge_types:
    #         graph.delete_edge_definition(table, purge=False)
    #
    # for table in graph.vertex_collections():
    #     if table not in node_types:
    #         graph.delete_vertex_collection(table)


@with_client
def table(query, create=False, arango=None):
    workspace = db(query.workspace, arango=arango)
    if workspace.has_collection(query.table):
        return workspace.collection(query.table)
    elif create:
        return workspace.create_collection(query.table)
    else:
        return None


@with_client
def graph(graph, create=False, arango=None):
    workspace = db(graph.workspace, arango=arango)
    if workspace.has_graph(graph.graph):
        return workspace.graph(graph.graph)
    elif create:
        return workspace.create_graph(graph.graph)
    else:
        return None


def countRows(query):
    collection = table(query)
    if query.id:
        return 1
    elif query.search:
        return 0  # to be implemented
    else:
        return collection.count()


def fetchRows(query, cursor):
    collection = table(query)
    if query.id:
        return [collection.get(query.id)]
    elif query.search:
        return []  # to be implemented
    else:
        return [Row(query.workspace, query.table, row) for row in collection.all(skip=cursor.offset, limit=cursor.limit)]


def countNodes(query):
    if query.search:
        return 0  # to be implemented
    else:
        return (nodes(query, Cursor(0, 0)))[1]


def fetchNodes(query, cursor):
    if query.search:
        return []  # to be implemented
    else:
        return (nodes(query, cursor))[0]


def countEdges(query):
    if query.search:
        return 0  # to be implemented
    else:
        return (edges(query, Cursor(0, 0)))[1]


def fetchEdges(query, cursor):
    if query.search:
        return []  # to be implemented
    else:
        return (edges(query, cursor))[0]


def graph_node_types(graph):
    workspace = db(graph.workspace)
    gr = workspace.graph(graph.graph)
    return [EntityType(graph.workspace, graph.graph, table) for table in gr.vertex_collections()]


def graph_edge_types(graph):
    workspace = db(graph.workspace)
    gr = workspace.graph(graph.graph)
    return [EntityType(graph.workspace, graph.graph, edges['edge_collection']) for edges in gr.edge_definitions()]


def type_properties(workspace, graph, table):
    workspace = db(workspace)
    metadata = workspace.collection("_graphs")
    graph_meta = metadata.get(graph)

    if graph_meta.get('nodeTypes', None) is not None and graph_meta['nodeTypes'].get(table, None):
        return graph_meta['nodeTypes'][table]

    if graph_meta.get('edgeTypes', None) is not None and graph_meta['edgeTypes'].get(table, None):
        return graph_meta['edgeTypes'][table]


def source(edge):
    workspace = db(edge.workspace)
    nodeTable = workspace.collection(edge.data['_from'].split('/')[0])
    return Entity(edge.workspace, edge.graph, edge.data['_from'].split('/')[0], nodeTable.get(edge.data['_from']))


def target(edge):
    workspace = db(edge.workspace)
    nodeTable = workspace.collection(edge.data['_to'].split('/')[0])
    return Entity(edge.workspace, edge.graph, edge.data['_from'].split('/')[0], nodeTable.get(edge.data['_to']))


def outgoing(node):
    workspace = db(node.workspace)
    graph = workspace.graph(node.graph)
    edgeTables = [table['edge_collection'] for table in graph.edge_definitions()]
    edges = []
    for table in edgeTables:
        edges += [edge for edge in
                  graph.edges(table, node.data['_id'], direction='out')['edges']]
    return [Entity(node.workspace, node.graph, edge.data['_id'].split('/')[0], edge)
            for edge in edges]


def incoming(node):
    workspace = db(node.workspace)
    graph = workspace.graph(node.graph)
    edgeTables = [table['edge_collection'] for table in graph.edge_definitions()]
    edges = []
    for table in edgeTables:
        edges += [edge for edge in
                  graph.edges(table, node.data['_id'], direction='in')['edges']]
    return [Entity(node.workspace, node.graph, edge.data['_id'].split('/')[0], edge)
            for edge in edges]


def create_table(table, edges, fields=[], primary='_id'):
    workspace = db(table.workspace)
    if workspace.has_collection(table.table):
        coll = workspace.collection(table.table)
    else:
        coll = workspace.create_collection(table.table, edge=edges)
    return coll


def create_type(entity_type, properties):
    workspace = db(entity_type.workspace)
    table = workspace.collection(entity_type.table)
    variety = 'edgeTypes' if table.properties()['edge'] else 'nodeTypes'

    metadata = workspace.collection("_graphs")
    graph_meta = metadata.get(entity_type.graph)
    if graph_meta.get(variety) is None:
        graph_meta[variety] = {}

    graph_meta[variety][entity_type.table] = properties

    if variety == 'edgeTypes':
        possible_nodes = set()
        for node_type in graph_meta.get('nodeTypes', []):
            possible_nodes.add(graph_meta['nodeTypes'][node_type][0]['table'])
        for edge_def in graph_meta['edgeDefinitions']:
            if edge_def['collection'] == entity_type.table:
                break
        else:  # this else is for the for loop! indentation is correct!
            graph_meta['edgeDefinitions'].append({
                'collection': entity_type.table,
                'from': list(possible_nodes),
                'to': list(possible_nodes)
            })
    else:
        for edge_def in graph_meta['edgeDefinitions']:
            if entity_type.table not in edge_def['from']:
                edge_def['from'].push(entity_type.table)
                edge_def['to'].push(entity_type.table)

    metadata.update(graph_meta)
