"""Operations that deal with tables."""
from __future__ import annotations  # noqa: T484
from arango.collection import StandardCollection
from arango.aql import AQL

from multinet import util
from multinet.types import EdgeTableProperties
from multinet.errors import InternalServerError

from typing import List, Set, Dict, Iterable, Union, Optional


class Table:
    """Table."""

    def __init__(self, name: str, workspace: str, handle: StandardCollection, aql: AQL):
        """Init Table class."""
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

    def row_fields(self, filter_keys: bool = False) -> List[str]:
        """Return a the fields present on each row in this table."""
        keys = []
        cur = self.handle.find({}, limit=1)

        # TODO: Determine what should happen if cur is empty
        if not cur.empty():
            doc: Dict = next(cur)

            if filter_keys:
                keys = list(util.filter_unwanted_keys(doc).keys())
            else:
                keys = list(doc.keys())

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

    # This may be a reason to split Table up into EdgeTable and NodeTable
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
