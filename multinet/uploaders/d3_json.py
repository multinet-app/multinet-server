"""Multinet uploader for nested JSON files."""

from .. import util

from flask import Blueprint

from typing import Any

bp = Blueprint("d3_json", __name__)
bp.before_request(util.require_db)


def validate_d3_json():
    """Works something."""
    pass


@bp.route("/<workspace>/<table>", methods=["POST"])
def upload(workspace: str, table: str) -> Any:
    """Works something."""
    pass
