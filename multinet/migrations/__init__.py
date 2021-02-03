"""Logic to manage and run migrations."""
import pkgutil
import click
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


def run_migrations() -> bool:
    """Run all defined migrations."""

    delimiter = f"{'-' * 10}\n"
    migrations = get_unapplied_migrations()
    if not len(migrations):
        click.secho("All migrations up to date!", fg="green", bold=True)
        return True

    click.secho(f"Applying Migrations...")

    success = 0
    for migration in migrations:
        name = migration.__name__
        failed = False

        try:
            migration.run()
        except Exception as e:
            failed = True
            click.secho(
                f"{delimiter}Migration {name} raised {type(e)} with message: \n\n{e}",
                fg="red",
                bold=True,
                err=True,
            )

        if not failed:
            click.secho(f"Migration {name} applied successfully", fg="green", bold=True)
            store_migration(migration)
            success += 1

    click.echo(
        f"{delimiter}Successfully applied {success}/{len(migrations)} migrations"
    )
    if success == len(migrations):
        return True

    return False
