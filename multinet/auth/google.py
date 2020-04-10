"""Handling of Google Authorization."""
import requests
from os import getenv
from flask import redirect, request, make_response
from flask.blueprints import Blueprint
from authlib.integrations.flask_client import OAuth

from webargs.flaskparser import use_kwargs
from webargs import fields

from multinet.user import (
    load_user_from_cookie,
    load_user,
    get_user_cookie,
    register_user,
    user_exists,
)


CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")

GOOGLE_BASE_API = "https://www.googleapis.com/"
GOOGLE_USER_INFO_URL = "oauth2/v3/userinfo"

bp = Blueprint("auth", "auth")
oauth = OAuth()

states_to_return_urls = {}


def google_oauth2_info():
    """Return Google's spec for their OAuth endpoints."""
    resp = requests.get("https://accounts.google.com/.well-known/openid-configuration")
    info = resp.json()
    return info


def init_oauth(app):
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
        client_kwargs={"scope": "profile email openid"},
    )


@bp.route("/login")
@use_kwargs({"return_url": fields.Str(location="query")})
def login(return_url):
    """Redirect the user to Google to authorize this app."""
    google = oauth.create_client("google")

    # Used instead of google.authorize_redirect, so we can grab the state and url
    state_and_url = google.create_authorization_url(
        "http://localhost:5000/google/authorized"
    )

    state = state_and_url["state"]
    url = state_and_url["url"]

    # Used to return user to return_url
    states_to_return_urls[state] = return_url

    # So the flask session knows about the state
    google.save_authorize_data(
        request, state=state, redirect_uri="http://localhost:5000/google/authorized"
    )
    return redirect(url)


@bp.route("/authorized")
@use_kwargs({"state": fields.Str(), "code": fields.Str()})
def authorized(state, code):
    """Where google redirects to once the user had authorized the app."""
    google = oauth.create_client("google")

    # This is needed so the line below knows the user token.
    # I'm not sure how to get around this,
    token = google.authorize_access_token()
    userinfo = google.get(GOOGLE_USER_INFO_URL).json()

    if user_exists(userinfo):
        user = load_user(userinfo)
    else:
        user = register_user(userinfo, token)

    cookie = get_user_cookie(user)

    # Pop return_url using state as key
    return_url = states_to_return_urls.pop(state)
    resp = make_response(redirect(return_url))

    if (
        "multinet-token" not in request.cookies
        or request.cookies["multinet-token"] != cookie
    ):
        resp.set_cookie("multinet-token", cookie)

    return resp


@bp.route("/info")
def user_info():
    """Return the filtered user object."""
    # TODO: Filter out unwanted keys from the user object

    cookie = request.cookies.get("multinet-token")
    user = load_user_from_cookie(cookie)

    if cookie is None or user is None:
        return "403 Forbidden"

    return user
