"""User data and functions."""

import dataclasses
from uuid import uuid4
from arango.collection import StandardCollection
from dacite import from_dict
from flask import session

from multinet.db import db
from multinet.errors import InternalServerError
from multinet.auth.types import (
    GoogleUserInfo,
    MultinetInfo,
    UserInfo,
    User,
    FilteredUser,
)

from typing import Optional, Dict

MULTINET_COOKIE = "multinet-token"


def user_collection() -> StandardCollection:
    """Return the collection that contains user documents."""
    sysdb = db("_system")

    if not sysdb.has_collection("users"):
        sysdb.create_collection("users")

    return sysdb.collection("users")


def user_exists(userinfo: UserInfo) -> bool:
    """Return the existance of a user."""
    return load_user(userinfo) is not None


def find_user_from_id(sub: str) -> Optional[User]:
    """Directly uses the `sub` property to return a user."""
    coll = user_collection()
    try:
        return from_dict(User, next(coll.find({"sub": sub}, limit=1)))
    except StopIteration:
        return None


def load_user(userinfo: UserInfo) -> Optional[User]:
    """Return a user doc if it exists, else None."""
    return find_user_from_id(userinfo.sub)


def updated_user(user: User) -> User:
    """Update a user using the provided user object."""
    coll = user_collection()
    inserted_info = coll.update(dataclasses.asdict(user))

    return from_dict(User, next(coll.find({"_id": inserted_info["_id"]}, limit=1)))


def register_user(userinfo: UserInfo) -> User:
    """Register a user with the given user info."""
    coll = user_collection()

    document = dataclasses.asdict(userinfo)
    document["multinet"] = dataclasses.asdict(MultinetInfo())

    inserted_info: Dict = coll.insert(document)
    return from_dict(User, next(coll.find(inserted_info, limit=1)))


def set_user_cookie(user: User) -> User:
    """Update the user cookie."""
    new_user = copy_user(user)

    new_cookie = uuid4().hex
    new_user.multinet.session = new_cookie

    return updated_user(new_user)


def delete_user_cookie(user: User) -> User:
    """Delete the user cookie."""
    user_copy = copy_user(user)

    # Remove the session object from the user record, then persist that to the
    # database.
    user_copy.multinet.session = None
    return updated_user(user_copy)


def user_from_cookie(cookie: str) -> Optional[User]:
    """Use provided cookie to load a user, return None if they dont exist."""
    coll = user_collection()

    try:
        return from_dict(User, next(coll.find({"multinet.session": cookie}, limit=1)))
    except StopIteration:
        return None


def current_user() -> Optional[User]:
    """Return the logged in user (if any) from the current session."""
    cookie = session.get(MULTINET_COOKIE)
    if cookie is None:
        return None

    return user_from_cookie(cookie)


def get_user_cookie(user: User) -> str:
    """Return the cookie from the user object, or create it if it doesn't exist."""

    if user.multinet.session is None:
        user = set_user_cookie(user)

    if not isinstance(user.multinet.session, str):
        raise InternalServerError("User cookie not set.")

    return user.multinet.session


def filter_user_info(info: GoogleUserInfo) -> UserInfo:
    """Return a subset of the User Object."""
    fields = {field.name for field in dataclasses.fields(UserInfo)}
    info_dict = dataclasses.asdict(info)

    return from_dict(UserInfo, {k: v for k, v in info_dict.items() if k in fields})


def filtered_user(user: User) -> FilteredUser:
    """Remove ArangoDB metadata from a document."""
    doc = dataclasses.asdict(user)

    fields = {field.name for field in dataclasses.fields(FilteredUser)}
    filtered = {k: v for k, v in doc.items() if k in fields}

    return from_dict(FilteredUser, filtered)


def copy_user(user: User) -> User:
    """Create and return a new instance of User."""
    return from_dict(User, dataclasses.asdict(user))
