"""Utility functions for auth."""

import functools
import jwt
import re
import calendar
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError, DecodeError
from flask import request
from datetime import datetime, timedelta

from multinet.errors import Unauthorized
from multinet.util import current_app_secret_key
from multinet.db.models.workspace import Workspace
from multinet.db.models.user import User
from multinet.auth.types import LoginSessionDict

from typing import Any, Optional, Callable, cast


login_token_header_regex = re.compile(r"^Bearer (\S+)$")


# NOTE: unfortunately, it is difficult to write a type signature for this
# decorator. I've opened an issue to ask about this here:
# https://github.com/python/mypy/issues/9032.
def require_login(f: Callable) -> Callable:
    """Decorate an API endpoint to check for a logged in user."""

    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = current_user()
        if user is None:
            raise Unauthorized("You must be logged in to perform this action")

        return f(*args, **kwargs)

    return wrapper


def is_reader(user: Optional[User], workspace: Workspace) -> bool:
    """Indicate whether `user` has read permissions for `workspace`."""
    perms = workspace.permissions

    # A non-logged-in user, by definition, is a reader of public workspaces.
    if user is None:
        return perms.public

    # Otherwise, check to see if the workspace is public, or the user is at
    # least a reader of the workspace.
    sub = user.sub
    return (
        perms.public
        or sub in perms.readers
        or sub in perms.writers
        or sub in perms.maintainers
        or perms.owner == sub
    )


def require_reader(f: Any) -> Any:
    """Decorate an API endpoint to require read permission."""

    @functools.wraps(f)
    def wrapper(workspace: str, *args: Any, **kwargs: Any) -> Any:
        user = current_user()
        if not is_reader(user, Workspace(workspace)):
            raise Unauthorized(f"You must be a reader of workspace '{workspace}'")

        return f(workspace, *args, **kwargs)

    return wrapper


def is_writer(user: Optional[User], workspace: Workspace) -> bool:
    """Indicate whether `user` has write permissions for `workspace`."""

    if user is None:
        return False

    perms = workspace.permissions
    sub = user.sub

    return sub in perms.writers or sub in perms.maintainers or perms.owner == sub


def require_writer(f: Any) -> Any:
    """Decorate an API endpoint to require write permission."""

    @functools.wraps(f)
    def wrapper(workspace: str, *args: Any, **kwargs: Any) -> Any:
        user = current_user()
        if not is_writer(user, Workspace(workspace)):
            raise Unauthorized(f"You must be a writer of workspace '{workspace}'")

        return f(workspace, *args, **kwargs)

    return wrapper


def is_maintainer(user: Optional[User], workspace: Workspace) -> bool:
    """Indicate whether `user` has maintainer permissions for `workspace`."""

    if user is None:
        return False

    perms = workspace.permissions
    sub = user.sub

    return sub in perms.maintainers or perms.owner == sub


def require_maintainer(f: Any) -> Any:
    """Decorate an API endpoint to require maintainer permission."""

    @functools.wraps(f)
    def wrapper(workspace: str, *args: Any, **kwargs: Any) -> Any:
        user = current_user()

        if not is_maintainer(user, Workspace(workspace)):
            raise Unauthorized(f"You must be a maintainer of workspace '{workspace}'")

        return f(workspace, *args, **kwargs)

    return wrapper


def is_owner(user: Optional[User], workspace: Workspace) -> bool:
    """Indicate whether `user` is the owner of `workspace`."""

    if user is None:
        return False

    perms = workspace.permissions
    sub = user.sub

    return perms.owner == sub


def require_owner(f: Any) -> Any:
    """Decorate an API endpoint to require ownership."""

    @functools.wraps(f)
    def wrapper(workspace: str, *args: Any, **kwargs: Any) -> Any:
        user = current_user()
        if not is_owner(user, Workspace(workspace)):
            raise Unauthorized(f"You must be the owner of workspace '{workspace}'")

        return f(workspace, *args, **kwargs)

    return wrapper


def current_login_token() -> Optional[LoginSessionDict]:
    """If the current request contains the correct header, decode the token."""
    token = request.headers.get("Authorization")
    if not token:
        return None

    match = login_token_header_regex.match(token)
    if not match:
        return None

    token = match.group(1)
    return decode_auth_token(token)


def encode_auth_token(token_dict: LoginSessionDict) -> str:
    """Encode an authorization token into a string."""
    secret = current_app_secret_key()
    return jwt.encode(token_dict, secret).decode()


def decode_auth_token(token: str) -> Optional[LoginSessionDict]:
    """Decode an authorization token into a LoginSessionDict."""
    decoded = None

    try:
        secret = current_app_secret_key()
        decoded = jwt.decode(token, secret)

    except InvalidSignatureError:
        return None
    except ExpiredSignatureError:
        return None
    except DecodeError:
        return None

    return cast(LoginSessionDict, decoded)


def create_login_token(session_str: str) -> LoginSessionDict:
    """Create a login token from a user session."""
    now = datetime.utcnow()
    expiration = now + timedelta(days=30)

    return {
        "session": session_str,
        "iss": "multinet:login",
        "iat": calendar.timegm(now.utctimetuple()),
        "exp": calendar.timegm(expiration.utctimetuple()),
    }


def current_user() -> Optional[User]:
    """Return the logged in user (if any) from the current session."""
    auth = request.headers.get("Authorization")
    if auth is None:
        return None

    session_dict = current_login_token()
    if session_dict is None:
        return None

    return User.from_session(session_dict["session"])
