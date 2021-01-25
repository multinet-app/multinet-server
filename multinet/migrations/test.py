"""Test migration module."""
from multinet.migrations.base import BaseMigration


# This performs a migration successfully
class TestMigrationA(BaseMigration):
    """Test Migration."""

    @staticmethod
    def run() -> None:
        """Run Migration."""
        print("MIGRATION!")
