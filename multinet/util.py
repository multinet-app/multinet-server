"""Utility functions."""
import os
import json
import random

from uuid import uuid1
from string import ascii_lowercase
from flask import Response
from typing import Sequence, Any, Generator, Dict, Set, Iterable

from multinet import db
from multinet.types import EdgeTableProperties
from multinet.errors import DatabaseNotLive, DecodeFailed

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test/data"))


def filter_unwanted_keys(row: Dict) -> Dict:
    """Remove any unwanted keys from a document."""
    unwanted = {"_rev", "_id"}
    return {k: v for k, v in row.items() if k not in unwanted}


def generate_filtered_docs(rows: Sequence[Dict]) -> Generator[Dict, None, None]:
    """Filter unwanted keys from all documents with a generator."""

    for row in rows:
        yield filter_unwanted_keys(row)


def get_edge_table_properties(workspace: str, edge_table: str) -> EdgeTableProperties:
    """
    Return extracted information about an edge table.

    Extracts 3 pieces of data from an edge table.

    table_keys: A mapping of all referenced tables to their respective referenced keys.
    from_tables: A set containing the tables referenced in the _from column.
    to_tables: A set containing the tables referenced in the _to column.
    """

    loaded_workspace = db.db(workspace)
    edges = loaded_workspace.collection(edge_table).all()

    tables_to_keys: Dict[str, Set[str]] = {}
    from_tables = set()
    to_tables = set()

    for edge in edges:
        from_node, to_node = edge["_from"].split("/"), edge["_to"].split("/")
        from_tables.add(from_node[0])
        to_tables.add(to_node[0])

        for table, key in (from_node, to_node):
            if table in tables_to_keys:
                tables_to_keys[table].add(key)
            else:
                tables_to_keys[table] = {key}

    return {
        "table_keys": tables_to_keys,
        "from_tables": from_tables,
        "to_tables": to_tables,
    }


def generate(iterator: Iterable[Any]) -> Generator[str, None, None]:
    """Return a generator that yields an iterator's contents into a JSON list."""
    yield "["

    comma = ""
    for row in iterator:
        yield f"{comma}{json.dumps(row)}"
        comma = ","

    yield "]"


def stream(iterator: Iterable[Any]) -> Response:
    """Convert an iterator to a Flask response."""
    return Response(generate(iterator), mimetype="application/json")


def require_db() -> None:
    """Check if the db is live."""
    if not db.check_db():
        raise DatabaseNotLive()


def decode_data(data: bytes) -> str:
    """Decode the request data assuming utf8 encoding."""
    try:
        body = data.decode("utf8")
    except UnicodeDecodeError as e:
        raise DecodeFailed(str(e))

    return body


def data_path(file_name: str) -> str:
    """Load data from the test directory."""
    file_path = os.path.join(TEST_DATA_DIR, file_name)
    print(file_path)
    return file_path


def generate_arango_workspace_name():
    """Generate a string that can be used as an ArangoDB workspace name."""
    return f"{random.choice(ascii_lowercase)}-{uuid1()}"
