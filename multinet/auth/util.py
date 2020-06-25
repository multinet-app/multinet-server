"""Utility functions for auth."""

from typing import Any, Optional, Callable

from multinet.errors import Unauthorized
from multinet.types import Workspace
from multinet.auth.types import UserInfo
from multinet.user import current_user


# NOTE: unfortunately, it is difficult to write a type signature for this
# decorator. I've opened an issue to ask about this here:
# https://github.com/python/mypy/issues/9032.
def require_login(f: Callable) -> Callable:
    """Decorate an API endpoint to check for a logged in user."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = current_user()
        if user is None:
            raise Unauthorized("You must be logged in to perform this action")

        return f(*args, **kwargs)

    return wrapper


def is_reader(user: Optional[UserInfo], workspace: Workspace) -> bool:
    """Indicate whether `user` has read permissions for `workspace`."""
    perms = workspace["permissions"]

    # A non-logged-in user, by definition, is a reader of public workspaces.
    if user is None:
        return perms["public"]

    # Otherwise, check to see if the workspace is public, or the user is at
    # least a Reader of the workspace.
    sub = user.sub
    return (
        perms["public"]
        or sub in perms["readers"]
        or sub in perms["writers"]
        or sub in perms["maintainers"]
        or perms["owner"] == sub
    )
