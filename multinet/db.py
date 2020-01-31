"""Low-level database operations."""
import os

from arango import ArangoClient
from arango.database import StandardDatabase, StandardCollection
from arango.exceptions import DatabaseCreateError, EdgeDefinitionCreateError
from requests.exceptions import ConnectionError

from typing import Callable, Any, Optional, Sequence, List, Set, Generator, Tuple
from mypy_extensions import TypedDict
from multinet.types import EdgeDirection, TableType

from multinet.errors import (
    BadQueryArgument,
    WorkspaceNotFound,
    TableNotFound,
    GraphNotFound,
    NodeNotFound,
    InvalidName,
    AlreadyExists,
    GraphCreationError,
)


# Type definitions.
WorkspaceSpec = TypedDict(
    "WorkspaceSpec",
    {"name": str, "owner": str, "readers": List[str], "writers": List[str]},
)
GraphSpec = TypedDict("GraphSpec", {"nodeTables": List[str], "edgeTable": str})
GraphNodesSpec = TypedDict("GraphNodesSpec", {"count": int, "nodes": List[str]})
GraphEdgesSpec = TypedDict("GraphEdgesSpec", {"count": int, "edges": List[str]})

Arango = ArangoClient(
    host=os.environ.get("ARANGO_HOST", "localhost"),
    port=int(os.environ.get("ARANGO_PORT", "8529")),
)


def db(name: str) -> StandardDatabase:
    """Return a handle for Arango database `name`."""
    return Arango.db(
        name, username="root", password=os.environ.get("ARANGO_PASSWORD", "letmein")
    )


def check_db() -> bool:
    """Check the database to see if it's alive."""
    try:
        db("_system").has_database("test")
        return True
    except ConnectionError:
        return False


def create_workspace(name: str) -> None:
    """Create a new workspace named `name`."""
    sysdb = db("_system")
    if not sysdb.has_database(name):
        try:
            sysdb.create_database(name)
        except DatabaseCreateError:
            raise InvalidName(name)
    else:
        raise AlreadyExists("Workspace", name)


def delete_workspace(name: str) -> None:
    """Delete the workspace named `name`."""
    sysdb = db("_system")
    if sysdb.has_database(name):
        sysdb.delete_database(name)


def get_workspace(name: str) -> WorkspaceSpec:
    """Return a single workspace, if it exists."""
    sysdb = db("_system")
    if not sysdb.has_database(name):
        raise WorkspaceNotFound(name)

    return {"name": name, "owner": "", "readers": [], "writers": []}


def get_workspace_db(name: str) -> StandardDatabase:
    """Return the Arango database associated with a workspace, if it exists."""
    get_workspace(name)
    return db(name)


def get_graph_collection(workspace: str, graph: str) -> StandardCollection:
    """Return the Arango collection associated with a graph, if it exists."""
    space = get_workspace_db(workspace)
    if not space.has_graph(graph):
        raise GraphNotFound(workspace, graph)

    return space.graph(graph)


def get_table_collection(workspace: str, table: str) -> StandardCollection:
    """Return the Arango collection associated with a table, if it exists."""
    space = get_workspace_db(workspace)
    if not space.has_collection(table):
        raise TableNotFound(workspace, table)

    return space.collection(table)


def get_workspaces() -> Generator[str, None, None]:
    """Return a list of all workspace names."""
    sysdb = db("_system")
    return (workspace for workspace in sysdb.databases() if workspace != "_system")


def workspace_tables(
    workspace: str, table_type: TableType
) -> Generator[str, None, None]:
    """Return a list of all table names in the workspace named `workspace`."""

    def edge_table(fields: Sequence[str]) -> bool:
        return "_from" in fields and "_to" in fields

    space = get_workspace_db(workspace)
    tables = (
        (table["name"], edge_table(table_fields(workspace, table["name"])))
        for table in space.collections()
        if not table["name"].startswith("_")
    )

    def pass_all(x: Tuple[Any, bool]) -> bool:
        return True

    def is_edge(x: Tuple[Any, bool]) -> bool:
        return x[1]

    def is_node(x: Tuple[Any, bool]) -> bool:
        return not is_edge(x)

    if table_type == "all":
        desired_type = pass_all
    elif table_type == "node":
        desired_type = is_node
    elif table_type == "edge":
        desired_type = is_edge
    else:
        raise BadQueryArgument("type", table_type, ["all", "node", "edge"])

    return (table[0] for table in tables if desired_type(table))


def workspace_table(workspace: str, table: str, offset: int, limit: int) -> dict:
    """Return a specific table named `name` in workspace `workspace`."""
    get_table_collection(workspace, table)

    query = f"""
    FOR d in {table}
      LIMIT {offset}, {limit}
      RETURN d
    """

    count_query = f"""
    FOR d in {table}
        COLLECT WITH COUNT INTO count
        return count
    """

    count = aql_query(workspace, count_query)
    rows = aql_query(workspace, query)

    return {"count": list(count)[0], "rows": list(rows)}


