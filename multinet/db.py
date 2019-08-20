"""Low-level database operations to fulfill GraphQL queries."""
import os

from arango import ArangoClient
from requests.exceptions import ConnectionError

from multinet.types import Row, Entity, EntityType, Cursor


def with_client(fun):
    """Call target function `fun`, passing in an authenticated ArangoClient object."""

    def wrapper(*args, **kwargs):
        kwargs["arango"] = kwargs.get(
            "arango",
            ArangoClient(
                host=os.environ.get("ARANGO_HOST", "localhost"),
                port=int(os.environ.get("ARANGO_PORT", "8529")),
            ),
        )
        return fun(*args, **kwargs)

    return wrapper


@with_client
def check_db(arango=None):
    """Check the database to see if it's alive."""
    try:
        db("_system", arango=arango).has_database("test")
        return True
    except ConnectionError:
        return False


@with_client
def db(name, arango=None):
    """Return a handle for Arango database `name`."""
    return arango.db(
        name, username="root", password=os.environ.get("ARANGO_PASSWORD", "letmein")
    )


@with_client
def create_workspace(name, arango=None):
    """Create a new workspace named `name`."""
    sys = db("_system", arango=arango)
    if not sys.has_database(name):
        sys.create_database(name)


@with_client
def delete_workspace(name, arango=None):
    """Delete the workspace named `name`."""
    sys = db("_system", arango=arango)
    if sys.has_database(name):
        sys.delete_database(name)
        return True
    else:
        return False


@with_client
def get_workspaces(name, arango=None):
    """Return a list of all workspace names."""
    sys = db("_system", arango=arango)
    if name and sys.has_database(name):
        return [name]

    workspaces = sys.databases()
    return [workspace for workspace in workspaces if workspace != "_system"]


@with_client
def workspace_tables(workspace, arango=None):
    """Return a list of all table names in the workspace named `workspace`."""
    space = db(workspace, arango=arango)
    return [
        table["name"]
        for table in space.collections()
        if not table["name"].startswith("_")
    ]


@with_client
def workspace_table(workspace, name, arango=None):
    """Return a specific table named `name` in workspace `workspace`."""
    space = db(workspace, arango=arango)

    tables = filter(lambda g: g["name"] == name, space.collections())
    table = None
    try:
        table = next(tables)
    except StopIteration:
        pass

    return table


@with_client
def workspace_graphs(workspace, arango=None):
    """Return a list of all graph names in workspace `workspace`."""
    space = db(workspace, arango=arango)
    return [graph["name"] for graph in space.graphs()]


@with_client
def workspace_graph(workspace, name, arango=None):
    """Return a specific graph named `name` in workspace `workspace`."""
    space = db(workspace, arango=arango)

    graphs = filter(lambda g: g["name"] == name, space.graphs())
    graph = None
    try:
        graph = next(graphs)
    except StopIteration:
        pass

    return graph


@with_client
def table_fields(query, arango=None):
    """Return a list of column names for `query.table` in `query.workspace`."""
    workspace = db(query.workspace, arango=arango)
    if (
        workspace.has_collection(query.table)
        and workspace.collection(query.table).count() > 0
    ):
        sample = workspace.collection(query.table).random()
        return sample.keys()
    else:
        return []


@with_client
def nodes(query, cursor, arango=None):
    """Return node documents matching a paged node query."""
    workspace = db(query.workspace, arango=arango)
    graph = workspace.graph(query.graph)
    if query.entity_type:
        if query.id:
            result = workspace.collection(query.entity_type).get(query.id)
            if result is not None:
                return (
                    [
                        Entity(
                            query.workspace,
                            query.graph,
                            query.entity_type,
                            workspace.collection(query.entity_type).get(query.id),
                        )
                    ],
                    1,
                )
            else:
                return [], 0
        else:
            tables = [workspace.collection(query.entity_type)]
    else:
        tables = [workspace.collection(nodes) for nodes in graph.vertex_collections()]
    if len(tables) == 0:
        return [], 0

    pages = paged(tables, cursor, query.id)
    return (
        [
            Entity(query.workspace, query.graph, node["_id"].split("/")[0], node)
            for node in pages[0]
        ],
        pages[1],
    )


