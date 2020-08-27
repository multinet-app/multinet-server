"""Low-level database operations."""
import os
from functools import lru_cache
from uuid import uuid4

from arango import ArangoClient
from arango.database import StandardDatabase
from arango.collection import StandardCollection
from arango.aql import AQL
from arango.cursor import Cursor

from arango.exceptions import AQLQueryValidateError, AQLQueryExecuteError
from requests.exceptions import ConnectionError

from typing import Any, List, Dict, Optional
from typing_extensions import TypedDict

from multinet.errors import (
    UploadNotFound,
    AlreadyExists,
    AQLExecutionError,
    AQLValidationError,
)


# Type definitions.
GraphSpec = TypedDict("GraphSpec", {"nodeTables": List[str], "edgeTable": str})
GraphNodesSpec = TypedDict("GraphNodesSpec", {"count": int, "nodes": List[str]})
GraphEdgesSpec = TypedDict("GraphEdgesSpec", {"count": int, "edges": List[str]})

arango = ArangoClient(
    host=os.environ.get("ARANGO_HOST", "localhost"),
    port=int(os.environ.get("ARANGO_PORT", "8529")),
    protocol=os.environ.get("ARANGO_PROTOCOL", "http"),
)


def db(name: str, readonly: bool = True) -> StandardDatabase:
    """Return a handle for Arango database `name`."""

    username = "readonly" if readonly else "root"
    password = (
        os.environ.get("ARANGO_READONLY_PASSWORD", "letmein")
        if readonly
        else os.environ.get("ARANGO_PASSWORD", "letmein")
    )

    return arango.db(name, username=username, password=password)


@lru_cache()
def system_db(readonly: bool = True) -> StandardDatabase:
    """Return the singleton `_system` db handle."""
    return db("_system", readonly)


def check_db() -> bool:
    """Check the database to see if it's alive."""
    try:
        system_db().has_database("test")
        return True
    except ConnectionError:
        return False


def register_legacy_workspaces() -> None:
    """Add legacy workspaces to the workspace mapping."""
    sysdb = system_db()
    coll = workspace_mapping_collection(readonly=False)

    system_databases = {"_system", "uploads"}
    databases = {name for name in sysdb.databases() if name not in system_databases}
    registered = {doc["internal"] for doc in coll.all()}

    unregistered = databases - registered
    for workspace in unregistered:
        coll.insert({"name": workspace, "internal": workspace})


# Since this shouldn't ever change while running, this function becomes a singleton
@lru_cache(maxsize=1)
def workspace_mapping_collection(readonly: bool = True) -> StandardCollection:
    """Return the collection used for mapping external to internal workspace names."""
    sysdb = system_db(readonly=readonly)

    if not sysdb.has_collection("workspace_mapping"):
        sysdb.create_collection("workspace_mapping")

    return sysdb.collection("workspace_mapping")


# Caches the document that maps an external workspace name to it's internal one
@lru_cache()
def workspace_mapping(name: str) -> Optional[Dict]:
    """
    Get the document containing the workspace mapping for :name: (if it exists).

    Returns the document if found, otherwise returns None.
    """
    coll = workspace_mapping_collection()
    docs = list(coll.find({"name": name}, limit=1))

    if docs:
        return docs[0]

    return None


def user_collection() -> StandardCollection:
    """Return the collection that contains user documents."""
    sysdb = system_db(readonly=False)

    if not sysdb.has_collection("users"):
        sysdb.create_collection("users")

    return sysdb.collection("users")


def _run_aql_query(
    aql: AQL, query: str, bind_vars: Optional[Dict[str, Any]] = None
) -> Cursor:
    try:
        aql.validate(query)
        cursor = aql.execute(query, bind_vars=bind_vars)
    except AQLQueryValidateError as e:
        raise AQLValidationError(str(e))
    except AQLQueryExecuteError as e:
        raise AQLExecutionError(str(e))

    return cursor


# TODO: Refactor the below functions into an `Upload` class
# https://github.com/multinet-app/multinet-server/issues/464
@lru_cache(maxsize=1)
def uploads_database(readonly: bool = True) -> StandardDatabase:
    """Return the database used for storing multipart upload collections."""
    sysdb = system_db(readonly=False)
    if not sysdb.has_database("uploads"):
        sysdb.create_database("uploads")

    return db("uploads", readonly=readonly)


def create_upload_collection() -> str:
    """Insert empty multipart upload temp collection."""
    uploads_db = uploads_database(readonly=False)
    upload_id = f"u-{uuid4().hex}"
    uploads_db.create_collection(upload_id)
    return upload_id


def insert_file_chunk(upload_id: str, sequence: str, chunk: str) -> str:
    """Insert b64-encoded string `chunk` into temporary collection."""
    uploads_db = uploads_database(readonly=False)
    if not uploads_db.has_collection(upload_id):
        raise UploadNotFound(upload_id)

    collection = uploads_db.collection(upload_id)

    if collection.get(sequence) is not None:
        raise AlreadyExists("Upload Chunk", f"{upload_id}/{sequence}")

    collection.insert({sequence: chunk, "_key": sequence})

    return upload_id


def delete_upload_collection(upload_id: str) -> str:
    """Delete a multipart upload collection."""
    uploads_db = uploads_database(readonly=False)

    if not uploads_db.has_collection(upload_id):
        raise UploadNotFound(upload_id)

    uploads_db.delete_collection(upload_id)

    return upload_id
