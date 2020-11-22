"""Test migration module."""
from multinet.migrations.base import Migration


# This performs a migration successfully
class TestMigrationA(Migration):
    """Test Migration."""

    @staticmethod
    def run() -> None:
        """Run Migration."""
        print("MIGRATION!")


# This is not loaded by the migration runner, as
# it does not inherit the base Migration class
class TestMigrationB:
    """Test Migration."""

    pass


# This migration fails, due to not being implemented
class TestMigrationC(Migration):
    """Test Migration."""

    pass
