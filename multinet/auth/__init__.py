"""Authorization types."""
from dataclasses import asdict
from flasgger import swag_from
from flask import make_response, session
from flask.blueprints import Blueprint
import json
from werkzeug.wrappers import Response as ResponseWrapper
from webargs import fields
from webargs.flaskparser import use_kwargs

from multinet.user import (
    MULTINET_COOKIE,
    user_from_cookie,
    filtered_user,
    delete_user_cookie,
    search_user,
)

from multinet.util import stream
from multinet.auth.util import require_login

bp = Blueprint("user", "user")


@bp.route("/info", methods=["GET"])
@swag_from("swagger/user/info.yaml")
def user_info() -> ResponseWrapper:
    """Return the filtered user object."""

    logged_out = make_response(json.dumps(None), 200)

    cookie = session.get(MULTINET_COOKIE)
    if cookie is None:
        return logged_out

    user = user_from_cookie(cookie)
    if user is None:
        session.pop(MULTINET_COOKIE, None)
        return logged_out

    return make_response(asdict(filtered_user(user)))


@bp.route("/logout", methods=["GET"])
@swag_from("swagger/user/logout.yaml")
def logout() -> ResponseWrapper:
    """Return the filtered user object."""

    # Instruct the browser to delete its session cookie, if it exists.
    cookie = session.pop(MULTINET_COOKIE, None)
    if cookie is not None:
        # Load the user model and invalidate its session.
        user = user_from_cookie(cookie)
        if user is not None:
            delete_user_cookie(user)

    return make_response("", 200)


@bp.route("/search", methods=["GET"])
@require_login
@use_kwargs({"query": fields.Str()})
@swag_from("swagger/user/search.yaml")
def search(query: str) -> ResponseWrapper:
    """Search for users given a partial string."""
    return stream(search_user(query))
