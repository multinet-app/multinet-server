"""Low-level database operations."""
import os

from arango import ArangoClient
from requests.exceptions import ConnectionError

from .errors import WorkspaceNotFound, TableNotFound, GraphNotFound, NodeNotFound


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
    sysdb = db("_system", arango=arango)
    if not sysdb.has_database(name):
        sysdb.create_database(name)


@with_client
def delete_workspace(name, arango=None):
    """Delete the workspace named `name`."""
    sysdb = db("_system", arango=arango)
    if sysdb.has_database(name):
        sysdb.delete_database(name)
        return True
    else:
        return False


@with_client
def get_workspace(name, arango=None):
    """Return a single workspace, if it exists."""
    sysdb = db("_system", arango=arango)
    if not sysdb.has_database(name):
        raise WorkspaceNotFound(name)

    return name


@with_client
def get_workspace_db(name, arango=None):
    """Return the Arango database associated with a workspace, if it exists."""
    get_workspace(name, arango=arango)
    return db(name, arango=arango)


@with_client
def get_workspaces(arango=None):
    """Return a list of all workspace names."""
    sysdb = db("_system", arango=arango)
    return [workspace for workspace in sysdb.databases() if workspace != "_system"]


@with_client
def workspace_tables(workspace, fields=True, arango=None):
    """Return a list of all table names in the workspace named `workspace`."""
    space = get_workspace_db(workspace, arango=arango)
    tables = [
        {"table": table["name"]}
        for table in space.collections()
        if not table["name"].startswith("_")
    ]

    if fields:
        for table in tables:
            fields = table_fields(workspace, table["table"])
            table["fields"] = fields

    return tables


@with_client
def workspace_table(workspace, table, offset, limit, arango=None):
    """Return a specific table named `name` in workspace `workspace`."""
    space = get_workspace_db(workspace, arango=arango)
    tables = filter(lambda g: g["name"] == table, space.collections())
    try:
        next(tables)
    except StopIteration:
        raise TableNotFound(table)

    query = f"""
    FOR d in {table}
      LIMIT {offset}, {limit}
      RETURN d
    """

    return aql_query(workspace, query)


@with_client
def graph_node(workspace, graph, table, node, arango=None):
    """Return the data associated with a particular node in a graph."""
    space = get_workspace_db(workspace, arango=arango)
    graphs = filter(lambda g: g["name"] == graph, space.graphs())
    try:
        next(graphs)
    except StopIteration:
        raise GraphNotFound(graph)

    tables = filter(lambda t: t["name"] == table, space.collections())
    try:
        next(tables)
    except StopIteration:
        raise TableNotFound(table)

    query = f"""
    FOR d in {table}
      FILTER d._id == "{table}/{node}"
      RETURN d
    """

    result = aql_query(workspace, query)
    try:
        data = next(result)
    except StopIteration:
        raise NodeNotFound(table, node)

    return {k: data[k] for k in data if k != "_rev"}


@with_client
def workspace_graphs(workspace, arango=None):
    """Return a list of all graph names in workspace `workspace`."""
    space = get_workspace_db(workspace, arango=arango)
    return [graph["name"] for graph in space.graphs()]


@with_client
def workspace_graph(workspace, graph, offset, limit, arango=None):
    """Return a specific graph named `name` in workspace `workspace`."""
    space = get_workspace_db(workspace, arango=arango)
    graphs = filter(lambda g: g["name"] == graph, space.graphs())
    try:
        next(graphs)
    except StopIteration:
        raise GraphNotFound(graph)

    # Get the lists of node and edge tables.
    node_tables = graph_node_tables(workspace, graph, arango=arango)
    edge_tables = graph_edge_tables(workspace, graph, arango=arango)

    # Get the requested node data.
    node_query = f"""
    FOR c in [{", ".join(node_tables)}]
      FOR d in c
        LIMIT {offset}, {limit}
        RETURN d._id
    """

    nodes = aql_query(workspace, node_query, arango=arango)

    # Get the total node count.
    count_query = f"""
    FOR c in [{", ".join(node_tables)}]
      FOR d in c
        COLLECT WITH COUNT INTO count
        RETURN count
    """

    count = aql_query(workspace, count_query, arango=arango)

    return {
        "nodeTables": node_tables,
        "edgeTables": edge_tables,
        "nodes": list(nodes),
        "nodeCount": list(count)[0],
    }

    return graph


@with_client
def table_fields(workspace, table, arango=None):
    """Return a list of column names for `query.table` in `query.workspace`."""
    workspace = db(workspace, arango=arango)
    if workspace.has_collection(table) and workspace.collection(table).count() > 0:
        sample = workspace.collection(table).random()
        return list(sample.keys())
    else:
        return []


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


@with_client
def graph_node_tables(workspace, graph, arango=None):
    """Return the node tables associated with a graph."""
    workspace = db(workspace, arango=arango)
    g = workspace.graph(graph)
    return g.vertex_collections()


@with_client
def graph_edge_tables(workspace, graph, arango=None):
    """Return the edge tables associated with a graph."""
    workspace = db(workspace, arango=arango)
    g = workspace.graph(graph)
    return [d["edge_collection"] for d in g.edge_definitions()]


@with_client
def node_edges(workspace, graph, node, offset, limit, direction, arango=None):
    """Return the edges connected to a node."""
    database = db(workspace, arango=arango)
    graph = database.graph(graph)
    edge_table = graph.edge_definitions()[0]["edge_collection"]

    def query_text(filt):
        return f"""
        FOR e IN {edge_table}
            FILTER {filt}
            LIMIT {offset}, {limit}
            RETURN {{
                "edge": e._id,
                "from": e._from,
                "to": e._to
            }}
        """

    def count_text(filt):
        return f"""
        FOR e IN {edge_table}
            FILTER {filt}
            COLLECT WITH COUNT INTO count
            RETURN count
        """

    if direction == "all":
        filter_clause = f'e._from == "{node}" || e._to == "{node}"'
        query = query_text(filter_clause)
        count = count_text(filter_clause)
    elif direction == "incoming":
        filter_clause = f'e._to == "{node}"'
        query = query_text(filter_clause)
        count = count_text(filter_clause)
    elif direction == "outgoing":
        filter_clause = f'e._from == "{node}"'
        query = query_text(filter_clause)
        count = count_text(filter_clause)
    else:
        raise RuntimeError(f"bad direction argument: {direction}")

    return {
        "edges": list(aql_query(workspace, query)),
        "edgeCount": next(aql_query(workspace, count)),
    }
