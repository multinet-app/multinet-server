"""Types associated with authentication."""

from typing_extensions import TypedDict


class GoogleUserInfo(TypedDict):
    """Representation of raw User Info from a Google Account."""

    family_name: str
    given_name: str
    name: str
    picture: str
    locale: str
    sub: str  # Unique identifier
    email: str
    email_verified: bool

    # Time of token expiration in Unix Seconds
    exp: int

    # Time of token issue
    iat: int

    # Issuer
    iss: str

    aud: str
    azp: str
    at_hash: str
    hd: str


class UserInfo(TypedDict):
    """The filtered info that is used to create a User."""

    family_name: str
    given_name: str
    name: str
    picture: str
    email: str
    sub: str  # Unique identifier


class MultinetInfo(TypedDict):
    """Data specific to multinet."""

    session: str


class User(GoogleUserInfo):
    """Representation of a user document."""

    multinet: MultinetInfo
