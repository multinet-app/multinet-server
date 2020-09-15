"""User data and functions."""
from __future__ import annotations  # noqa: T484

import json

from dataclasses import dataclass
from uuid import uuid4
from copy import copy
from dacite import from_dict
from arango.cursor import Cursor

from multinet.db import user_collection, system_db, _run_aql_query
from multinet.auth.types import LoginSessionDict

from typing import Optional, Dict, Generator, Any


@dataclass
class MultinetInfo:
    """Multinet specific user metadata."""

    session: Optional[str] = None


@dataclass
class UserInfo:
    """Base info for a user."""

    family_name: str
    given_name: str
    name: str
    sub: str
    email: str
    picture: Optional[str] = None


def generate_user_session() -> str:
    """Generate a session."""
    return uuid4().hex


class User:
    """The class representing a user in multinet."""

    def __init__(
        self,
        family_name: str,
        given_name: str,
        name: str,
        sub: str,
        email: str,
        picture: Optional[str] = None,
        **kwargs: Any
    ):
        """Construct user object."""
        self.family_name = family_name
        self.given_name = given_name
        self.name = name
        self.sub = sub
        self.email = email
        self.picture = picture

        # Keeps track of multinet metadata
        self.multinet: Optional[MultinetInfo] = None

    @staticmethod
    def exists(sub: str) -> bool:
        """Search the user collection for a user that has the matching `sub` value."""
        return User.get(sub) is not None

    @staticmethod
    def get(sub: str) -> Optional[Dict]:
        """Return the respective user document if it exists, or None."""
        coll = user_collection()

        try:
            doc = next(coll.find({"sub": sub}, limit=1))
        except StopIteration:
            return None

        return doc

    @staticmethod
    def register(*args: Any, **kwargs: Any) -> User:
        """Register and return a user with the passed info."""
        user = User(*args, **kwargs)
        user.ensure_session()

        return user

    @staticmethod
    def from_id(sub: str) -> Optional[User]:
        """Return a user from the passed `sub` value, if they exist."""
        doc = User.get(sub)
        return User.from_dict(doc) if doc else None

    @staticmethod
    def from_session(session_id: str) -> Optional[User]:
        """Return a User from the session, if it exists."""
        coll = user_collection()

        try:
            return User.from_dict(
                next(coll.find({"multinet.session": session_id}, limit=1))
            )
        except StopIteration:
            return None

    @staticmethod
    def from_token(token: LoginSessionDict) -> Optional[User]:
        """Return a User from a login token."""
        return User.from_session(token["session"])

    @staticmethod
    def from_dict(d: Dict) -> User:
        """Return a user object from a dict."""
        keys = UserInfo.__annotations__.keys()
        filtered = {k: v for k, v in d.items() if k in keys}

        user = User(**filtered)
        user.multinet = from_dict(MultinetInfo, d["multinet"])

        return user

    @staticmethod
    def search(query: str) -> Cursor:
        """Search for users given a partial string."""

        coll = user_collection()
        aql = system_db().aql

        bind_vars = {"@users": coll.name, "query": query}
        query = """
            FOR doc in @@users
            FILTER CONTAINS(LOWER(doc.name), LOWER(@query))
                OR CONTAINS(LOWER(doc.email), LOWER(@query))

            LIMIT 50
            RETURN doc
        """

        return _run_aql_query(aql, query, bind_vars)

    def save(self) -> None:
        """Save this user into the user collection."""
        coll = user_collection()
        user_as_dict = self.asdict()

        doc = User.get(self.sub)
        if doc:
            dict_to_save = {**doc, **user_as_dict}
            coll.update(dict_to_save)
        else:
            coll.insert(user_as_dict)

    def delete(self) -> None:
        """Delete this user from the database."""
        coll = user_collection()
        doc = User.get(self.sub)
        if doc:
            coll.delete(doc["_id"])

    def ensure_session(self) -> None:
        """Ensure that this user has a valid session."""
        if self.multinet is None:
            self.multinet = MultinetInfo(session=generate_user_session())

        if self.multinet.session is None:
            self.multinet.session = generate_user_session()

        self.save()

    def get_session(self) -> str:
        """Return the login session of a user."""
        self.ensure_session()

        # Asserts needed for mypy
        assert self.multinet is not None
        assert self.multinet.session is not None
        return self.multinet.session

    def set_session(self, session: str) -> None:
        """Set the login session of a user."""
        if self.multinet is None:
            self.multinet = MultinetInfo(session=session)
        else:
            self.multinet.session = session

        self.save()

    def delete_session(self) -> None:
        """Delete the login session of a user."""
        if self.multinet is not None:
            self.multinet.session = None
            self.save()

    def asjson(self) -> str:
        """Return this user as JSON."""
        return json.dumps(self.asdict())

    def asdict(self) -> Dict:
        """Return this user as a dict."""
        full_dict = copy(self.__dict__)
        full_dict["multinet"] = copy(self.multinet.__dict__)

        return full_dict

    def available_workspaces(self) -> Generator[str, None, None]:
        """Return all workspaces this user has access to."""

        sysdb = system_db()
        bind_vars = {"@workspaces": "workspace_mapping", "userid": self.sub}

        query = """
        FOR w in @@workspaces
            FILTER (
                w.permissions.public == true
                || w.permissions.owner == @userid
                || @userid IN w.permissions.maintainers
                || @userid IN w.permissions.writers
                || @userid IN w.permissions.readers
            )
            RETURN w
        """

        return (x["name"] for x in _run_aql_query(sysdb.aql, query, bind_vars))
