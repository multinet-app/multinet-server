"""Custom types for Multinet codebase."""
from typing import List
from typing_extensions import Literal, TypedDict

from dataclasses import dataclass

EdgeDirection = Literal["all", "incoming", "outgoing"]
TableType = Literal["all", "node", "edge"]


@dataclass
class ValidationFailure:
    """Base class for any validation errors."""


# Type only errors
@dataclass
class UnsupportedTable(ValidationFailure):
    """Unsupported table type when uploading a file."""


@dataclass
class D3InvalidStructure(ValidationFailure):
    """Invalid structure in a D3 JSON file."""


@dataclass
class D3InvalidLinkKeys(ValidationFailure):
    """Invalid link keys in a D3 JSON file."""


@dataclass
class D3InconsistentLinkKeys(ValidationFailure):
    """Inconsistent link keys in a D3 JSON file."""


@dataclass
class D3NodeDuplicates(ValidationFailure):
    """Duplicate nodes in a D3 JSON file."""


# Basic Errors
@dataclass
class BasicError(ValidationFailure):
    """Class for errors who have a basic body type."""

    body: List[str]


@dataclass
class GraphCreationUndefinedTables(BasicError):
    """Undefined tables referenced in an edge table when creating a graph."""


@dataclass
class DuplicateKeys(BasicError):
    """Duplicate keys detected when trying to create a table."""


@dataclass
class GraphCreationUndefinedKeys(ValidationFailure):
    """Undefined keys referencd in graph creation."""

    table: str
    keys: List[str]


class CSVInvalidRow(TypedDict):
    """Invalid syntax in a CSV file."""

    row: int
    fields: List[str]


@dataclass
class CSVInvalidSyntax(ValidationFailure):
    """Invalid syntax in a CSV file."""

    body: List[CSVInvalidRow]


class NewickDuplicateEdge(TypedDict):
    """The edge which is duplicated."""

    _from: str
    _to: str
    length: int


@dataclass
class NewickDuplicateEdges(ValidationFailure):
    """Duplicate edge in a newick file."""

    body: List[NewickDuplicateEdge]
