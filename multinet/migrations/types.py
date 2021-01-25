"""Migration Types."""
from pydantic import BaseModel
from multinet.migrations.base import BaseMigration
from typing import Type

# This is done because we need to pass the type of BaseMigration around,
# instead of an instance of that class
Migration = Type[BaseMigration]


class MigrationDocument(BaseModel):
    """Describes a migration that's been applied."""

    name: str
    applied: str  # datetime
