"""Handling of Google Authorization."""
import requests
import base64
import json
import os

from flasgger import swag_from
from flask import (
    Flask,
    current_app,
    redirect,
    request,
    Response,
    session,
    make_response,
    url_for,
)
from werkzeug.wrappers import Response as ResponseWrapper
from flask.blueprints import Blueprint
from authlib.integrations.flask_client import OAuth

from webargs.flaskparser import use_kwargs
from webargs import fields

from multinet.db.models.user import User
from multinet.auth.types import GoogleUserInfo
from multinet.auth.util import (
    create_login_token,
    encode_auth_token,
    MULTINET_LOGIN_TOKEN,
)

from typing import Dict, Optional


CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

GOOGLE_BASE_API = "https://www.googleapis.com/"
GOOGLE_USER_INFO_URL = "oauth2/v3/userinfo"

bp = Blueprint("google", "google")
oauth = OAuth()


def default_return_url() -> str:
    """
    Return a default return_url value.

    Must be done as a function, so the app context is available.
    """
    return url_for("user.user_info", _external=True)


def parse_id_token(token: str) -> GoogleUserInfo:
    """Parse the base64 encoded id token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise RuntimeError("Received Invalid ID Token")

    payload = parts[1]
    padded = payload + ("=" * (4 - len(payload) % 4))
    decoded = base64.b64decode(padded)

    return GoogleUserInfo(**json.loads(decoded))


def ensure_external_url(url: str) -> str:
    """Ensure a url is prefixed with a protocol (http or https)."""
    return_url = url

    if not url.startswith("http://") and not url.startswith("https://"):
        return_url = f"http://{url}"

    return return_url


def google_oauth2_info() -> Dict:
    """Return Google's spec for their OAuth endpoints."""
    resp = requests.get("https://accounts.google.com/.well-known/openid-configuration")
    info = resp.json()
    return info


def init_oauth(app: Flask) -> None:
    """Initialize the OAuth integration."""
    oauth.init_app(app)
    info = google_oauth2_info()

    if CLIENT_ID is not None and CLIENT_SECRET is not None:
        oauth.register(
            name="google",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            access_token_url=info["token_endpoint"],
            authorize_url=info["authorization_endpoint"],
            api_base_url=GOOGLE_BASE_API,
            client_kwargs={"scope": "openid profile email"},
        )


@bp.route("/login", methods=["GET"])
@use_kwargs({"return_url": fields.Str(location="query")})
@swag_from("swagger/google/login.yaml")
def login(return_url: Optional[str] = None) -> ResponseWrapper:
    """Redirect the user to Google to authorize this app."""
    google = oauth.create_client("google")

    if return_url is None:
        return_url = default_return_url()

    # Used instead of google.authorize_redirect, so we can grab the state and url
    state_and_url = google.create_authorization_url(
        url_for("google.authorized", _external=True)
    )

    state = state_and_url["state"]
    url = state_and_url["url"]

    # Used to return user to return_url
    session["return_url"] = return_url

    # So the flask session knows about the state
    google.save_authorize_data(
        request, state=state, redirect_uri=url_for("google.authorized", _external=True)
    )
    return redirect(url)


@bp.route("/authorized", methods=["GET"])
@use_kwargs({"state": fields.Str(), "code": fields.Str()})
@swag_from("swagger/google/authorized.yaml")
def authorized(state: str, code: str) -> ResponseWrapper:
    """Where google redirects to once the user had authorized the app."""
    google = oauth.create_client("google")

    # Code is automatically read from flask session
    token = google.authorize_access_token()
    rawinfo = parse_id_token(token["id_token"])

    existing_user = User.from_id(rawinfo.sub)
    if not existing_user:
        user = User.register(**rawinfo.__dict__)
    else:
        new_user_data = {**User.asdict(existing_user), **rawinfo.__dict__}
        user = User.from_dict(new_user_data)
        user.save()

    return_url = session.pop("return_url", default_return_url())
    resp: Response = make_response(redirect(ensure_external_url(return_url)))

    encoded_login_token = encode_auth_token(create_login_token(user.get_session()))

    # If running in development, don't set secure and samesite cookie attributes
    development = current_app.config.get("ENV") == "development"
    resp.set_cookie(
        MULTINET_LOGIN_TOKEN,
        value=encoded_login_token,
        secure=True if not development else False,
        samesite="None" if not development else None,
        httponly=True,
    )

    return resp
