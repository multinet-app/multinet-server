"""Low-level database operations."""
import os

from arango import ArangoClient  # type: ignore
from arango.database import StandardDatabase, StandardCollection  # type: ignore
from arango.exceptions import DatabaseCreateError  # type: ignore
from requests.exceptions import ConnectionError

from typing import Callable, Any, Optional, Sequence, List, Generator, Tuple
from typing_extensions import Literal
from mypy_extensions import TypedDict

from .errors import (
    BadQueryArgument,
    WorkspaceNotFound,
    TableNotFound,
    GraphNotFound,
    NodeNotFound,
    InvalidName,
    AlreadyExists,
)


# Type definitions.
WorkspaceSpec = TypedDict(
    "WorkspaceSpec",
    {"name": str, "owner": str, "readers": List[str], "writers": List[str]},
)
GraphSpec = TypedDict("GraphSpec", {"nodeTables": List[str], "edgeTable": str})
GraphNodesSpec = TypedDict("GraphNodesSpec", {"count": int, "nodes": List[str]})
GraphEdgesSpec = TypedDict("GraphEdgesSpec", {"count": int, "edges": List[str]})
TableType = Literal["all", "node", "edge"]
DirectionType = Literal["all", "incoming", "outgoing"]


def with_client(fun: Callable) -> Callable:
    """Call target function `fun`, passing in an authenticated ArangoClient object."""

    def wrapper(*args: Any, **kwargs: Any) -> Callable:
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
def check_db(arango: ArangoClient) -> bool:
    """Check the database to see if it's alive."""
    try:
        db("_system", arango=arango).has_database("test")
        return True
    except ConnectionError:
        return False


@with_client
def db(name: str, arango: ArangoClient) -> StandardDatabase:
    """Return a handle for Arango database `name`."""
    return arango.db(
        name, username="root", password=os.environ.get("ARANGO_PASSWORD", "letmein")
    )


@with_client
def create_workspace(name: str, arango: ArangoClient) -> None:
    """Create a new workspace named `name`."""
    sysdb = db("_system", arango=arango)
    if not sysdb.has_database(name):
        try:
            sysdb.create_database(name)
        except DatabaseCreateError:
            raise InvalidName(name)
    else:
        raise AlreadyExists("Workspace", name)


@with_client
def delete_workspace(name: str, arango: ArangoClient) -> None:
    """Delete the workspace named `name`."""
    sysdb = db("_system", arango=arango)
    if sysdb.has_database(name):
        sysdb.delete_database(name)


@with_client
def get_workspace(name: str, arango: ArangoClient) -> WorkspaceSpec:
    """Return a single workspace, if it exists."""
    sysdb = db("_system", arango=arango)
    if not sysdb.has_database(name):
        raise WorkspaceNotFound(name)

    return {"name": name, "owner": "", "readers": [], "writers": []}


@with_client
def get_workspace_db(name: str, arango: ArangoClient) -> StandardDatabase:
    """Return the Arango database associated with a workspace, if it exists."""
    get_workspace(name, arango=arango)
    return db(name, arango=arango)


@with_client
def get_graph_collection(
    workspace: str, graph: str, arango: ArangoClient
) -> StandardCollection:
    """Return the Arango collection associated with a graph, if it exists."""
    space = get_workspace_db(workspace, arango=arango)
    if not space.has_graph(graph):
        raise GraphNotFound(workspace, graph)

    return space.graph(graph)


@with_client
def get_table_collection(
    workspace: str, table: str, arango: ArangoClient
) -> StandardCollection:
    """Return the Arango collection associated with a table, if it exists."""
    space = get_workspace_db(workspace, arango=arango)
    if not space.has_collection(table):
        raise TableNotFound(workspace, table)

    return space.collection(table)


@with_client
def get_workspaces(arango: ArangoClient) -> Generator[str, None, None]:
    """Return a list of all workspace names."""
    sysdb = db("_system", arango=arango)
    return (workspace for workspace in sysdb.databases() if workspace != "_system")


