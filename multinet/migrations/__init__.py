"""Logic to manage and run migrations."""
import pkgutil
from functools import lru_cache
from multinet.migrations.util import get_migrations
from multinet.migrations.base import Migration

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


# TODO
def get_unapplied_migrations() -> List[Migration]:
    """Return any migrations which have yet to be applied."""
    pass


def run_migrations() -> None:
    """Run all defined migrations."""

    # TODO: Store migrations that have been run already in the database,
    # and check before running any
    modules = get_modules()
    migrations = get_migrations(modules)
    for migration in migrations:
        migration.run()
