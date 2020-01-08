"""Script that populates initial data into the multinet backend."""

import csv
import click
from hashlib import md5

from pathlib import Path
from typing import Tuple, List

from multinet.db import create_workspace, get_workspace_db, delete_workspace
from multinet.errors import WorkspaceNotFound

WORKSPACE_NAME = f"example_data_{md5('test'.encode()).digest().hex()}"
NODE_TABLE_KEY = "node"
EDGE_TABLE_KEY = "edge"


def determine_table_types(paths) -> Tuple:
    """
    Given several csv file Path objects, determines the edge table and node table.

    The returned tuple contains the types of each path (respecting order).
    If the format of one of the paths isn't consistent an error is thrown.
    """

    def is_edge_table(header: List) -> bool:
        if "_from" in header and "_to" in header:
            return True
        return False

    def is_node_table(header: List) -> bool:
        if "_key" in header:
            return True
        return False

    types = []

    for path in paths:
        with path.open(mode="r") as in_file:
            header = in_file.readline().strip()
            columns = header.split(",")

            if is_edge_table(columns):
                types.append(EDGE_TABLE_KEY)

            elif is_node_table(columns):
                types.append(NODE_TABLE_KEY)
            else:
                raise Exception(
                    f"Path {path} is neither a node table nor an edge table."
                )

    return tuple(types)


@click.group()
def cli():
    """Script that helps with bootstrapping example data."""
    pass


@cli.command("populate")
def populate():
    """Populate arangodb with example data."""
    data_dir = Path(__file__).absolute().parents[1] / "data"

    for path in data_dir.iterdir():
        dataset_name = path.name
        print(f'Processing dataset "{dataset_name}"')

        files = tuple(path.glob("*.csv"))
        tables_types = determine_table_types(files)
        tables = zip(files, tables_types)

        try:
            workspace = get_workspace_db(WORKSPACE_NAME)
        except WorkspaceNotFound:
            create_workspace(WORKSPACE_NAME)
            workspace = get_workspace_db(WORKSPACE_NAME)

        for file, table_type in tables:
            table_name = file.stem
            edge = table_type == EDGE_TABLE_KEY

            with file.open(mode="r") as csv_file:
                rows = list(csv.DictReader(csv_file))

            if workspace.has_collection(table_name):
                print(f'\tTable "{table_name}" already exists, skipping...')
            else:
                coll = workspace.create_collection(table_name, edge=edge)
                inserted = len(coll.insert_many(rows))

                print(
                    f'\tInserted {inserted} rows into {table_type} table "{table_name}"'
                )


@cli.command("clean")
def clean():
    """Remove example data."""
    delete_workspace(WORKSPACE_NAME)
    print(f"Deleted workspace {WORKSPACE_NAME}")


if __name__ == "__main__":
    cli()