@with_client
def workspace_tables(
    workspace: str, type: TableType, arango: ArangoClient
) -> Generator[str, None, None]:
    """Return a list of all table names in the workspace named `workspace`."""

    def edge_table(fields: Sequence[str]) -> bool:
        return "_from" in fields and "_to" in fields

    space = get_workspace_db(workspace, arango=arango)
    tables = (
        (
            table["name"],
            edge_table(table_fields(workspace, table["name"], arango=arango)),
        )
        for table in space.collections()
        if not table["name"].startswith("_")
    )

    def pass_all(x: Tuple[Any, bool]) -> bool:
        return True

    def is_edge(x: Tuple[Any, bool]) -> bool:
        return x[1]

    def is_node(x: Tuple[Any, bool]) -> bool:
        return not is_edge(x)

    if type == "all":
        desired_type = pass_all
    elif type == "node":
        desired_type = is_node
    elif type == "edge":
        desired_type = is_edge
    else:
        raise BadQueryArgument("type", type, ["all", "node", "edge"])

    return (table[0] for table in tables if desired_type(table))


@with_client
def workspace_table(
    workspace: str, table: str, offset: int, limit: int, arango: ArangoClient
) -> Generator[dict, None, None]:
    """Return a specific table named `name` in workspace `workspace`."""
    get_table_collection(workspace, table, arango=arango)

    query = f"""
    FOR d in {table}
      LIMIT {offset}, {limit}
      RETURN d
    """

    return aql_query(workspace, query)


@with_client
def graph_node(
    workspace: str, graph: str, table: str, node: str, arango: ArangoClient
) -> dict:
    """Return the data associated with a particular node in a graph."""
    space = get_workspace_db(workspace, arango=arango)
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


@with_client
def workspace_graphs(workspace: str, arango: ArangoClient) -> List[str]:
    """Return a list of all graph names in workspace `workspace`."""
    space = get_workspace_db(workspace, arango=arango)
    return [graph["name"] for graph in space.graphs()]


@with_client
def workspace_graph(workspace: str, graph: str, arango: ArangoClient) -> GraphSpec:
    """Return a specific graph named `name` in workspace `workspace`."""
    get_graph_collection(workspace, graph)

    # Get the lists of node and edge tables.
    node_tables = graph_node_tables(workspace, graph, arango=arango)
    edge_table = graph_edge_table(workspace, graph, arango=arango)

    return {"nodeTables": node_tables, "edgeTable": edge_table}


@with_client
def graph_nodes(
    workspace: str, graph: str, offset: int, limit: int, arango: ArangoClient
) -> GraphNodesSpec:
    """Return the nodes of a graph."""
    get_graph_collection(workspace, graph)

    # Get the actual node data.
    node_tables = graph_node_tables(workspace, graph, arango=arango)
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

    return {"count": list(count)[0], "nodes": list(nodes)}


@with_client
def table_fields(workspace: str, table: str, arango: ArangoClient) -> List[str]:
    """Return a list of column names for `query.table` in `query.workspace`."""
    space = db(workspace, arango=arango)
    if space.has_collection(table) and space.collection(table).count() > 0:
        sample = space.collection(table).random()
        return list(sample.keys())
    else:
        return []


@with_client
def aql_query(
    workspace: str, query: str, arango: ArangoClient
) -> Generator[dict, None, None]:
    """Perform an AQL query in the given workspace."""
    aql = db(workspace, arango=arango).aql

    cursor = aql.execute(query)
    return cursor


@with_client
def create_graph(
    workspace: str,
    graph: str,
    node_tables: List[str],
    edge_table: str,
    arango: ArangoClient,
) -> bool:
    """Create a graph named `graph`, defined by`node_tables` and `edge_table`."""
    space = db(workspace, arango=arango)
    if space.has_graph(graph):
        return False
    else:
        g = space.create_graph(graph)
        g.create_edge_definition(
            edge_collection=edge_table,
            from_vertex_collections=node_tables,
            to_vertex_collections=node_tables,
        )

        return True


@with_client
def graph_node_tables(
    workspace: str, graph: str, arango: ArangoClient
) -> List[StandardCollection]:
    """Return the node tables associated with a graph."""
    g = get_graph_collection(workspace, graph)
    return g.vertex_collections()


@with_client
def graph_edge_table(
    workspace: str, graph: str, arango: ArangoClient
) -> Optional[StandardCollection]:
    """Return the edge tables associated with a graph."""
    g = get_graph_collection(workspace, graph)
    edge_collections = g.edge_definitions()

    return None if not edge_collections else edge_collections[0]["edge_collection"]


@with_client
def node_edges(
    workspace: str,
    graph: str,
    table: str,
    node: str,
    offset: int,
    limit: int,
    direction: DirectionType,
    arango: ArangoClient,
) -> GraphEdgesSpec:
    """Return the edges connected to a node."""
    get_table_collection(workspace, table)
    edge_table = graph_edge_table(workspace, graph, arango=arango)

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
        filter_clause = f'e._from == "{table}/{node}" || e._to == "{node}"'
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
