"""Script that populates initial data into the multinet backend."""

import os
import click
import requests

from pathlib import Path


DATA_DIR = Path(__file__).absolute().parents[1] / "data"

DEFAULT_HOST = os.environ.get("MULTINET_HOST", "localhost")
DEFAULT_PORT = os.environ.get("MULTINET_PORT", "5000")
DEFAULT_ADDRESS = f"{DEFAULT_HOST}:{DEFAULT_PORT}"

server_address = DEFAULT_ADDRESS


def root_api_endpoint() -> str:
    """Return the shared root api endpoint."""
    return f"http://{server_address}/api"


def check_workspace_exists(workspace: str) -> bool:
    """Return if the specified workspace exists yet or not."""

    resp = requests.get(f"http://{server_address}/api/workspaces/{workspace}")

    if resp.status_code == 200:
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


def table_exists(workspace: str, table: str) -> bool:
    """Check if the table exists."""
    resp = requests.get(f"{root_api_endpoint()}/workspaces/{workspace}/tables/{table}")

    if resp.status_code == 400:
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


@click.group()
def cli():
    """Script that helps with bootstrapping example data."""
    pass


@cli.command("populate")
@click.argument("address", nargs=1, required=False)
def populate(address: str):
    """Populate arangodb with example data."""
    global server_address

    if address is not None:
        address_parts = address.split(":")
        address_parts = [x for x in address_parts if x]

        if len(address_parts) != 2:
            raise Exception("Invalid passed address.")

        server_address = address

    print(f"Populating data on {server_address}...")

    for path in DATA_DIR.iterdir():
        dataset_name = path.name
        print(f'Processing dataset "{dataset_name}"')

        files = tuple(path.glob("*.csv"))

        try:
            if check_workspace_exists(dataset_name):
                print(f'\tWorkspace "{dataset_name}" already exists, skipping...')
                continue
        except requests.exceptions.ConnectionError:
            raise Exception(f"\tConnection could not be established at {address}")

        if not create_workspace(dataset_name):
            print(f"\tError creating workspace {dataset_name}.")
            continue

        for file in files:
            table_name = file.stem

            if table_exists(dataset_name, table_name):
                print(f'\tTable "{table_name}" already exists, skipping...')
            else:
                with file.open(mode="r") as csv_file:
                    csv_data = csv_file.read()

                if not create_table(dataset_name, table_name, csv_data):
                    print(f"\tError creating table {table_name}.")
                else:
                    print(f"\tTable {table_name} created.")

    script_complete_string = "Data population complete."
    print("-" * len(script_complete_string))
    print(script_complete_string)


if __name__ == "__main__":
    cli()
