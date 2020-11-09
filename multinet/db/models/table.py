"""Operations that deal with tables."""
from __future__ import annotations  # noqa: T484

from arango.collection import StandardCollection
from arango.aql import AQL
from pydantic import ValidationError as PydanticValidationError

from multinet import util
from multinet.db.models import workspace
from multinet.types import (
    EdgeTableProperties,
    ArangoEntityDocument,
    EntityMetadata,
    TableMetadata,
)
from multinet.errors import ServerError, FlaskTuple, InvalidMetadata

from typing import List, Set, Dict, Iterable, Union, Optional


class NotAnEdgeTable(ServerError):
    """Error raised if an edge table is required, but a node table is given."""

    def __init__(self, table: str):
        """Initialize the error with the table name."""
        self.table = table

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return (self.table, "400 Not an Edge Table")


class Table:
    """Tables store tabular data, and are the root of all data storage in Multinet."""

    def __init__(self, name: str, workspace: workspace.Workspace):
        """
        Initialize all Table parameters, but make no requests.

        The `name` parameter is the name of this table.
        The `workspace` parameter is the workspace this table belongs to.
        """
        self.name = name

        # Used for inserting/modifying table metadata
        self.metadata_collection = workspace.entity_metadata_collection()

        # Used for querying table items
        self.handle: StandardCollection = workspace.handle.collection(name)

        # Used for running AQL queries when necessary
        self.aql: AQL = workspace.handle.aql

    def rows(self, offset: Optional[int] = None, limit: Optional[int] = None) -> Dict:
        """Return the desired rows in a table."""
        rows = self.handle.find({}, skip=offset, limit=limit)
        count = self.handle.all().count()

        return {"count": count, "rows": list(rows)}

    def row(self, doc: Union[Dict, str]) -> Optional[Dict]:
        """Return a specific document, or `None` if not present."""
        return self.handle.get(doc)

    def row_count(self) -> int:
        """Return the number of rows in a table."""
        return self.handle.count()

    def keys(self) -> Iterable[str]:
        """Return all the keys in a table."""
        return self.handle.keys()

    def headers(self) -> List[str]:
        """Return the fields present on each row in this table."""
        keys = []
        cur = self.handle.find({}, limit=1)

        if not cur.empty():
            doc: Dict = next(cur)
            keys = list(util.filter_unwanted_keys(doc).keys())

        return keys

    def get_metadata(self) -> ArangoEntityDocument:
        """Retrieve metadata for this table, if it exists."""
        try:
            doc = next(self.metadata_collection.find({"item_id": self.name}, limit=1))
        except StopIteration:
            entity = EntityMetadata(item_id=self.name, table=TableMetadata())

            # Return is just metadata, merge with entity to get full doc
            doc = self.metadata_collection.insert(entity.dict())
            doc.update(entity.dict())

        return ArangoEntityDocument(**doc)

    def set_metadata(self, raw_data: Dict) -> ArangoEntityDocument:
        """Set metadata for this table."""
        try:
            data = TableMetadata(**raw_data)
        except PydanticValidationError:
            raise InvalidMetadata(raw_data)

        entity = self.get_metadata()
        entity.table = data

        new_doc = entity.dict()
        new_doc.update(self.metadata_collection.insert(new_doc, overwrite=True))

        return ArangoEntityDocument(**new_doc)

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
            raise NotAnEdgeTable(self.name)

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
