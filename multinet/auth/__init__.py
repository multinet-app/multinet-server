"""Authorization types."""
import json
from flasgger import swag_from
from flask import make_response
from flask.blueprints import Blueprint
from werkzeug.wrappers import Response as ResponseWrapper
from webargs import fields
from webargs.flaskparser import use_kwargs

from multinet.db.models.user import User
from multinet.util import stream
from multinet.auth.util import require_login, get_login_token_from_request

bp = Blueprint("user", "user")


@bp.route("/info", methods=["GET"])
@swag_from("swagger/user/info.yaml")
def user_info() -> ResponseWrapper:
    """Return the filtered user object."""

    logged_out = make_response(json.dumps(None), 200)

    token = get_login_token_from_request()
    if token is None:
        return logged_out

    user = User.from_token(token)
    if user is None:
        return logged_out

    return make_response(user.asdict())


@bp.route("/logout", methods=["GET"])
@swag_from("swagger/user/logout.yaml")
def logout() -> ResponseWrapper:
    """Return the filtered user object."""

    token = get_login_token_from_request()
    if token is not None:
        # Load the user model and invalidate its session.

        user = User.from_token(token)
        if user is not None:
            user.delete_session()

    return make_response("", 200)


@bp.route("/search", methods=["GET"])
@require_login
@use_kwargs({"query": fields.Str()})
@swag_from("swagger/user/search.yaml")
def search(query: str) -> ResponseWrapper:
    """Search for users given a partial string."""
    return stream(User.search(query))
