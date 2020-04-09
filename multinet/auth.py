"""Handling of Authorization."""
import requests
from os import getenv
from flask import redirect, request
from flask.blueprints import Blueprint
from authlib.integrations.flask_client import OAuth

from webargs.flaskparser import use_kwargs
from webargs import fields

# from multinet.db import db


CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")
MULTINET_CLIENT_BASE_URL = getenv("MULTINET_CLIENT_BASE_URL")

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


@bp.route("/")
@use_kwargs({"return_url": fields.Str(location="query")})
def login(return_url: str):
    """Redirect the user to Google to authorize this app."""
    google = oauth.create_client("google")

    # Used instead of google.authorize_redirect, so we can grab the state and url
    state_and_url = google.create_authorization_url(
        "http://localhost:5000/login/google/authorized"
    )

    state = state_and_url["state"]
    url = state_and_url["url"]

    states_to_return_urls[state] = return_url

    # So the flask session knows about the state
    google.save_authorize_data(
        request,
        state=state,
        redirect_uri="http://localhost:5000/login/google/authorized",
    )
    return redirect(url)


@bp.route("/google/authorized")
@use_kwargs({"state": fields.Str(), "code": fields.Str()})
def authorized(state, code):
    """Where google redirects to once the user had authorized the app."""
    google = oauth.create_client("google")

    # This is needed so the line below knows the user token.
    # I'm not sure how to get around this,
    # regardless we'll probably need to save this at some point.
    # token = google.authorize_access_token()
    # userinfo = google.get(GOOGLE_USER_INFO_URL).json()
    # return userinfo

    return_url = states_to_return_urls.pop(state)
    return redirect(return_url)
    # return "200 OK"


@bp.route("/info")
def user_info():
    google = oauth.create_client("google")
    google.authorize_access_token()
    userinfo = google.get(GOOGLE_USER_INFO_URL).json()
    return userinfo


# def user_collection():
#     """."""
#     sysdb = db("_system")

#     if not sysdb.has_collection("users"):
#         sysdb.create_collection("users")

#     return sysdb.collection("users")


# def load_user(user_id):
#     """."""
#     coll = user_collection()
#     user = coll.find({"multinet_id": user_id}, limit=1)
#     print(list(user))
