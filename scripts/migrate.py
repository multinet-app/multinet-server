"""This script runs multinet migrations."""
import sys
from multinet.migrations import run_migrations

if __name__ == "__main__":
    sys.exit(not run_migrations())
