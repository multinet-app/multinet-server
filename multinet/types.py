"""Custom types for Multinet codebase."""
from typing import Union, List
from typing_extensions import Literal, TypedDict

EdgeDirection = Literal["all", "incoming", "outgoing"]
TableType = Literal["all", "node", "edge"]

CSVUndefinedTables = List[str]
CSVDuplicateKeys = List[str]
NewickDuplicateKeys = List[str]


class CSVUndefinedKeys(TypedDict):
    """Undefined keys referencd in a CSV file."""

    table: str
    keys: List[str]


class CSVInvalidSyntax(TypedDict):
    """Invalid syntax in a CSV file."""

    row: int
    fields: List[str]


class NewickDuplicateEdge(TypedDict):
    """Duplicate edge in a newick file."""

    _from: str
    _to: str
    length: int


ValidationTypes = Literal[
    "graph_creation_undefined_tables",
    "graph_creation_undefined_keys",
    "csv_duplicate_keys",
    "csv_invalid_syntax",
    "csv_unsupported_table",
    "d3_invalid_structure",
    "d3_invalid_link_keys",
    "d3_inconsistent_link_keys",
    "d3_node_duplicates",
    "newick_duplicate_keys",
    "newick_duplicate_edges",
]

ValidationBodyTypes = Union[
    CSVUndefinedKeys,
    List[CSVInvalidSyntax],
    List[NewickDuplicateEdge],
    CSVUndefinedTables,
    CSVDuplicateKeys,
    NewickDuplicateKeys,
]


class ValidationFailedBase(TypedDict):
    """Base type for failed validation."""

    type: ValidationTypes


class ValidatonFailedError(ValidationFailedBase, total=False):
    """Failed validation of some data."""

    body: ValidationBodyTypes
