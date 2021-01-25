"""Logic to manage and run migrations."""
import pkgutil
from datetime import datetime
from functools import lru_cache

from arango.collection import StandardCollection
from multinet.db import system_db
from multinet.migrations.util import get_migrations
from multinet.migrations.base import Migration
from multinet.migrations.types import MigrationDocument

from types import ModuleType
from typing import List, Generator


# This function must exist in this file, as it needs access to the `__path__` variable,
# and will infinitely recurse (through pkgutil.walk_packages) if it's placed in a
# sub-module of this module.
@lru_cache()
def get_modules() -> List[ModuleType]:
    """Return all migration modules."""
    modules = [
        loader.find_module(name).load_module(name)
        for loader, name, _ in pkgutil.walk_packages(__path__)  # type: ignore
    ]
    return modules


def migrations_collection() -> StandardCollection:
    """Return the collection that stores previously applied migrations."""

    if not system_db().has_collection("migrations"):
        return system_db(False).create_collection("migrations")

    return system_db(False).collection("migrations")


def store_migration(migration: Migration) -> None:
    """Insert a migration into the migrations collection."""
    now = datetime.now().isoformat()
    doc = MigrationDocument(name=migration.__name__, applied=now)
    migrations_collection().insert(doc.dict())


def get_stored_migrations() -> Generator[MigrationDocument, None, None]:
    """Return all previously run migrations."""
    return (MigrationDocument(**doc) for doc in migrations_collection().all())


def get_unapplied_migrations() -> List[Migration]:
    """Return any migrations which have yet to be applied."""
    modules = get_modules()
    all_migrations = get_migrations(modules)
    applied_migrations = {migration.name for migration in get_stored_migrations()}

    return [
        migration
        for migration in all_migrations
        if migration.__name__ not in applied_migrations
    ]


def run_migrations() -> None:
    """Run all defined migrations."""

    migrations = get_unapplied_migrations()
    if not len(migrations):
        print("All migrations up to date!")
        return

    for migration in migrations:
        migration.run()
        store_migration(migration)

    print(f"Successfully applied {len(migrations)} migrations")
