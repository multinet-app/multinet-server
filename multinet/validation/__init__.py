"""Validation errors for various multinet processes."""
from pydantic import BaseModel
from typing import List, Dict


class ValidationFailure(BaseModel):
    """Base class for any validation errors."""

    def validation_dict(self) -> Dict:
        """Return a dict representation of the Validation Failure."""
        return {**self.dict(), "type": self.schema()["title"]}


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
