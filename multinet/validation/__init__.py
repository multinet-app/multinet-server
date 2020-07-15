"""Validation errors for various multinet processes."""
from typing import List, Dict
from dataclasses import dataclass, asdict


@dataclass
class ValidationFailure:
    """Base class for any validation errors."""

    def asdict(self) -> Dict:
        """Return a dict representation of the Validation Failure."""
        d = asdict(self)
        d["type"] = type(self).__name__
        return d


# Type only errors
@dataclass
class UnsupportedTable(ValidationFailure):
    """Unsupported table type when uploading a file."""


@dataclass
class UndefinedTable(ValidationFailure):
    """Undefined table referenced in an edge table when creating a graph."""

    table: str


@dataclass
class UndefinedKeys(ValidationFailure):
    """Undefined keys referencd in graph creation."""

    table: str
    keys: List[str]


@dataclass
class DuplicateKey(ValidationFailure):
    """Duplicate key detected when trying to create a table."""

    key: str
