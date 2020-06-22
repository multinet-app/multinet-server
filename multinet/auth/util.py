"""Utility functions for auth."""

from typing import Any

from multinet.errors import Unauthorized
from multinet.user import session_user


# NOTE: unfortunately, it is difficult to write a type signature for this
# decorator. I've opened an issue to ask about this here:
# https://github.com/python/mypy/issues/9032.
def require_login(f: Any) -> Any:
    """Decorate an API endpoint to check for a logged in user."""

    def wrapper(workspace: str, *args: Any, **kwargs: Any) -> Any:
        user = session_user()
        if user is None:
            raise Unauthorized("You must be logged in to create new workspaces")

        return f(workspace, *args, **kwargs)

    return wrapper
