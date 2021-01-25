"""Migration Types."""
from pydantic import BaseModel


class MigrationDocument(BaseModel):
    """Describes a migration that's been applied."""

    name: str
    applied: str  # datetime
