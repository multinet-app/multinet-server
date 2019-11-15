"""Utility functions."""
import json
import os

from flask import Response

from typing import Sequence, Any, Generator

from . import db
from .errors import DatabaseNotLive, DecodeFailed

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test/data"))


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
