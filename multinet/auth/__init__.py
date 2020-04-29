"""Authorization types."""
from dataclasses import asdict
from flask import make_response, session
from flask.blueprints import Blueprint
from werkzeug.wrappers import Response as ResponseWrapper

from multinet.user import load_user_from_cookie, filtered_user

MULTINET_COOKIE = "multinet-token"

bp = Blueprint("user", "user")


@bp.route("/info")
def user_info() -> ResponseWrapper:
    """Return the filtered user object."""

    forbidden = make_response("null", 403)

    cookie = session.get(MULTINET_COOKIE)
    if cookie is None:
        return forbidden

    user = load_user_from_cookie(cookie)
    if user is None:
        session.pop(MULTINET_COOKIE, None)
        return forbidden

    return make_response(asdict(filtered_user(user)))


@bp.route("/logout")
def logout() -> ResponseWrapper:
    """Return the filtered user object."""

    session.pop(MULTINET_COOKIE, None)
    return make_response("", 200)
