"""Low-level database operations."""
import os
import copy
from functools import lru_cache
from uuid import uuid4

from arango import ArangoClient
from arango.graph import Graph
from arango.database import StandardDatabase
from arango.collection import StandardCollection
from arango.aql import AQL
from arango.cursor import Cursor

from arango.exceptions import (
    DatabaseCreateError,
    EdgeDefinitionCreateError,
    AQLQueryValidateError,
    AQLQueryExecuteError,
)
from requests.exceptions import ConnectionError

from typing import Any, List, Dict, Set, Generator, Optional, cast
from typing_extensions import TypedDict
from multinet.types import (
    EdgeDirection,
    TableType,
    Workspace,
    WorkspaceDocument,
    WorkspacePermissions,
)
from multinet.auth.types import User
from multinet.errors import InternalServerError
from multinet.validation.csv import validate_csv
from multinet import util

from multinet.errors import (
    BadQueryArgument,
    WorkspaceNotFound,
    TableNotFound,
    GraphNotFound,
    NodeNotFound,
    UploadNotFound,
    AlreadyExists,
    GraphCreationError,
    AQLExecutionError,
    AQLValidationError,
    DatabaseCorrupted,
)


# Type definitions.
GraphSpec = TypedDict("GraphSpec", {"nodeTables": List[str], "edgeTable": str})
GraphNodesSpec = TypedDict("GraphNodesSpec", {"count": int, "nodes": List[str]})
GraphEdgesSpec = TypedDict("GraphEdgesSpec", {"count": int, "edges": List[str]})

arango = ArangoClient(
    host=os.environ.get("ARANGO_HOST", "localhost"),
    port=int(os.environ.get("ARANGO_PORT", "8529")),
    protocol=os.environ.get("ARANGO_PROTOCOL", "http"),
)
restricted_keys = {"_rev", "_id"}


def db(name: str) -> StandardDatabase:
    """Return a handle for Arango database `name`."""
    return arango.db(
        name,
        username="root",
        password=os.environ.get("ARANGO_PASSWORD", "letmein"),
        verify=True,
    )


def read_only_db(name: str) -> StandardDatabase:
    """Return a read-only handle for the Arango database `name`."""
    return arango.db(
        name,
        username="readonly",
        password=os.environ.get("ARANGO_READONLY_PASSWORD", "letmein"),
        verify=True,
    )


def check_db() -> bool:
    """Check the database to see if it's alive."""
    try:
        db("_system").has_database("test")
        return True
    except ConnectionError:
        return False


def register_legacy_workspaces() -> None:
    """Add legacy workspaces to the workspace mapping."""
    sysdb = db("_system")
    coll = workspace_mapping_collection()

    system_databases = {"_system", "uploads"}
    databases = {name for name in sysdb.databases() if name not in system_databases}
    registered = {doc["internal"] for doc in coll.all()}

    unregistered = databases - registered
    for workspace in unregistered:
        coll.insert({"name": workspace, "internal": workspace})


# Since this shouldn't ever change while running, this function becomes a singleton
@lru_cache(maxsize=1)
def workspace_mapping_collection() -> StandardCollection:
    """Return the collection used for mapping external to internal workspace names."""
    sysdb = db("_system")

    if not sysdb.has_collection("workspace_mapping"):
        sysdb.create_collection("workspace_mapping")

    return sysdb.collection("workspace_mapping")


# Caches the document that maps an external workspace name to it's internal one
@lru_cache()
def workspace_mapping(name: str) -> Optional[WorkspaceDocument]:
    """
    Get the document containing the workspace mapping for :name: (if it exists).

    Returns the document if found, otherwise returns None.
    """
    coll = workspace_mapping_collection()
    docs = list(coll.find({"name": name}, limit=1))

    if docs:
        return docs[0]

    return None


def workspace_exists(name: str) -> bool:
    """Convinience wrapper for checking if a workspace exists."""
    # Use un-cached underlying function
    return bool(workspace_mapping.__wrapped__(name))


def workspace_exists_internal(name: str) -> bool:
    """Return True if a workspace with the internal name :name: exists."""
    sysdb = db("_system")
    return sysdb.has_database(name)


