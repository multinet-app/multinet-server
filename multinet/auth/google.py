"""Handling of Google Authorization."""
import requests
import base64
import json

from os import getenv
from flask import Flask, redirect, request, make_response, url_for
from werkzeug.wrappers import Response as ResponseWrapper
from flask.blueprints import Blueprint
from authlib.integrations.flask_client import OAuth

from webargs.flaskparser import use_kwargs
from webargs import fields

from multinet.user import (
    load_user,
    updated_user,
    get_user_cookie,
    set_user_cookie,
    register_user,
    filter_user_info,
)
from multinet.auth import MULTINET_COOKIE
from multinet.auth.types import GoogleUserInfo, User

from typing import Dict


CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")

GOOGLE_BASE_API = "https://www.googleapis.com/"
GOOGLE_USER_INFO_URL = "oauth2/v3/userinfo"

bp = Blueprint("google", "google")
oauth = OAuth()

states_to_return_urls = {}


def parse_id_token(token: str) -> GoogleUserInfo:
    """Parse the base64 encoded id token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise RuntimeError("Received Invalid ID Token")

    payload = parts[1]
    padded = payload + ("=" * (4 - len(payload) % 4))
    decoded = base64.b64decode(padded)
    return json.loads(decoded)


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
    oauth.register(
        name="google",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        access_token_url=info["token_endpoint"],
        authorize_url=info["authorization_endpoint"],
        api_base_url=GOOGLE_BASE_API,
        client_kwargs={"scope": "openid profile email"},
    )


@bp.route("/login")
@use_kwargs({"return_url": fields.Str(location="query")})
def login(return_url: str) -> ResponseWrapper:
    """Redirect the user to Google to authorize this app."""
    google = oauth.create_client("google")

    # Used instead of google.authorize_redirect, so we can grab the state and url
    state_and_url = google.create_authorization_url(
        url_for("google.authorized", _external=True)
    )

    state = state_and_url["state"]
    url = state_and_url["url"]

    # Used to return user to return_url
    states_to_return_urls[state] = return_url

    # So the flask session knows about the state
    google.save_authorize_data(
        request, state=state, redirect_uri=url_for("google.authorized", _external=True)
    )
    return redirect(url)


@bp.route("/authorized")
@use_kwargs({"state": fields.Str(), "code": fields.Str()})
def authorized(state: str, code: str) -> ResponseWrapper:
    """Where google redirects to once the user had authorized the app."""
    google = oauth.create_client("google")

    # Code is automatically read from flask session
    token = google.authorize_access_token()
    rawinfo: GoogleUserInfo = parse_id_token(token["id_token"])
    userinfo = filter_user_info(rawinfo)

    loaded_user = load_user(userinfo)
    if loaded_user is None:
        user = register_user(userinfo)
    else:
        new_user: User = {**loaded_user, **userinfo}
        user = updated_user(new_user)

    user = set_user_cookie(user)
    cookie = get_user_cookie(user)

    # Pop return_url using state as key
    return_url = states_to_return_urls.pop(state)
    resp = make_response(redirect(ensure_external_url(return_url)))
    resp.set_cookie(MULTINET_COOKIE, cookie)

    return resp