@with_client
def edges(query, cursor, arango=None):
    """Return edge documents matching a paged edge query."""
    workspace = db(query.workspace, arango=arango)
    graph = workspace.graph(query.graph)
    if query.entity_type:
        if query.id:
            return (
                [
                    Entity(
                        query.workspace,
                        query.graph,
                        query.entity_type,
                        workspace.collection(query.entity_type).get(query.id),
                    )
                ],
                1,
            )
        else:
            tables = [workspace.collection(query.entity_type)]
    else:
        tables = [
            workspace.collection(e["edge_collection"]) for e in graph.edge_definitions()
        ]
    if len(tables) == 0:
        return [], 0

    pages = paged(tables, cursor, query.id)
    return (
        [
            Entity(query.workspace, query.graph, edge["_id"].split("/")[0], edge)
            for edge in pages[0]
        ],
        pages[1],
    )


def paged(tables, cursor, id=None):
    """
    Perform a query against one or more tables, slicing out a page of results.

    `tables` - a list of tables from which to retrieve results.
    `cursor.offset` - an int value giving an offset into the concatentated `tables`.
    `cursor.limit` - the maximum number of documents to return. If set to 0, the
        function will return as many documents as are available.
    `id` - if given, will return only the IDed document, if it exists.
    """
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
def aql_query(workspace, query, arango=None):
    """Perform an AQL query in the given workspace."""
    aql = db(workspace, arango=arango).aql

    cursor = aql.execute(query)
    return cursor


@with_client
def create_graph(workspace, graph, node_tables, edge_table, arango=None):
    """Create a graph named `graph`, defined by`node_tables` and `edge_table`."""
    workspace = db(workspace, arango=arango)
    if workspace.has_graph(graph):
        return False
    else:
        graph = workspace.create_graph(graph)
        graph.create_edge_definition(
            edge_collection=edge_table,
            from_vertex_collections=node_tables,
            to_vertex_collections=node_tables,
        )

        return True


@with_client
def table(query, create=False, arango=None):
    """Return a handle to table `query.table` in workspace `query.workspace`."""
    workspace = db(query.workspace, arango=arango)
    if workspace.has_collection(query.table):
        return workspace.collection(query.table)
    elif create:
        return workspace.create_collection(query.table)
    else:
        return None


@with_client
def graph(graph, create=False, arango=None):
    """Return graph `graph.graph` in workspace `graph.workspace`.

    This function creates the graph if `create` is True and the graph does not
    already exist.
    """
    workspace = db(graph.workspace, arango=arango)
    if workspace.has_graph(graph.graph):
        return workspace.graph(graph.graph)
    elif create:
        return workspace.create_graph(graph.graph)
    else:
        return None


def countRows(query):
    """Give the max number of rows that can come back from query `query`."""
    collection = table(query)
    if query.id:
        return 1
    elif query.search:
        return 0  # to be implemented
    else:
        return collection.count()


def fetchRows(query, cursor):
    """Return all rows in the table referenced by `query`."""
    collection = table(query)
    if query.id:
        row = collection.get(query.id)
        return [Row(query.workspace, query.table, row)] if row else []

    elif query.search:
        return []  # to be implemented
    else:
        return [
            Row(query.workspace, query.table, row)
            for row in collection.all(skip=cursor.offset, limit=cursor.limit)
        ]


def countNodes(query):
    """Return the number of nodes that will come back from `query`."""
    if query.search:
        return 0  # to be implemented
    else:
        return (nodes(query, Cursor(0, 0)))[1]


def fetchNodes(query, cursor):
    """Return all nodes in the table referenced by `query`."""
    if query.search:
        return []  # to be implemented
    else:
        return (nodes(query, cursor))[0]


def countEdges(query):
    """Return the number of edges that will come back from `query`."""
    if query.search:
        return 0  # to be implemented
    else:
        return (edges(query, Cursor(0, 0)))[1]


def fetchEdges(query, cursor):
    """Return all edges in the table referenced by `query`."""
    if query.search:
        return []  # to be implemented
    else:
        return (edges(query, cursor))[0]


def graph_node_types(graph):
    """Return a list of node types existing in graph `graph.graph`."""
    workspace = db(graph.workspace)
    gr = workspace.graph(graph.graph)
    return [
        EntityType(graph.workspace, graph.graph, table)
        for table in gr.vertex_collections()
    ]


