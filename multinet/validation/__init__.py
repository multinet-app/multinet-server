"""Validation errors for various multinet processes."""
from pydantic import BaseModel
from typing import List, Dict, Any


class ValidationFailure(BaseModel):
    """Base class for any validation errors."""

    def dict(self, **kwargs: Any) -> Dict:  # noqa: A003
        """Overload dict method to inject the `type` field."""
        return {**super().dict(**kwargs), "type": self.schema()["title"]}


# Type only errors
class UnsupportedTable(ValidationFailure):
    """Unsupported table type when uploading a file."""


class UndefinedTable(ValidationFailure):
    """Undefined table referenced in an edge table when creating a graph."""

    table: str


class UndefinedKeys(ValidationFailure):
    """Undefined keys referencd in graph creation."""

    table: str
    keys: List[str]


class DuplicateKey(ValidationFailure):
    """Duplicate key detected when trying to create a table."""

    key: str


class MetadataColumnKeyNotFound(ValidationFailure):
    """A key in the column metadata was not found in the source data."""

    key: str


class IncompatibleMetadata(ValidationFailure):
    """Metadata on an entity is imcompatible with the underlying data."""

    row: int
    column: str
    message: str
