"""Test migration module."""
from multinet.migrations.base import Migration


# This performs a migration successfully
class TestMigrationA(Migration):
    """Test Migration."""

    @staticmethod
    def run() -> None:
        """Run Migration."""
        print("MIGRATION!")
