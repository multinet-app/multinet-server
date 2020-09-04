"""Authorization types."""
import json
from flasgger import swag_from
from flask import make_response, request, Response
from flask.blueprints import Blueprint
from werkzeug.wrappers import Response as ResponseWrapper
from webargs import fields
from webargs.flaskparser import use_kwargs

from multinet.db.models.user import User
from multinet.util import stream
from multinet.auth.util import require_login, LOGIN_TOKEN_COOKIE

bp = Blueprint("user", "user")


@bp.route("/info", methods=["GET"])
@swag_from("swagger/user/info.yaml")
def user_info() -> ResponseWrapper:
    """Return the filtered user object."""
    logged_out: Response = make_response(json.dumps(None), 200)

    cookie = request.cookies.get(LOGIN_TOKEN_COOKIE)
    if cookie is None:
        return logged_out

    user = User.from_session(cookie)
    if user is None:
        logged_out.set_cookie(LOGIN_TOKEN_COOKIE, "", expires=0)
        return logged_out

    return make_response(user.asdict())


@bp.route("/logout", methods=["GET"])
@swag_from("swagger/user/logout.yaml")
def logout() -> ResponseWrapper:
    """Return the filtered user object."""

    cookie = request.cookies.get(LOGIN_TOKEN_COOKIE)
    if cookie is not None:
        # Load the user model and invalidate its session.

        user = User.from_session(cookie)
        if user is not None:
            user.delete_session()

    # Instruct the browser to delete its session cookie, if it exists.
    resp: Response = make_response("", 200)
    resp.set_cookie(LOGIN_TOKEN_COOKIE, "", expires=0)

    return resp


@bp.route("/search", methods=["GET"])
@require_login
@use_kwargs({"query": fields.Str()})
@swag_from("swagger/user/search.yaml")
def search(query: str) -> ResponseWrapper:
    """Search for users given a partial string."""
    return stream(User.search(query))
