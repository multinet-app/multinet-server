"""Script that populates initial data into the multinet backend."""

import os
import click
import requests
import json

from pathlib import Path
from typing import List


DATA_DIR = Path(__file__).absolute().parents[1] / "data"

DEFAULT_HOST = os.environ.get("MULTINET_HOST", "localhost")
DEFAULT_PORT = os.environ.get("MULTINET_PORT", "5000")
DEFAULT_ADDRESS = f"{DEFAULT_HOST}:{DEFAULT_PORT}"

server_address = DEFAULT_ADDRESS


def root_api_endpoint() -> str:
    """Return the shared root api endpoint."""
    return f"http://{server_address}/api"


def check_server_connection() -> None:
    """Check if the server is running."""
    try:
        requests.get(f"{root_api_endpoint()}/workspaces")
        return
    except requests.exceptions.ConnectionError:
        fatal(f"Could not establish connection at {server_address}.")
    except requests.exceptions.InvalidURL:
        fatal(f"Invalid address {server_address}.")


def get_edge_tables(workspace: str) -> List[str]:
    """Return the edge tables for a given workspace."""
    resp = requests.get(
        f"{root_api_endpoint()}/workspaces/{workspace}/tables?type=edge"
    )

    if resp.ok:
        tables = json.loads(resp.text)
        return tables

    return []


def get_table_rows(workspace: str, table: str) -> List:
    """Return the rows of a table."""
    resp = requests.get(
        f"{root_api_endpoint()}/workspaces/{workspace}/tables/{table}/rows"
    )

    if resp.ok:
        rows = json.loads(resp.text)
        return rows

    return []


def check_workspace_exists(workspace: str) -> bool:
    """Return if the specified workspace exists yet or not."""

    resp = requests.get(f"{root_api_endpoint()}/workspaces/{workspace}")

    if resp.ok:
        return True

    return False


def create_workspace(workspace: str) -> bool:
    """
    Create the workspace.

    Returns True if successful, False otherwise
    """
    resp = requests.post(f"{root_api_endpoint()}/workspaces/{workspace}")

    if resp.ok:
        return True

    return False


def create_graph(workspace: str, graph_name: str, edge_table: str) -> bool:
    """Create a graph."""
    resp = requests.post(
        f"{root_api_endpoint()}/workspaces/{workspace}/graphs/{graph_name}",
        params={"edge_table": edge_table},
    )

    if resp.ok:
        return True

    return False


def table_exists(workspace: str, table: str) -> bool:
    """Check if the table exists."""
    resp = requests.get(f"{root_api_endpoint()}/workspaces/{workspace}/tables/{table}")

    if resp.status_code == 200:
        return True
    return False


def create_table(workspace: str, table: str, data: str) -> bool:
    """
    Create table.

    Returns True if successful, False otherwise
    """
    resp = requests.post(
        f"{root_api_endpoint()}/csv/{workspace}/{table}", data=data.encode("utf-8")
    )

    if resp.ok:
        return True
    return False


def log(text: str, indent: int = 0, error=False, success=False):
    """Log to console output."""

    fg = None
    if error:
        fg = "red"
    elif success:
        fg = "green"

    text = click.wrap_text(text, initial_indent=(indent * " "))
    click.echo(click.style(text, fg=fg))


def fatal(text: str, indent: int = 0):
    """Log and immediately exit."""
    log(text, indent, error=True)
    exit(1)


@click.group()
def cli():
    """Script that helps with bootstrapping example data."""
    pass


@cli.command("populate")
@click.argument("address", nargs=1, required=False)
def populate(address: str):
    """
    Populate the multinet instance with example data.

    If the server address is not provided as a command argument, this script checks the
    MULTINET_HOST and MULTINET_PORT environment variables, defaulting to localhost:5000.
    """
    global server_address
    log_tabstop = 4
    log_indent = 0

    if address is not None:
        server_address = address

    check_server_connection()

    log(f"Populating data on {server_address}...", indent=log_indent)

    for path in DATA_DIR.iterdir():
        workspace = path.name

        log(f'Processing dataset "{workspace}"', indent=log_indent)
        log_indent += log_tabstop

        files = tuple(path.glob("*.csv"))

        if check_workspace_exists(workspace):
            log(
                f'Workspace "{workspace}" already exists, skipping...',
                indent=log_indent,
            )
            continue

        if not create_workspace(workspace):
            log(f"Error creating workspace {workspace}.", indent=log_indent)
            continue

        # Create Tables
        for file in files:
            table_name = file.stem

            if table_exists(workspace, table_name):
                fatal(
                    f'FATAL: Table "{table_name}" already exists '
                    "in newly created workspace.",
                    indent=log_indent,
                )
            else:
                with file.open(mode="r") as csv_file:
                    csv_data = csv_file.read()

                if not create_table(workspace, table_name, csv_data):
                    log(f"Error creating table {table_name}.", indent=log_indent)
                else:
                    log(f"Table {table_name} created.", indent=log_indent)

        # Create Graphs
        edge_tables = get_edge_tables(workspace)
        log(f"Generating graphs...", indent=log_indent)

        for edge_table in edge_tables:
            rows = get_table_rows(workspace, edge_table)
            rows = [
                {k: v for k, v in row.items() if k == "_from" or k == "_to"}
                for row in rows
            ]

            create_graph(workspace, workspace, edge_table)

        log_indent -= log_tabstop

    script_complete_string = "Data population complete."
    log("-" * len(script_complete_string), indent=log_indent)
    log(script_complete_string, indent=log_indent, success=True)


if __name__ == "__main__":
    cli()
