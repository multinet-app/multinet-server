"""Multinet uploader for multi-part uploaded files."""
from base64 import b64encode

from multinet import db, util

from flask import Blueprint, request
from webargs import fields
from webargs.flaskparser import use_kwargs

# Import types
from typing import Any

bp = Blueprint("uploads", __name__)
bp.before_request(util.require_db)


@bp.route("", methods=["POST"])
def create_upload() -> Any:
    """Create a collection for multipart upload."""
    return db.create_upload_document()


@bp.route("/<upload_id>/chunk", methods=["POST"])
@use_kwargs({"sequence": fields.Str()})
def chunk_upload(upload_id: str, sequence: str) -> Any:
    """Upload a chunk to the specified collection."""
    chunk = dict(request.files)["chunk"].read()

    # convert bytes to base64 string since arango doesn't support binary blobs
    stringified_blob = b64encode(chunk).decode("ascii")

    db.insert_file_chunk(upload_id, sequence, stringified_blob)
    return sequence


@bp.route("/<upload_id>", methods=["DELETE"])
def delete_upload_collection(upload_id: str) -> Any:
    """Delete the database collection associated with the given upload_id."""
    return db.delete_document(db.uploads_collection(), upload_id)
