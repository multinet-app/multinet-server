"""Operations that deal with graphs."""

from arango.graph import Graph as ArangoGraph
from arango.aql import AQL
from arango.exceptions import DocumentGetError

from multinet.types import EdgeDirection
from multinet.errors import TableNotFound, NodeNotFound

from typing import Any, Dict, Iterable, Optional


edge_direction_map = {"all": "any", "incoming": "inbound", "outgoing": "outbound"}


class Graph:
    """Graphs link data between tables in Multinet."""

    def __init__(self, name: str, workspace: str, handle: ArangoGraph, aql: AQL):
        """
        Initialize all Graph parameters, but make no requests.

        The `workspace` parameter is the name of the workspace this graph belongs to.

        The `handle` parameter is the handle to the arangodb graph for which this
        class instance is associated.

        The `aql` parameter is the AQL handle of the creating Workspace, so that this
        class may make AQL requests when necessary.
        """
        self.name = name
        self.workspace = workspace
        self.handle = handle
        self.aql = aql

    def nodes(
        self, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Return nodes in this graph."""
        coll_names = self.handle.vertex_collections()

        result_set_size = 0
        query_size = 0
        total_nodes = []

        for coll_name in coll_names:
            coll = self.handle.vertex_collection(coll_name)
            result_set_size += coll.all().count()

            if limit is None or query_size < limit:
                remaining_limit = min(limit, limit - query_size) if limit else None
                cur = coll.all(skip=offset, limit=remaining_limit)

                query_size += cur.count()
                total_nodes.extend(list(cur))

        # Because we're embedding a list in a dictionary, we can't take full advantage
        # of cursors. If this isn't required in the future, this may be more efficient
        return {"count": result_set_size, "nodes": list(total_nodes)}

    def node_tables(self) -> Iterable[str]:
        """Return all node tables in this graph."""
        return self.handle.vertex_collections()

    def edge_table(self) -> str:
        """Return the edge table of this graph."""
        edge_defs = self.handle.edge_definitions()

        # Currently assume one edge definition per graph
        return edge_defs[0]["edge_collection"]

    def node_attributes(self, table: str, node: str) -> Dict:
        """Return the attributes of the document with an ID of `table`/`node`."""
        node_id = f"{table}/{node}"

        try:
            res = self.handle.vertex(node_id)
        except DocumentGetError:
            raise TableNotFound(self.workspace, table)

        if res is None:
            raise NodeNotFound(table, node)

        if "_rev" in res:
            del res["_rev"]

        return res

    def node_edges(
        self,
        table: str,
        node: str,
        direction: EdgeDirection = "all",
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict:
        """Return the edges of the node `node` from table `table`."""
        node_id = f"{table}/{node}"
        edge_table = self.edge_table()

        query_direction = edge_direction_map[direction]
        query_filter = f'e._from == "{node_id}" || e._to == "{node_id}"'
        if query_direction == "inbound":
            query_filter = f'e._to == "{node_id}"'
        elif query_direction == "outbound":
            query_filter = f'e._from == "{node_id}"'

        query = f"""
        FOR e IN {edge_table}
            FILTER {query_filter}
            LIMIT {offset}, {limit}
            RETURN {{
                "edge": e._id,
                "from": e._from,
                "to": e._to
            }}
        """

        count_query = f"""
        FOR e IN {edge_table}
            FILTER {query_filter}
            COLLECT WITH COUNT INTO count
            RETURN count
        """

        query_cur = self.aql.execute(query)
        count_cur = self.aql.execute(count_query)

        return {"count": next(count_cur), "edges": list(query_cur)}