def graph_node(workspace: str, graph: str, table: str, node: str) -> dict:
    """Return the data associated with a particular node in a graph."""
    space = get_workspace_db(workspace)
    graphs = filter(lambda g: g["name"] == graph, space.graphs())
    try:
        next(graphs)
    except StopIteration:
        raise GraphNotFound(workspace, graph)

    tables = filter(lambda t: t["name"] == table, space.collections())
    try:
        next(tables)
    except StopIteration:
        raise TableNotFound(workspace, table)

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


def workspace_graphs(workspace: str) -> List[str]:
    """Return a list of all graph names in workspace `workspace`."""
    space = get_workspace_db(workspace)
    return [graph["name"] for graph in space.graphs()]


def workspace_graph(workspace: str, graph: str) -> GraphSpec:
    """Return a specific graph named `name` in workspace `workspace`."""
    get_graph_collection(workspace, graph)

    # Get the lists of node and edge tables.
    node_tables = graph_node_tables(workspace, graph)
    edge_table = graph_edge_table(workspace, graph)

    return {"nodeTables": node_tables, "edgeTable": edge_table}


def graph_nodes(workspace: str, graph: str, offset: int, limit: int) -> GraphNodesSpec:
    """Return the nodes of a graph."""
    get_graph_collection(workspace, graph)

    # Get the actual node data.
    node_tables = graph_node_tables(workspace, graph)
    node_query = f"""
    FOR c in [{", ".join(node_tables)}]
      FOR d in c
        LIMIT {offset}, {limit}
        RETURN d
    """
    nodes = aql_query(workspace, node_query)

    # Get the total node count.
    count_query = f"""
    FOR c in [{", ".join(node_tables)}]
      FOR d in c
        COLLECT WITH COUNT INTO count
        RETURN count
    """
    count = aql_query(workspace, count_query)

    return {"count": list(count)[0], "nodes": list(nodes)}


def table_fields(workspace: str, table: str) -> List[str]:
    """Return a list of column names for `query.table` in `query.workspace`."""
    space = db(workspace)
    if space.has_collection(table) and space.collection(table).count() > 0:
        sample = space.collection(table).random()
        return list(sample.keys())
    else:
        return []


def delete_table(workspace: str, table: str) -> str:
    """Delete a table."""
    space = db(workspace)
    if space.has_collection(table):
        space.delete_collection(table)

    return table


def aql_query(workspace: str, query: str) -> Generator[dict, None, None]:
    """Perform an AQL query in the given workspace."""
    aql = db(workspace).aql

    cursor = aql.execute(query)
    return cursor


def create_graph(
    workspace: str,
    graph: str,
    edge_table: str,
    from_vertex_collections: Set[str],
    to_vertex_collections: Set[str],
) -> bool:
    """Create a graph named `graph`, defined by`node_tables` and `edge_table`."""
    space = db(workspace)
    if space.has_graph(graph):
        return False

    try:
        space.create_graph(
            graph,
            edge_definitions=[
                {
                    "edge_collection": edge_table,
                    "from_vertex_collections": list(from_vertex_collections),
                    "to_vertex_collections": list(to_vertex_collections),
                }
            ],
        )
    except EdgeDefinitionCreateError as e:
        raise GraphCreationError(str(e))

    return True


def delete_graph(workspace: str, graph: str) -> str:
    """Delete graph `graph` from workspace `workspace`."""
    space = db(workspace)
    if space.has_graph(graph):
        space.delete_graph(graph)

    return graph


def graph_node_tables(workspace: str, graph: str) -> List[StandardCollection]:
    """Return the node tables associated with a graph."""
    g = get_graph_collection(workspace, graph)
    return g.vertex_collections()


def graph_edge_table(workspace: str, graph: str) -> Optional[StandardCollection]:
    """Return the edge tables associated with a graph."""
    g = get_graph_collection(workspace, graph)
    edge_collections = g.edge_definitions()

    return None if not edge_collections else edge_collections[0]["edge_collection"]


def node_edges(
    workspace: str,
    graph: str,
    table: str,
    node: str,
    offset: int,
    limit: int,
    direction: EdgeDirection,
) -> GraphEdgesSpec:
    """Return the edges connected to a node."""
    get_table_collection(workspace, table)
    edge_table = graph_edge_table(workspace, graph)

    def query_text(filt: str) -> str:
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

    def count_text(filt: str) -> str:
        return f"""
        FOR e IN {edge_table}
            FILTER {filt}
            COLLECT WITH COUNT INTO count
            RETURN count
        """

    if direction == "all":
        filter_clause = f'e._from == "{table}/{node}" || e._to == "{table}/{node}"'
    elif direction == "incoming":
        filter_clause = f'e._to == "{table}/{node}"'
    elif direction == "outgoing":
        filter_clause = f'e._from == "{table}/{node}"'
    else:
        raise BadQueryArgument("direction", direction, ["all", "incoming", "outgoing"])

    query = query_text(filter_clause)
    count = count_text(filter_clause)

    return {
        "edges": list(aql_query(workspace, query)),
        "count": next(aql_query(workspace, count)),
    }
