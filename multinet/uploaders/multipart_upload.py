"""Multinet uploader for multi-part uploaded files."""
from base64 import b64encode

from multinet import db, util

from flasgger import swag_from
from flask import Blueprint, request
from webargs import fields
from webargs.flaskparser import use_kwargs

# Import types
from typing import Any

from multinet.errors import RequiredParamsMissing

bp = Blueprint("uploads", __name__)
bp.before_request(util.require_db)


@bp.route("", methods=["POST"])
@swag_from("swagger/create_upload.yaml")
def create_upload() -> str:
    """Create a collection for multipart upload."""
    return db.create_upload_collection()


@bp.route("/<upload_id>/chunk", methods=["POST"])
@use_kwargs({"sequence": fields.Str(required=True)})
@swag_from("swagger/chunk_upload.yaml")
def chunk_upload(upload_id: str, sequence: str) -> Any:
    """Upload a chunk to the specified collection."""
    chunk = dict(request.files).get("chunk")

    if chunk is None:
        raise RequiredParamsMissing(["chunk"])

    # convert bytes to base64 string since arango doesn't support binary blobs
    stringified_blob = b64encode(chunk.read()).decode("ascii")

    db.insert_file_chunk(upload_id, sequence, stringified_blob)
    return sequence


@bp.route("/<upload_id>", methods=["DELETE"])
@swag_from("swagger/delete_upload_collection.yaml")
def delete_upload_collection(upload_id: str) -> Any:
    """Delete the database collection associated with the given upload_id."""
    return db.delete_upload_collection(upload_id)
