"""User data and functions."""

from uuid import uuid4
from arango.collection import StandardCollection

from multinet.db import db
from multinet.auth.types import GoogleUserInfo, UserInfo, User

from typing import Optional, Dict


# This essentially duplicated the UserInfo TypedDict.
# Is this a good reason to switch to dataclasses?
USER_FIELDS = {"email", "name", "family_name", "given_name", "picture", "sub"}


def user_collection() -> StandardCollection:
    """Return the collection that contains user documents."""
    sysdb = db("_system")

    if not sysdb.has_collection("users"):
        sysdb.create_collection("users")

    return sysdb.collection("users")


def user_exists(userinfo: GoogleUserInfo) -> bool:
    """Return the existance of a user."""
    return load_user(userinfo) is not None


def load_user(userinfo: UserInfo) -> Optional[User]:
    """Return a user doc if it exists, else None."""
    coll = user_collection()
    user = list(coll.find({"sub": userinfo["sub"]}, limit=1))

    if not user:
        return None

    return user[0]


def save_user(user: User) -> User:
    """Update a user using the provided user object."""
    coll = user_collection()
    inserted_info: Dict = coll.update(user)  # type: ignore
    return next(coll.find({"_id": inserted_info["_id"]}, limit=1))


def register_user(userinfo: UserInfo) -> User:
    """Register a user with the given user info."""
    coll = user_collection()

    # TODO: Fix mypy errors
    document: User = {**userinfo, "multinet": {}}
    inserted_info: Dict = coll.insert(document)  # type: ignore

    return next(coll.find(inserted_info, limit=1))


def set_user_cookie(user: User) -> User:
    """Update the user cookie."""
    new_user: User = dict(user)

    new_cookie = uuid4().hex
    new_user["multinet"]["session"] = new_cookie

    return save_user(new_user)


def load_user_from_cookie(cookie: str) -> Optional[User]:
    """Use provided cookie to load a user, return None if they dont exist."""
    coll = user_collection()
    document = list(coll.find({"multinet.session": cookie}, limit=1))

    if not len(document):
        return None

    return document[0]


def get_user_cookie(user: User) -> str:
    """Return the cookie from the user object, or create it if it doesn't exist."""

    if not user["multinet"].get("session"):
        user = set_user_cookie(user)

    return user["multinet"]["session"]


def filter_user_info(info: GoogleUserInfo) -> UserInfo:
    """Return a subset of the User Object."""
    return {k: v for k, v in info.items() if k in USER_FIELDS}


def filter_document_meta(doc: Dict) -> User:
    """Remove meta information from a document."""
    return {k: v for k, v in doc.items() if k not in {"_id", "_key", "_rev"}}
