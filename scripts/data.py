"""Script that populates initial data into the multinet backend."""

import csv
from pathlib import Path
from typing import Tuple, List

from multinet.db import create_workspace, get_workspace_db
from multinet.errors import WorkspaceNotFound

WORKSPACE_NAME = "example_data"


def determine_table_types(paths) -> Tuple:
    """
    Given 2 csv file names, determines the edge table and node table.

    The format of the returned tuple is (Node Table, Edge Table).
    If the format of the 2 files isn't relatively consistent, an Exception is thrown.
    """

    if len(paths) != 2:
        raise Exception(
            f"Directory {paths[0].parents[1]} must contain exactly 2 csv files."
        )

    def is_edge_table(header: List) -> bool:
        if "_from" in header and "_to" in header:
            return True
        return False

    def is_node_table(header: List) -> bool:
        if "_key" in header:
            return True
        return False

    edge_table = None
    node_table = None
    conflict = False

    for path in paths:
        with path.open(mode="r") as in_file:
            header = in_file.readline().strip()
            columns = header.split(",")

            if is_edge_table(columns):
                if edge_table is not None:
                    conflict = True
                else:
                    edge_table = path

            elif is_node_table(columns):
                if node_table is not None:
                    conflict = True
                else:
                    node_table = path
            else:
                raise Exception(
                    f"Path {path} is neither a node table nor an edge table."
                )

    if conflict:
        path_strings = list(map(lambda x: str(x), paths))
        raise Exception(f"Conflicting headers between files: {path_strings}")

    return (node_table, edge_table)


if __name__ == "__main__":
    data_dir = Path(__file__).absolute().parents[1] / "data"

    for path in data_dir.iterdir():
        dataset_name = path.name
        print(f'Processing dataset "{dataset_name}"')

        files = tuple(path.glob("*.csv"))
        node_table, edge_table = determine_table_types(files)

        try:
            workspace = get_workspace_db(WORKSPACE_NAME)
        except WorkspaceNotFound:
            create_workspace(WORKSPACE_NAME)
            workspace = get_workspace_db(WORKSPACE_NAME)

        for i, file in enumerate((node_table, edge_table)):
            table_name = file.stem
            edge = i == 1

            with file.open(mode="r") as csv_file:
                rows = list(csv.DictReader(csv_file))

            if workspace.has_collection(table_name):
                print(f'\tTable "{table_name}" already exists, skipping...')
            else:
                coll = workspace.create_collection(table_name, edge=edge)
                inserted = len(coll.insert_many(rows))
                table_type = "edge" if edge else "node"

                print(
                    f'\tInserted {inserted} rows into {table_type} table "{table_name}"'
                )
