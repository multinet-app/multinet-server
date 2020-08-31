"""Utility functions."""
import os
import json

from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
from uuid import uuid1, uuid4
from flask import Response
from typing import Any, Generator, Dict, Iterable

from multinet import db
from multinet.db.models import workspace

from multinet.errors import DatabaseNotLive, DecodeFailed

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test/data"))
restricted_document_keys = {"_rev", "_id"}


# TODO: Remove once permission storage is updated
# https://github.com/multinet-app/multinet-server/issues/456
def expand_user_permissions(permissons: workspace.WorkspacePermissions) -> Dict:
    """
    Transform permission documents to directly contain user info.

    Currently, `WorkspacePermissons` only contains references to users through their
    `sub` values, stored as a str in the role to which it pertains. The client requires
    more information to properly display/use permissions, so this function transforms
    the `sub` values to the entire user object.

    This fuction will eventually be supplanted by a change in our permission model.
    """

    new_permissions = asdict(permissons)
    for role, users in new_permissions.items():
        if role == "public":
            continue

        if role == "owner":
            # Since the role is "owner", `users` is a `str`
            user = db.models.user.User.from_id(users)
            if user is not None:
                new_permissions["owner"] = user.asdict()
        else:
            new_users = []
            for sub in users:
                user = db.models.user.User.from_id(sub)
                if user is not None:
                    new_users.append(user.asdict())

            new_permissions[role] = new_users

    return new_permissions


# TODO: Remove once permission storage is updated
# https://github.com/multinet-app/multinet-server/issues/456
def contract_user_permissions(
    expanded_user_permissions: Dict,
) -> workspace.WorkspacePermissions:
    """Transform permission documents to only contain the `sub` values of users."""
    permissions = deepcopy(expanded_user_permissions)

    for role, users in permissions.items():
        if role == "public":
            continue

        if role == "owner":
            if users is not None:
                permissions["owner"] = users["sub"]
        else:
            permissions[role] = [user["sub"] for user in users]

    return workspace.WorkspacePermissions(**permissions)


def filter_unwanted_keys(row: Dict) -> Dict:
    """Remove any unwanted keys from a document."""
    return {k: v for k, v in row.items() if k not in restricted_document_keys}


def generate_filtered_docs(rows: Iterable[Dict]) -> Generator[Dict, None, None]:
    """Filter unwanted keys from all documents with a generator."""

    for row in rows:
        yield filter_unwanted_keys(row)


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


def generate_arango_workspace_name() -> str:
    """Generate a string that can be used as an ArangoDB workspace name."""
    return f"w-{uuid1()}"


# Make sure this function is only evaluated once
@lru_cache()
def flask_secret_key() -> str:
    """Load or create a flask secret key."""
    return os.getenv("FLASK_SECRET_KEY") or uuid4().hex