def create_workspace(name: str, user: User) -> str:
    """Create a new workspace named `name`, owned by `user`."""

    # Bail out with a 409 if the workspace exists already.
    if workspace_exists(name):
        raise AlreadyExists("Workspace", name)

    # Create a workspace mapping document to represent the new workspace. This
    # document (1) sets the external name of the workspace to the requested
    # name, (2) sets the internal name to a random string, and (3) makes the
    # specified user the owner of the workspace.
    ws_doc: Workspace = {
        "name": name,
        "internal": util.generate_arango_workspace_name(),
        "permissions": {
            "owner": user.sub,
            "maintainers": [],
            "writers": [],
            "readers": [],
            "public": False,
        },
    }

    # Attempt to create an Arango database to serve as the workspace itself.
    # There is an astronomically negligible chance that the internal name would
    # clash with an existing internal name; in this case we go full UNIX and
    # just bail out, rather than building in logic to catch it happening.
    try:
        db("_system").create_database(ws_doc["internal"])
    except DatabaseCreateError:
        # Could only happen if there's a name collisison
        raise InternalServerError()

    # Retrieve the workspace mapping collection and log the workspace metadata
    # record.
    coll = workspace_mapping_collection()
    coll.insert(ws_doc)

    # Invalidate the cache for things changed by this function
    workspace_mapping.cache_clear()
    get_workspace_db.cache_clear()

    return name


def rename_workspace(old_name: str, new_name: str) -> None:
    """Rename a workspace."""
    doc = workspace_mapping(old_name)
    if not doc:
        raise WorkspaceNotFound(old_name)

    if workspace_exists(new_name):
        raise AlreadyExists("Workspace", new_name)

    doc["name"] = new_name
    coll = workspace_mapping_collection()
    coll.update(doc)

    # Invalidate the cache for things changed by this function
    get_workspace_db.cache_clear()
    workspace_mapping.cache_clear()


def delete_workspace(name: str) -> None:
    """Delete the workspace named `name`."""
    doc = workspace_mapping(name)
    if not doc:
        raise WorkspaceNotFound(name)

    sysdb = db("_system")
    coll = workspace_mapping_collection()

    sysdb.delete_database(doc["internal"])
    coll.delete(doc["_id"])

    # Invalidate the cache for things changed by this function
    get_workspace_db.cache_clear()
    workspace_mapping.cache_clear()


def get_workspace_metadata(name: str) -> Workspace:
    """Return the metadata for a single workspace, if it exists."""
    if not workspace_exists(name):
        raise WorkspaceNotFound(name)

    # Find the metadata record for the named workspace. If it's not there,
    # something went very wrong, so bail out.
    metadata = workspace_mapping.__wrapped__(name)
    if metadata is None:
        raise DatabaseCorrupted()

    return metadata


def set_workspace_permissions(
    name: str, permissions: WorkspacePermissions
) -> WorkspacePermissions:
    """Update the permissions for a given workspace."""
    doc = copy.deepcopy(get_workspace_metadata(name))
    if doc is None:
        raise DatabaseCorrupted()

    # TODO: Do user object validation once ORM is implemented

    # Disallow changing workspace ownership through this function.
    new_permissions = copy.deepcopy(permissions)
    new_permissions["owner"] = doc["permissions"]["owner"]

    doc["permissions"] = new_permissions
    return_doc = workspace_mapping_collection().get(
        workspace_mapping_collection().update(doc)
    )["permissions"]

    workspace_mapping.cache_clear()

    return cast(WorkspacePermissions, return_doc)


# Caches the reference to the StandardDatabase instance for each workspace
@lru_cache()
def get_workspace_db(name: str, readonly: bool = True) -> StandardDatabase:
    """Return the Arango database associated with a workspace, if it exists."""
    doc = workspace_mapping(name)
    if not doc:
        raise WorkspaceNotFound(name)

    name = doc["internal"]
    return read_only_db(name) if readonly else db(name)


def get_graph_collection(workspace: str, graph: str) -> Graph:
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


def get_workspaces() -> Generator[Workspace, None, None]:
    """Return a list of all workspace names."""
    coll = workspace_mapping_collection()
    return (doc for doc in coll.all())


def workspace_tables(
    workspace: str, table_type: TableType
) -> Generator[str, None, None]:
    """Return a list of all table names in the workspace named `workspace`."""
    space = get_workspace_db(workspace)
    tables = (
        space.collection(table["name"]).properties()
        for table in space.collections()
        if not table["name"].startswith("_")
    )

    def pass_all(x: Dict[str, Any]) -> bool:
        return True

    def is_edge(x: Dict[str, Any]) -> bool:
        return x["edge"]

    def is_node(x: Dict[str, Any]) -> bool:
        return not x["edge"]

    if table_type == "all":
        desired_type = pass_all
    elif table_type == "node":
        desired_type = is_node
    elif table_type == "edge":
        desired_type = is_edge
    else:
        raise BadQueryArgument("type", table_type, ["all", "node", "edge"])

    return (table["name"] for table in tables if desired_type(table))


def workspace_table(workspace: str, table: str, offset: int, limit: int) -> dict:
    """Return a specific table named `name` in workspace `workspace`."""
    get_table_collection(workspace, table)

    count = workspace_table_row_count(workspace, table)
    rows = workspace_table_rows(workspace, table, offset, limit)

    return {"count": count, "rows": list(rows)}


