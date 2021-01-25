"""Utilities for migrations."""
import inspect
from multinet.migrations.base import BaseMigration
from multinet.migrations.types import Migration
from types import ModuleType
from typing import List


# TODO: Add creation and return of `migrations` collection in _system db. This will
# hold a document for each migration that exists. This can be used to check the
# migrations that have been run, what needs to be run, etc.


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
            [
                obj
                for _, obj in inspect.getmembers(module, inspect.isclass)
                if is_migration(obj)
            ]
        )

    return migrations
