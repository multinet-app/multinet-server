"""Utilities for migrations."""
import inspect
from datetime import datetime
from arango.collection import StandardCollection
from multinet.db import system_db
from multinet.migrations.base import BaseMigration
from multinet.migrations.types import Migration, MigrationDocument
from types import ModuleType
from typing import List, Generator


def is_migration(cls: type) -> bool:
    """
    Return true if the supplied class is an implemented Migration.

    Only strict subclasses of the base Migration class are considered valid.
    """
    return issubclass(cls, BaseMigration) and cls != BaseMigration


def get_migrations(modules: List[ModuleType]) -> List[Migration]:
    """Return all migrations from the supplied list of modules."""

    migrations: List[Migration] = []
    for module in modules:
        migrations.extend(
            obj
            for _, obj in inspect.getmembers(module, inspect.isclass)
            if is_migration(obj)
        )

    return migrations


def migrations_collection() -> StandardCollection:
    """Return the collection that stores previously applied migrations."""

    if not system_db().has_collection("migrations"):
        return system_db(readonly=False).create_collection("migrations")

    return system_db(readonly=False).collection("migrations")


def store_migration(migration: Migration) -> None:
    """Insert a migration into the migrations collection."""
    now = datetime.now().isoformat()
    doc = MigrationDocument(name=migration.__name__, applied=now)
    migrations_collection().insert(doc.dict())


def get_stored_migrations() -> Generator[MigrationDocument, None, None]:
    """Return all previously run migrations."""
    return (MigrationDocument(**doc) for doc in migrations_collection().all())