def workspace_table_rows(
    workspace: str, table: str, offset: int, limit: int
) -> Generator[Dict, None, None]:
    """Stream the rows of a table in CSV form."""

    query = f"""
    FOR d in {table}
        LIMIT {offset}, {limit}
        RETURN d
    """

    return aql_query(workspace, query)


def workspace_table_row_count(workspace: str, table: str) -> int:
    """Return the number of rows in a table."""
    count_query = f"""
    RETURN LENGTH({table})
    """
    return next(aql_query(workspace, count_query))


def workspace_table_keys(
    workspace: str, table: str, filter_keys: bool = False
) -> List[str]:
    """Get the keys of a table in a workspace."""

    query = f"""
    FOR d in {table}
        LIMIT 0, 1
        RETURN ATTRIBUTES(d)
    """
    cur = aql_query(workspace, query)

    try:
        keys = next(cur)
    except StopIteration:
        return []

    if filter_keys:
        return [k for k in keys if k not in restricted_keys]

    return keys


def create_aql_table(workspace: str, name: str, aql: str) -> str:
    """Create a new table from an AQL query."""
    db = get_workspace_db(workspace, readonly=True)

    if db.has_collection(name):
        raise AlreadyExists("table", name)

    # In the future, the result of this validation can be
    # used to determine dependencies in virtual tables
    rows = list(_run_aql_query(db.aql, aql))
    validate_csv(rows, "_key", False)

    db = get_workspace_db(workspace, readonly=False)
    coll = db.create_collection(name, sync=True)
    coll.insert_many(rows)

    return name


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
    count: int = next(aql_query(workspace, count_query))

    return {"count": count, "nodes": list(nodes)}


def delete_table(workspace: str, table: str) -> str:
    """Delete a table."""
    space = get_workspace_db(workspace, readonly=False)
    if space.has_collection(table):
        space.delete_collection(table)

    return table


def _run_aql_query(
    aql: AQL, query: str, bind_vars: Optional[Dict[str, Any]] = None
) -> Cursor:
    try:
        aql.validate(query)
        cursor = aql.execute(query, bind_vars=bind_vars)
    except AQLQueryValidateError as e:
        raise AQLValidationError(str(e))
    except AQLQueryExecuteError as e:
        raise AQLExecutionError(str(e))

    return cursor


def aql_query(workspace: str, query: str) -> Cursor:
    """Perform an AQL query in the given workspace."""
    aql = get_workspace_db(workspace, readonly=True).aql
    return _run_aql_query(aql, query)


def create_graph(
    workspace: str,
    graph: str,
    edge_table: str,
    from_vertex_collections: Set[str],
    to_vertex_collections: Set[str],
) -> bool:
    """Create a graph named `graph`, defined by`node_tables` and `edge_table`."""
    space = get_workspace_db(workspace, readonly=False)
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
    space = get_workspace_db(workspace, readonly=False)
    if space.has_graph(graph):
        space.delete_graph(graph)

    return graph


def graph_node_tables(workspace: str, graph: str) -> List[str]:
    """Return the node tables associated with a graph."""
    g = get_graph_collection(workspace, graph)
    return g.vertex_collections()


def graph_edge_table(workspace: str, graph: str) -> str:
    """Return the edge tables associated with a graph."""
    g = get_graph_collection(workspace, graph)
    edge_collections = g.edge_definitions()

    if not edge_collections:
        raise InternalServerError

    return edge_collections[0]["edge_collection"]


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


@lru_cache(maxsize=1)
def uploads_database() -> StandardDatabase:
    """Return the database used for storing multipart upload collections."""
    sysdb = db("_system")
    if not sysdb.has_database("uploads"):
        sysdb.create_database("uploads")
    return db("uploads")


def create_upload_collection() -> str:
    """Insert empty multipart upload temp collection."""
    uploads_db = uploads_database()
    upload_id = f"u-{uuid4().hex}"
    uploads_db.create_collection(upload_id)
    return upload_id


def insert_file_chunk(upload_id: str, sequence: str, chunk: str) -> str:
    """Insert b64-encoded string `chunk` into temporary collection."""
    uploads_db = uploads_database()
    if not uploads_db.has_collection(upload_id):
        raise UploadNotFound(upload_id)

    collection = uploads_db.collection(upload_id)

    if collection.get(sequence) is not None:
        raise AlreadyExists("Upload Chunk", f"{upload_id}/{sequence}")

    collection.insert({sequence: chunk, "_key": sequence})

    return upload_id


def delete_upload_collection(upload_id: str) -> str:
    """Delete a multipart upload collection."""
    uploads_db = uploads_database()

    if not uploads_db.has_collection(upload_id):
        raise UploadNotFound(upload_id)

    uploads_db.delete_collection(upload_id)

    return upload_id
