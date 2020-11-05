"""Custom types for Multinet codebase."""
from pydantic import BaseModel, Field
from typing import List, Dict, Set, Optional, Any
from typing_extensions import Literal, TypedDict

EdgeDirection = Literal["all", "incoming", "outgoing"]

TableType = Literal["node", "edge"]
UnionTableType = Literal["all", TableType]
ColumnType = Literal["label", "boolean", "category", "number", "date"]


class ColumnMetadata(BaseModel):
    """Metadata for a table column."""

    key: str
    type: ColumnType


class TableMetadata(BaseModel):
    """Metadata for a table."""

    columns: List[ColumnMetadata] = Field(default_factory=list)


class GraphMetadata(BaseModel):
    """Metadata for a graph."""


class EntityMetadata(BaseModel):
    """Metadata for a table or graph."""

    item_id: str
    table: Optional[TableMetadata]
    graph: Optional[GraphMetadata]


class ArangoEntityDocument(EntityMetadata):
    """An entity metadata document with arangodb metadata."""

    def dict(self, **kwargs: Any) -> Dict:  # noqa: A003
        """
        Overload existing dict function to use alias for dict serialization.

        Variable names with leading underscores aren't treated normally, and need to be
        aliased to be properly specified. Since pydantic doesn't serialize with alias
        names by default, this overload is needed.
        """

        kwargs["by_alias"] = True
        return super().dict(**kwargs)

    id: str = Field(alias="_id")
    key: str = Field(alias="_key")
    rev: str = Field(alias="_rev")

    class Config:
        """Model config."""

        allow_population_by_field_name = True


class EdgeTableProperties(TypedDict):
    """Describes gathered information about an edge table."""

    # Dictionary mapping all referenced tables to the referenced keys within that table
    table_keys: Dict[str, Set[str]]

    # Keeps track of which tables are referenced in the _from column
    from_tables: Set[str]

    # Keeps track of which tables are referenced in the _to column
    to_tables: Set[str]