def graph_edge_types(graph):
    """Return a list of edge types existing in graph `graph.graph`."""
    workspace = db(graph.workspace)
    gr = workspace.graph(graph.graph)
    return [
        EntityType(graph.workspace, graph.graph, edges["edge_collection"])
        for edges in gr.edge_definitions()
    ]


def type_properties(workspace, graph, table):
    """Return the properties associated with nodes/edges in `graph` and `table`."""
    workspace = db(workspace)
    metadata = workspace.collection("_graphs")
    graph_meta = metadata.get(graph)

    if graph_meta.get("nodeTypes", None) is not None and graph_meta["nodeTypes"].get(
        table, None
    ):
        return graph_meta["nodeTypes"][table]

    if graph_meta.get("edgeTypes", None) is not None and graph_meta["edgeTypes"].get(
        table, None
    ):
        return graph_meta["edgeTypes"][table]


def source(edge):
    """Return the source node of edge `edge`."""
    workspace = db(edge.workspace)
    nodeTable = workspace.collection(edge.data["_from"].split("/")[0])
    return Entity(
        edge.workspace,
        edge.graph,
        edge.data["_from"].split("/")[0],
        nodeTable.get(edge.data["_from"]),
    )


def target(edge):
    """Return the target node of edge `edge`."""
    workspace = db(edge.workspace)
    nodeTable = workspace.collection(edge.data["_to"].split("/")[0])
    return Entity(
        edge.workspace,
        edge.graph,
        edge.data["_from"].split("/")[0],
        nodeTable.get(edge.data["_to"]),
    )


def outgoing(node):
    """Get all target nodes associated with edges for which `node` is a source."""
    workspace = db(node.workspace)
    graph = workspace.graph(node.graph)
    edgeTables = [table["edge_collection"] for table in graph.edge_definitions()]
    edges = []
    for table in edgeTables:
        edges += [
            edge
            for edge in graph.edges(table, node.data["_id"], direction="out")["edges"]
        ]
    return [
        Entity(node.workspace, node.graph, edge["_id"].split("/")[0], edge)
        for edge in edges
    ]


def incoming(node):
    """Get all source nodes associated with edges for which `node` is a target."""
    workspace = db(node.workspace)
    graph = workspace.graph(node.graph)
    edgeTables = [table["edge_collection"] for table in graph.edge_definitions()]
    edges = []
    for table in edgeTables:
        edges += [
            edge
            for edge in graph.edges(table, node.data["_id"], direction="in")["edges"]
        ]
    return [
        Entity(node.workspace, node.graph, edge["_id"].split("/")[0], edge)
        for edge in edges
    ]


def create_table(table, edges, fields=None, primary="_id"):
    """
    Create a table `table.table` in workspace `table.workspace`.

    This function will make the table an edge definition table if `edges` is
    True).
    """
    if fields is None:
        fields = []

    workspace = db(table.workspace)
    if workspace.has_collection(table.table):
        coll = workspace.collection(table.table)
    else:
        coll = workspace.create_collection(table.table, edge=edges)
    return coll


def create_type(entity_type, properties):
    """Create a new edge or node type."""
    workspace = db(entity_type.workspace)
    table = workspace.collection(entity_type.table)
    variety = "edgeTypes" if table.properties()["edge"] else "nodeTypes"

    metadata = workspace.collection("_graphs")
    graph_meta = metadata.get(entity_type.graph)
    if graph_meta.get(variety) is None:
        graph_meta[variety] = {}

    graph_meta[variety][entity_type.table] = properties

    if variety == "edgeTypes":
        possible_nodes = set()
        for node_type in graph_meta.get("nodeTypes", []):
            possible_nodes.add(graph_meta["nodeTypes"][node_type][0]["table"])
        for edge_def in graph_meta["edgeDefinitions"]:
            if edge_def["collection"] == entity_type.table:
                break
        else:  # this else is for the for loop! indentation is correct!
            graph_meta["edgeDefinitions"].append(
                {
                    "collection": entity_type.table,
                    "from": list(possible_nodes),
                    "to": list(possible_nodes),
                }
            )
    else:
        for edge_def in graph_meta["edgeDefinitions"]:
            if entity_type.table not in edge_def["from"]:
                edge_def["from"].push(entity_type.table)
                edge_def["to"].push(entity_type.table)

    metadata.update(graph_meta)
