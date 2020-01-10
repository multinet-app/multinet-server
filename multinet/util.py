"""Utility functions."""
import json
import os

from flask import Response

from typing import Sequence, Any, Generator, Tuple, List, Set

from . import db
from .errors import DatabaseNotLive, DecodeFailed

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test/data"))


# TODO: Replace Tuple structure with a TypedDict
def get_edge_table_properties(
    workspace: str, edge_table: str
) -> Tuple[List[Tuple[str, Set[str]]], Tuple[List[str], List[str]]]:
    """Return extracted information about an edge table."""

    loaded_workspace = db.db(workspace)
    edges = list(loaded_workspace.collection(edge_table).all())

    tables_to_keys = {}
    from_tables = set()
    to_tables = set()

    for edge in edges:
        nodes = (edge["_from"].split("/"), edge["_to"].split("/"))
        from_tables.add(nodes[0][0])
        to_tables.add(nodes[1][0])

        for table, key in nodes:
            if table in tables_to_keys:
                tables_to_keys[table].add(key)
            else:
                tables_to_keys[table] = {key}

    mapping_list = [(table, tables_to_keys[table]) for table in tables_to_keys.keys()]
    return (mapping_list, (list(from_tables), list(to_tables)))


def generate(iterator: Sequence[Any]) -> Generator[str, None, None]:
    """Return a generator that yields an iterator's contents into a JSON list."""
    yield "["

    comma = ""
    for row in iterator:
        yield f"{comma}{json.dumps(row)}"
        comma = ","

    yield "]"


def stream(iterator: Sequence[Any]) -> Response:
    """Convert an iterator to a Flask response."""
    return Response(generate(iterator), mimetype="application/json")


def require_db() -> None:
    """Check if the db is live."""
    if not db.check_db():
        raise DatabaseNotLive()


def decode_data(input: bytes) -> str:
    """Decode the request data assuming utf8 encoding."""
    try:
        body = input.decode("utf8")
    except UnicodeDecodeError as e:
        raise DecodeFailed(str(e))

    return body


def data_path(file_name: str) -> str:
    """Load data from the test directory."""
    file_path = os.path.join(TEST_DATA_DIR, file_name)
    print(file_path)
    return file_path
