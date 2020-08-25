"""Utility functions for auth."""

import functools
from typing import Any, Optional, Callable

from multinet.errors import Unauthorized
from multinet.workspace import Workspace
from multinet.user import current_user, User


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
        return bool(perms.public)

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
