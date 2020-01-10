"""Custom types for Multinet codebase."""
from typing import Dict, Set
from typing_extensions import Literal, TypedDict


EdgeDirection = Literal["all", "incoming", "outgoing"]
TableType = Literal["all", "node", "edge"]


class EdgeTableProperties(TypedDict):
    """Describes gathered information about an edge table."""

    table_keys: Dict[str, Set[str]]
    from_tables: Set[str]
    to_tables: Set[str]
