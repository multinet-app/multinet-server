"""Logic to manage and run migrations."""
import pkgutil
from functools import lru_cache

from multinet.migrations.types import Migration
from multinet.migrations.util import (
    get_migrations,
    get_stored_migrations,
    store_migration,
)

from types import ModuleType
from typing import List


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
    if not migrations:
        print("All migrations up to date!")
        return

    for migration in migrations:
        migration.run()
        store_migration(migration)

    print(f"Successfully applied {len(migrations)} migrations")
