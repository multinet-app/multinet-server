"""Custom types for Multinet codebase."""
from typing import Union, List
from typing_extensions import Literal, TypedDict

EdgeDirection = Literal["all", "incoming", "outgoing"]
TableType = Literal["all", "node", "edge"]


class NoBodyError(TypedDict):
    """A set of errors that have only a type and no body."""

    type: Literal[
        "csv_unsupported_table",
        "d3_invalid_structure",
        "d3_invalid_link_keys",
        "d3_inconsistent_link_keys",
        "d3_node_duplicates",
    ]


class BasicError(TypedDict):
    """A set of errors that have a body of type List[str]."""

    type: Literal[
        "graph_creation_undefined_tables", "csv_duplicate_keys", "newick_duplicate_keys"
    ]
    body: List[str]


class _GraphUndefinedKeysBody(TypedDict):
    """Undefined keys referencd in graph creation."""

    table: str
    keys: List[str]


class GraphUndefinedKeys(TypedDict):
    """Undefined keys referencd in graph creation."""

    type: Literal["graph_creation_undefined_keys"]
    body: _GraphUndefinedKeysBody


class CSVInvalidRow(TypedDict):
    """Invalid syntax in a CSV file."""

    row: int
    fields: List[str]


class CSVInvalidSyntax(TypedDict):
    """Invalid syntax in a CSV file."""

    type: Literal["csv_invalid_syntax"]
    body: List[CSVInvalidRow]


class NewickDuplicateEdge(TypedDict):
    """The edge which is duplicated."""

    _from: str
    _to: str
    length: int


class NewickDuplicateEdges(TypedDict):
    """Duplicate edge in a newick file."""

    type: Literal["newick_duplicate_edges"]
    body: List[NewickDuplicateEdge]


ValidationFailedError = Union[
    NoBodyError, BasicError, GraphUndefinedKeys, CSVInvalidSyntax, NewickDuplicateEdges
]
