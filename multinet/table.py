"""Operations that deal with tables."""
from __future__ import annotations  # noqa: T484
from arango.collection import StandardCollection
from arango.aql import AQL

from multinet import util
from multinet.types import EdgeTableProperties
from multinet.errors import InternalServerError

from typing import List, Set, Dict, Iterable, Union, Optional


class Table:
    """Tables store tabular data, and are the root of all data storage in Multinet."""

    def __init__(self, name: str, workspace: str, handle: StandardCollection, aql: AQL):
        """
        Initialize all Table parameters, but make no requests.

        The `workspace` parameter is the name of the workspace this table belongs to.

        The `handle` parameter is the handle to the arangodb collection for which this
        class instance is associated.

        The `aql` parameter is the AQL handle of the creating Workspace, so that this
        class may make AQL requests when necessary.
        """
        self.name = name
        self.workspace = workspace
        self.handle = handle
        self.aql = aql

    def rows(self, offset: Optional[int] = None, limit: Optional[int] = None) -> Dict:
        """Return the desired rows in a table."""
        rows = self.handle.find({}, skip=offset, limit=limit)
        count = self.handle.all().count()

        return {"count": count, "rows": list(rows)}

    def row(self, doc: Union[Dict, str]) -> Union[Dict, None]:
        """Return a specific document, or `None` if not present."""
        return self.handle.get(doc)

    def row_count(self) -> int:
        """Return the number of rows in a table."""
        return self.handle.count()

    def keys(self) -> Iterable[str]:
        """Return all the keys in a table."""
        return self.handle.keys()

    def headers(self) -> List[str]:
        """Return a the fields present on each row in this table."""
        keys = []
        cur = self.handle.find({}, limit=1)

        # TODO: Determine what should happen if cur is empty
        if not cur.empty():
            doc: Dict = next(cur)
            keys = list(util.filter_unwanted_keys(doc).keys())

        return keys

    def rename(self, new_name: str) -> None:
        """Rename a table."""
        self.handle.rename(new_name)
        self.name = new_name

    def insert(self, rows: List[Dict]) -> List[Dict]:
        """
        Insert rows into this table.

        Returns the metadata from the documents inserted.
        """
        return self.handle.insert_many(rows)

    def edge_properties(self) -> EdgeTableProperties:
        """
        Return extracted information about an edge table.

        Extracts 3 pieces of data from an edge table.

        table_keys: A map of all referenced tables to the specific keys referenced.
        from_tables: A set containing the tables referenced in the _from column.
        to_tables: A set containing the tables referenced in the _to column.

        Raises an InternalServerError if this table is not an edge table.
        """
        props = self.handle.properties()
        if not props["edge"]:
            raise InternalServerError(f"Table {self.name} is not an edge table.")

        edges = self.rows()["rows"]

        tables_to_keys: Dict[str, Set[str]] = {}
        from_tables = set()
        to_tables = set()

        for edge in edges:
            from_node, to_node = edge["_from"].split("/"), edge["_to"].split("/")
            from_tables.add(from_node[0])
            to_tables.add(to_node[0])

            for table, key in (from_node, to_node):
                if table in tables_to_keys:
                    tables_to_keys[table].add(key)
                else:
                    tables_to_keys[table] = {key}

        return {
            "table_keys": tables_to_keys,
            "from_tables": from_tables,
            "to_tables": to_tables,
        }
