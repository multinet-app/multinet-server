"""User data and functions."""

from uuid import uuid4
from multinet.db import db


def user_collection():
    """Return the collection that contains user documents."""
    sysdb = db("_system")

    if not sysdb.has_collection("users"):
        sysdb.create_collection("users")

    return sysdb.collection("users")


def user_exists(userinfo):
    """Return the existance of a user."""
    return load_user(userinfo) is not None


def load_user(userinfo):
    """Return a user doc if it exists, else None."""
    coll = user_collection()
    user = list(coll.find({"sub": userinfo["sub"]}, limit=1))

    if not user:
        return None

    return user[0]


def register_user(userinfo, token):
    """Register a user with the given user info, and token."""
    coll = user_collection()

    document = dict(userinfo)
    document.update(
        {"multinet_id": uuid4().hex, "token": token, "session": uuid4().hex}
    )

    # Probably handle errors here
    coll.insert(document)
    return document


def load_user_from_cookie(cookie):
    """Use provided cookie to load a user, return None if they dont exist."""
    coll = user_collection()
    document = list(coll.find({"session": cookie}, limit=1))

    if not len(document):
        return None

    return document[0]


def get_user_cookie(user):
    """Return the cookie from the user object."""
    return user["session"]
